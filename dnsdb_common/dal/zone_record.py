# -*- coding: utf-8 -*-

import json
import os
import re
import tempfile
from hashlib import md5

from oslo.config import cfg
from ping import quiet_ping

from dnsdb.constant.constant import ZONE_MAP, VIEW_ZONE, NORMAL_TO_VIEW
from . import commit_on_success
from . import db
from .models import DnsHeader
from .models import DnsRecord
from .models import DnsSerial
from .models import IpPool
from .models import ViewDomainNameState
from .models import ViewIsps
from .models import ViewRecords
from ..library.exception import BadParam
from ..library.log import getLogger

log = getLogger(__name__)

CONF = cfg.CONF


VIEW_TO_CNAME = {NORMAL_TO_VIEW[zone]: cname_zone for zone, cname_zone in ZONE_MAP.iteritems()}

def _make_glbs_cname(domain, abbr):
    for zone, cname_zone in VIEW_TO_CNAME.iteritems():
        if domain.endswith('.' + zone):
            return '%s.%s.%s' % (domain.replace('.' + zone, ''), abbr, cname_zone)
    raise BadParam('Domain name format wrong: %s' % domain)


class ZoneRecordDal(object):
    @staticmethod
    def list_zone_header():
        zones = DnsHeader.query.all()
        results = [zone.zone_name for zone in zones if not zone.zone_name.endswith('.IN-ADDR.ARPA')]
        return sorted(results)

    @staticmethod
    def list_zone_ttl():
        pattern = re.compile(r'\$TTL\s+(\d+)\s+;')
        zone_ttl = {zone: pattern.match(header).group(1)
                    for zone, header in db.session.query(DnsHeader.zone_name, DnsHeader.header_content)}

        return zone_ttl

    @staticmethod
    def select_zone(domain):
        zones = set([zone.zone_name for zone in DnsSerial.query.all()])
        for index in range(1, len(domain.split('.'))):
            best_match = domain.split('.', index)[-1]
            if best_match in zones:
                return best_match
        return None

    @staticmethod
    def get_zone_header(zone_name):
        header = DnsHeader.query.filter_by(zone_name=zone_name).first()
        if not header:
            raise BadParam('not header for zone: %s' % zone_name)
        serial = DnsSerial.query.filter_by(zone_name=zone_name).first()
        if not serial:
            raise BadParam('not serial for zone: %s' % zone_name)
        return dict(header=header.header_content, serial_num=serial.serial_num)

    @staticmethod
    def get_zone_need_update(group_name):
        return [item.zone_name for item in (DnsSerial.query.
                                            filter_by(zone_group=group_name).
                                            filter(DnsSerial.update_serial_num < DnsSerial.serial_num))]

    @staticmethod
    def _get_records_of_view_zone(isp_map):
        # These are 'normal' records since they are in DnsRecord, should included by all isp.
        cname_ttl = CONF.view.cname_ttl
        records = (DnsRecord.query.
                   filter_by(zone_name=VIEW_ZONE).
                   order_by(DnsRecord.domain_name, DnsRecord.record).all())
        res = {isp: [] for isp in isp_map.keys()}
        for record in records:
            for isp in isp_map.iterkeys():
                res[isp].append({"name": record.domain_name, "record": record.record,
                                 "type": record.record_type, "ttl": record.ttl})

        states = ViewDomainNameState.query.order_by(ViewDomainNameState.domain_name).all()
        for state in states:
            res[state.isp].append(
                {"name": state.domain_name, "record": _make_glbs_cname(state.domain_name, isp_map[state.isp]),
                 "type": 'CNAME', "ttl": cname_ttl})
        return res

    @staticmethod
    def _get_records_of_view_domain(zone, isp_map):
        states = ViewDomainNameState.query.all()
        records = (ViewRecords.query.
                   filter_by(zone_name=zone).
                   order_by(ViewRecords.domain_name, ViewRecords.property).
                   all())

        merge_states = {}
        for state in states:
            if state.domain_name not in merge_states:
                merge_states[state.domain_name] = []
            state.enabled_rooms = json.loads(state.enabled_rooms)
            merge_states[state.domain_name].append(state)

        active_records = []
        for record in records:
            if record.record_type != 'A' and record.record_type != 'CNAME':
                raise BadParam('ViewRecord type error: only [A, CNAME] allow.')

            states = merge_states[record.domain_name]
            for state in states:
                if state.state == 'disabled':
                    continue
                # It's an A record and state record indicates that the A record is being used.
                if state.state == 'A' and record.record_type == 'A' and record.property in state.enabled_rooms:
                    active_records.append({"name": _make_glbs_cname(state.domain_name, isp_map[state.isp]),
                                           "record": record.record, "type": record.record_type, "ttl": record.ttl})
                # It's a CNAME record and state record says the CNAME the record is in use.
                elif record.record_type == 'CNAME' and str(record.id) == state.state:
                    active_records.append({"name": _make_glbs_cname(state.domain_name, isp_map[state.isp]),
                                           "record": record.record, "type": record.record_type, "ttl": record.ttl})
        return sorted(active_records, key=lambda record: (record['name'], record['record']))

    @staticmethod
    def _get_records_of_ordinary_zone(zone_name):
        records = DnsRecord.query.filter_by(zone_name=zone_name).all()
        record_info = []
        for record in records:
            if record.ttl != 0:
                record_info.append(
                    {"name": record.domain_name, "record": record.record,
                     "type": record.record_type, 'ttl': record.ttl})
            else:
                record_info.append({"name": record.domain_name, "record": record.record, "type": record.record_type})
        return sorted(record_info, key=lambda x: (x['name'], x['record']))

    @staticmethod
    def get_zone_records(zone_name):
        isp_map = {item.name_in_english: item.abbreviation for item in ViewIsps.query.all()}
        if zone_name == VIEW_ZONE:
            return ZoneRecordDal._get_records_of_view_zone(isp_map)
        elif zone_name in ZONE_MAP.values():
            return ZoneRecordDal._get_records_of_view_domain(zone_name, isp_map)
        else:
            return ZoneRecordDal._get_records_of_ordinary_zone(zone_name)

    @staticmethod
    @commit_on_success
    def update_serial_num(zone_name):
        item = DnsSerial.query.filter_by(zone_name=zone_name).first()
        if not item:
            raise BadParam('No such zone: %s' % zone_name)
        serial_num = item.serial_num
        item.update_serial_num = serial_num
        return serial_num

    @staticmethod
    def has_no_mx_txt_record(zone, domain_name):
        # 是否存在MX TXT记录
        zone_header = ZoneRecordDal.get_zone_header(zone)['header']
        pattern = r'\s{0}[\s\d]+IN\s+MX|\s{0}[\s\d]+IN\s+TXT'.format(domain_name.replace('.' + zone, ''))
        if re.search(pattern, zone_header.header_content):
            raise BadParam('%s has mx or txt record in zone: %s' % (domain_name, zone))

    @staticmethod
    def check_dns_restriction(zone, domain_name, record_type):
        """
       1  有TXT/MX/A/CNAME 任意一种记录，都不允许添加cname
       2  有cname记录不允许添加a记录
       """
        if record_type == 'A' and DnsRecord.query.filter_by(domain_name=domain_name, record_type='CNAME').first():
            raise BadParam('%s has CNAME record.' % domain_name, msg_ch=u'域名已有CNAME记录')
        if record_type == 'CNAME':
            if DnsRecord.query.filter(domain_name=domain_name).first():
                raise BadParam('%s has %s record.' % domain_name, msg_ch=u'域名只能有一条CNAME记录')

            ZoneRecordDal.has_no_mx_txt_record(zone, domain_name)

    @staticmethod
    def check_zone_syntax(zone_name, header_content):
        '''
        named-checkzone zone zone-file
        这个工具检查的时候在非master主机如果zone名与里面ns记录域名相同，检查失败，因为头文件没有相应ns的A记录。
        所以检查的时候把zone名加上check-前缀
        '''
        tmp_file = os.path.join(CONF.tmp_dir, zone_name)
        with open(tmp_file, 'w') as f:
            f.write(header_content)

        if CONF.etc.env != 'dev':
            err_file = tempfile.mktemp(prefix='err_', dir='/tmp')
            if os.system("named-checkzone -k fail %s %s >%s 2>&1" % (
                    zone_name, tmp_file, err_file)) != 0:
                with open(err_file) as f:
                    error_log = f.read()
                raise BadParam('Check header failed:%s' % error_log)

    @staticmethod
    def check_zone_header(zone_name, header_content):
        headers = DnsHeader.query.filter_by(zone_name=zone_name).all()
        if len(headers) != 1:
            raise BadParam('No this zone header: %s' % zone_name, msg_ch=u'没有相关记录')
        zone_name = zone_name.strip()
        if 'pre_serial' not in header_content:
            raise BadParam('check header failed: no pre_serial', msg_ch=u'文件中必须包含pre_serial,用于serial占位')
        if not header_content.endswith('\n'):
            raise BadParam('check header failed: end line must be line break', msg_ch=u'文件末尾需要有空行')
        header_content = header_content.replace('pre_serial', '1')

        ZoneRecordDal.check_zone_syntax(zone_name, header_content)

        # 检查里面的MX和TXT记录是否有对应的cname记录
        pattern = r'(?<=[\s;])(([\w-]+\.)*[-@\w]+)(\s+\d+)?\s+IN\s+(MX|TXT)'
        if re.search(r'\sIN\s(MX|TXT)\s', header_content):
            domains = set(
                ['{}.{}'.format(domain.group(1), zone_name) for domain in re.finditer(pattern, header_content)]
            )
            records = DnsRecord.query.filter(DnsRecord.domain_name.in_(domains)).filter(
                DnsRecord.record_type == 'CNAME').all()
            if records:
                conflict_domain = [dns.name for dns in records]
                raise BadParam('%s already has cname record, can not add MX or TXT record.' % conflict_domain,
                               msg_ch=u'域名%s已有CNAME记录，不能有MX/TXT记录')

    @staticmethod
    @commit_on_success
    def increase_serial_num(zone_name):
        serials = DnsSerial.query.filter_by(zone_name=zone_name).all()
        if len(serials) != 1:
            raise BadParam('Zone serial should be unique: %s' % zone_name, msg_ch=u'zone serial记录不存在或者不唯一')
        serial = serials[0]
        serial.serial_num += 1

        return serial.serial_num

    @staticmethod
    def update_zone_header(zone_name, header_content):
        ZoneRecordDal.check_zone_header(zone_name, header_content)
        old_header = DnsHeader.query.filter_by(zone_name=zone_name).first().header_content
        if md5(header_content).hexdigest() == md5(old_header).hexdigest():
            raise BadParam('No change for this header: %s' % zone_name, msg_ch=u'内容没有变化')

        # 更新数据库中的header
        with db.session.begin(subtransactions=True):
            headers = DnsHeader.query.filter_by(zone_name=zone_name).all()
            if len(headers) != 1:
                raise BadParam('Zone header should be unique: %s' % zone_name, msg_ch=u'header记录不存在或者不唯一')
            DnsHeader.query.filter_by(zone_name=zone_name).update({
                'header_content': header_content
            })

            serial_num = ZoneRecordDal.increase_serial_num(zone_name)

        return serial_num

    @staticmethod
    @commit_on_success
    def add_record(domain_name, record, record_type, ttl, username):
        zone = ZoneRecordDal.select_zone(domain_name)

        ZoneRecordDal.check_dns_restriction(zone, domain_name, record_type)
        # 保证域名唯一
        if DnsRecord.query.filter_by(domain_names=domain_name, record=record).first():
            # 'already exists' 不能删，dnsutil里在用
            raise BadParam("Domain name has already exists which repells this new record.", msg_ch=u'记录已存在')

        other_record = DnsRecord.query.filter_by(domain_name=domain_name).first()
        # 如果有其他记录 ttl默认参数与其他记录保持一致
        if other_record:
            if ttl == 0:
                ttl = other_record.ttl

        insert_record = DnsRecord(domain_name=domain_name, record=record,
                                  zone_name=zone, update_user=username,
                                  record_type=record_type, ttl=ttl)
        db.session.add(insert_record)

        # 更新zone
        return ZoneRecordDal.increase_serial_num(zone)

    @staticmethod
    @commit_on_success
    def auto_add_record(domain_name, region, username):
        zone = ZoneRecordDal.select_zone(domain_name)
        # Select an unsed ip if @domain name has no records existed.
        records = IpPool.query.outerjoin(DnsRecord, DnsRecord.record == IpPool.fixed_ip).add_columns(
            IpPool.fixed_ip,
            DnsRecord.record).filter(IpPool.region == region, DnsRecord.record.is_(None),
                                     IpPool.allocated.is_(True)).order_by(IpPool.fixed_ip)

        for item in records:
            ip = item.fixed_ip
            # By sending 8 icmp packets with 64 bytes to this ip within 0.1 second,
            # we can probably make sure if an ip is alive.
            # If this ip does not answer any pings in 0.2 second, it will be presumed to be unused.
            if CONF.etc.env != 'dev' and quiet_ping(ip, 0.1, 8, 64)[0] != 100:
                IpPool.query.filter_by(fixed_ip=ip).update({'allocated': False})
                log.error("%s should have been set allocated=False since it is ping-able." % ip)
                continue
            with db.session.begin(subtransactions=True):
                try:
                    iprecord = IpPool.query.filter_by(fixed_ip=ip).with_for_update(nowait=True, of=IpPool)
                except Exception:
                    log.error("%s has been locked by other process" % ip)
                    continue
                if DnsRecord.query.filter_by(record=ip).first():
                    continue

                insert_record = DnsRecord(domain_name=domain_name, record=ip,
                                          zone_name=zone, update_user=username,
                                          record_type='A')
                db.session.add(insert_record)

                return ZoneRecordDal.increase_serial_num(zone)
        else:
            raise BadParam("No unused ip for region:%s." % region, msg_ch=u'没有可用的ip')

    @staticmethod
    @commit_on_success
    def modify_record(domain_name, origin_record, update_dict, username):
        zone = ZoneRecordDal.select_zone(domain_name)

        if update_dict.get('record_type', None) == 'CNAME':
            ZoneRecordDal.has_no_mx_txt_record(zone, domain_name)

        records = DnsRecord.query.filter_by(domain_name=domain_name, record=origin_record).all()
        if len(records) > 1:
            raise BadParam("More than one record,check database!")
        if len(records) == 0:
            raise BadParam("Can not find this record!")

        update_dict.pop('check_record')
        update_dict['update_user'] = username
        DnsRecord.query.filter_by(domain_name=domain_name, record=origin_record).update(update_dict)

        if update_dict.get('record_type') == 'A':
            # 保证没有重复的A记录
            if DnsRecord.query.filter_by(domain_name=domain_name, record=update_dict['record']).count() > 1:
                raise BadParam('Domain %s already have record %s' % (domain_name, update_dict['record']),
                               msg_ch=u'记录与存在')

        # 同一域名的不同记录保持ttl一致
        ttl = update_dict.get('ttl')
        if ttl is not None:
            DnsRecord.query.filter_by(domain_name=domain_name).update({'ttl': ttl})

        # 如果是修改为CNAME,删除所有A记录
        if update_dict.get('record_type') == 'CNAME':
            DnsRecord.query.filter_by(domain_name=domain_name, record_type='A').delete()

        return ZoneRecordDal.increase_serial_num(zone)

    @staticmethod
    @commit_on_success
    def delete_record(domain_name, record, record_type):
        dns_records = DnsRecord.query.filter_by(domain_name=domain_name, record=record, record_type=record_type).all()
        if len(dns_records) == 0:
            raise BadParam("No such a record:[domain name:%s, record:%s, type:%s]" %
                           (domain_name, record, record_type), msg_ch=u'记录不存在')
        zone = dns_records[0].zone_name
        DnsRecord.query.filter_by(domain_name=domain_name, record=record, record_type=record_type).delete()

        return ZoneRecordDal.increase_serial_num(zone)

    @staticmethod
    def get_domain_records(**kwargs):
        return [item.json_serialize() for item in DnsRecord.query.filter_by(**kwargs)]

    @staticmethod
    def search_domain_records(field, pattern):
        return [item.json_serialize() for item in DnsRecord.query.filter(getattr(DnsRecord, field).like(pattern))]
