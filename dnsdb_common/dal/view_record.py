# -*- coding: utf-8 -*-

from __future__ import print_function
import json
from collections import defaultdict

import sqlalchemy
from sqlalchemy import func
from oslo.config import cfg

from .models import DnsColo
from .models import DnsSerial
from .models import ViewDomainNameState
from .models import ViewDomainNames
from .models import ViewIsps
from .models import ViewRecords
from .models import DnsRecord
from ..dal import db, commit_on_success
from ..library.IPy import IP
from ..library.exception import BadParam
from ..library.log import setup, getLogger
from ..library.utils import is_valid_domain_name, is_valid_ip_format
from dnsdb.constant.constant import NORMAL_TO_CNAME, NORMAL_TO_VIEW, VIEW_ZONE

setup("dnsdb")
log = getLogger(__name__)

CONF = cfg.CONF


def is_valid_view_ip(ip, room):
    from ..dal.subnet_ip import SubnetIpDal
    is_valid_ip_format(ip)
    try:
        tmp = IP(ip)
    except Exception:
        raise BadParam('Invalid ip format: %s' % ip, msg_ch=u'机房 %s ip格式错误：%s' % (room, ip))
    # 需要公网ip
    if tmp.iptype() != 'PUBLIC':
        raise BadParam('view ip should bu public: room %s ip %s' % (room, ip),
                       msg_ch=u'view域名对应ip需为公网ip: 机房 %s ip %s' % (room, ip))
    # 机房ip检查
    colo = SubnetIpDal.get_region_by_ip(ip)['colo']
    if colo != room:
        raise BadParam('ip  %s belong to room %s, not %s' % (ip, colo, room),
                       msg_ch=u'机房%s: ip %s 属于机房 %s' % (room, ip, colo))
    return True


def _validate_domain_args(domain_name, rooms, cnames):
    is_valid_domain_name(domain_name)
    # Each cname and the name of the cname can appear only once.
    tmp = set()
    if cnames:
        for name, cdn in cnames.iteritems():
            if (not name) or (not cdn) or (cdn == domain_name) or (not is_valid_domain_name(cdn)):
                raise BadParam("cnames format wrong: %s: %s" % (name, cdn),
                               msg_ch=u'cdn参数格式错误%s: %s' % (name, cdn))
            if cdn in tmp:
                raise BadParam("Duplicate cdn:%s" % cdn, msg_ch=u'cdn参数重复: %s' % name)
            if name in tmp:
                raise BadParam("Duplicate name:%s" % name, msg_ch=u'cdn厂商重复: %s' % name)
            tmp.add(name)
            tmp.add(cdn)
    # Each room and ip can appear only once.
    tmp.clear()
    if rooms:
        for room, ips in rooms.iteritems():
            if (not room) or (not ips) or (not isinstance(ips, list)):
                raise BadParam("rooms format wrong: %s, %s" % (room, ips),
                               msg_ch=u'机房参数格式错误%s: %s' % (room, ips))
            if room in tmp:
                raise BadParam("Duplicate server room:%s" % room, msg_ch=u'机房重复: %s' % room)
            tmp.add(room)
            for j in ips:
                is_valid_view_ip(j, room)
                if j in tmp:
                    raise BadParam("Duplicate ip:%s" % j, msg_ch=u'机房 %s ip %s 重复' % (room, j))
                tmp.add(j)
    return True


def _need_reload_zone(active_record, rooms):
    need_reload = False
    update_rooms = {}
    for room, ips in rooms.iteritems():
        if len(ips) == 0:
            continue
        update_rooms[room] = ips
    # 和已激活记录对比
    for room, ips in active_record.items():
        # 删除机房的情况
        if room not in update_rooms:
            need_reload = True
            break
        else:
            # 新增/删除ip的情况
            if set(update_rooms[room]).symmetric_difference(set(ips)):
                need_reload = True
                break
    return need_reload


class ViewRecordDal(object):
    @staticmethod
    def create_view_domain(domain_name):
        if domain_name.endswith(VIEW_ZONE):
            for k, v in NORMAL_TO_VIEW.iteritems():
                if domain_name.endswith(v):
                    return domain_name, k
            raise BadParam('invalid domain', msg_ch=u'可用view域名后缀: %s' % NORMAL_TO_VIEW.values())

        normal_zone = ViewRecordDal.select_zone(domain_name)
        if normal_zone not in NORMAL_TO_VIEW:
            raise BadParam('invalid domain: %s' % domain_name,
                           msg_ch=u'%s 不是可用普通域名后缀: %s' % (normal_zone, NORMAL_TO_VIEW.keys()))
        return domain_name.replace(normal_zone, NORMAL_TO_VIEW[normal_zone]), normal_zone

    @staticmethod
    def get_view_domain_zone(domain_name):
        return (db.session.query(ViewRecords.zone_name).
                filter_by(domain_name=domain_name).
                group_by(ViewRecords.zone_name).first().zone_name)

    @staticmethod
    def zone_domain_count():
        zone_count = []
        exclude_zones = NORMAL_TO_CNAME.values()
        for item in db.session.query(DnsRecord.zone_name,
                                     func.count(DnsRecord.zone_name)).group_by(DnsRecord.zone_name):
            if item[0] in exclude_zones:
                continue
            zone_count.append({'zone': item[0], 'count': item[1]})
        result = sorted(zone_count, key=lambda x: x['count'], reverse=True)[:5]
        if VIEW_ZONE:
            result.append({'zone': VIEW_ZONE, 'count': ViewDomainNames.query.count()})
        return result



    @staticmethod
    def is_migrate_domain(domain_name):
        return (ViewDomainNameState.query.
                filter_by(domain_name=domain_name).
                filter(ViewDomainNameState.enabled_rooms != ViewDomainNameState.origin_enabled_rooms).
                first()) is not None

    @staticmethod
    def list_server_room(**conditions):
        return DnsColo.query.filter_by(**conditions)

    @staticmethod
    def get_domain_name_record(domain_name):
        view_domain = ViewRecordDal.get_view_domain_name(domain_name)
        if not view_domain:
            raise BadParam('No such domain_name: %s' % domain_name, msg_ch=u'没有对应的view域名记录')

        record_dict = {}
        for record in ViewRecords.query.filter_by(domain_name=view_domain):
            if record.record_type == 'A':
                if record.property not in record_dict:
                    record_dict[record.property] = []
                record_dict[record.property].append(record.record)
            else:
                record_dict[record.property] = record.record
        return view_domain, record_dict


    @staticmethod
    def get_view_domain_name(domain):
        record = ViewDomainNames.query.filter(sqlalchemy.or_(ViewDomainNames.domain_name == domain,
                                                             ViewDomainNames.cname == domain)).first()
        if not record:
            return None
        else:
            return record.cname

    @staticmethod
    def get_view_domain_info(domain):
        view_domain = ViewRecordDal.get_view_domain_name(domain)
        if not view_domain:
            raise BadParam('No such domain_name: %s' % domain, msg_ch=u'没有对应的view域名记录')

        records = ViewRecords.query.filter_by(domain_name=view_domain).all()
        state_list = ViewDomainNameState.query.filter_by(domain_name=view_domain).all()
        isp_list = [item.name_in_english for item in ViewIsps.query.all()]
        room_confs = defaultdict(lambda: {
            'is_enabled': False,
            'isps': {i: False for i in isp_list},
            'ips': []
        })
        cdn_conf = {
            'cdn': [{
                "name": r.property,
                "cname": r.record
            } for r in records if r.record_type == 'CNAME'],
            'isps': {isp: {'name': "不使用cdn", 'cname': "不使用cdn"} for isp in isp_list}
        }

        for record in records:
            if record.record_type == 'A':
                room = record.property
                room_info = room_confs[room]
                if record.record not in room_info['ips']:
                    room_info['ips'].append(record.record)
                for s in state_list:
                    if s.state == 'A' and room in json.loads(s.enabled_rooms):
                        room_info['isps'][s.isp] = True
                        room_info['is_enabled'] = True
            elif record.record_type == 'CNAME':
                for s in state_list:
                    if s.state.isdigit() and int(s.state) == int(record.id):
                        cdn_conf['isps'][s.isp]['name'] = record.property
                        cdn_conf['isps'][s.isp]['cname'] = record.record
            else:
                raise BadParam("Unexepected record type:%s" % record.record_type,
                               msg_ch=u'数据库中存在非[A CNAME]记录类型： %s' % record.record_type)

        return {
            'domain_name': domain,
            'is_migrate': ViewRecordDal.is_migrate_domain(view_domain),
            'cnames': cdn_conf,
            'rooms': room_confs
        }

    @staticmethod
    def get_isp_enable(domain_name, isps):
        q = ViewDomainNameState.query
        q = q.filter(ViewDomainNameState.domain_name == domain_name)
        q = q.filter(ViewDomainNameState.isp.in_(isps))
        state = {}
        for domain_state in q:
            try:
                if domain_state.state == 'A':
                    state[domain_state.isp] = json.loads(domain_state.enabled_rooms)
                elif domain_state.state == 'disabled':
                    pass
                else:
                    record = ViewRecords.query.filter(ViewRecords.id == int(domain_state.state)).one()
                    state[domain_state.isp] = record.record
            except Exception as e:
                log.error('search isp enabel failed')
        return state

    @staticmethod
    def search_view_domain(domain='', rooms=(), isps=(), select_cdn=True):
        records = ViewDomainNames.query.order_by(ViewDomainNames.domain_name).all()
        view2normal = {record.cname: record.domain_name for record in records}

        domain_names = []

        view_domain = domain
        if domain:
            view_domain, _ = ViewRecordDal.create_view_domain(domain)

        if len(rooms) == 0 and domain != '':
            result = db.session.query(ViewDomainNameState).filter(ViewDomainNameState.domain_name == view_domain).all()
            domain_names.extend([
                record.domain_name for record in result
            ])

        for room in rooms:
            like_str = '%{}%'.format(room)
            q = db.session.query(ViewDomainNameState).filter(ViewDomainNameState.enabled_rooms.like(like_str))
            if isps:
                q = q.filter(
                    ViewDomainNameState.isp.in_(isps))
            result = q.all()
            domain_names.extend([
                record.domain_name for record in result
            ])

        # add all cname in isps
        if select_cdn:
            result = db.session.query(ViewDomainNameState).filter(ViewDomainNameState.state != 'A').filter(
                ViewDomainNameState.isp.in_(isps)).all()
            domain_names.extend([
                record.domain_name for record in result
            ])
        domain_names = [domain_name for domain_name in list(set(domain_names)) if view_domain in domain_name]
        domain_names = sorted(domain_names, key=lambda x: len(x))

        return [{
            "view_domain": domain_name,
            "domain": view2normal[domain_name]
        } for domain_name in domain_names]

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
    def select_zone(domain):
        zones = set([zone.zone_name for zone in DnsSerial.query.all()])
        for index in range(1, len(domain.split('.'))):
            best_match = domain.split('.', index)[-1]
            if best_match in zones:
                return best_match
        return None

    @staticmethod
    def is_cname_used(record_id, domain_name):
        return ViewDomainNameState.query.filter_by(state=str(record_id), domain_name=domain_name).count() != 0

    @staticmethod
    @commit_on_success
    def insert_view_record(domain_name, cnames, rooms, cname_zone):
        # CDN
        for name, cdn in cnames.iteritems():
            record = ViewRecords.query.filter_by(domain_name=domain_name,
                                                 record=cdn).first()
            if record:
                record.property = name
                db.session.add(record)
            else:
                db.session.add(ViewRecords(
                    domain_name=domain_name,
                    ttl=60,
                    record=cdn,
                    record_type='CNAME',
                    zone_name=cname_zone,
                    property=name
                ))

        # A
        for room, ips in rooms.iteritems():
            for ip in ips:
                db.session.add(ViewRecords(
                    domain_name=domain_name,
                    ttl=60,
                    record=ip,
                    record_type='A',
                    zone_name=cname_zone,
                    property=room
                ))

    @staticmethod
    @commit_on_success
    def _del_unused_cname(domain_name, cnames):
        new_names = [(name, cdn) for name, cdn in cnames.iteritems()]
        records = ViewRecords.query.filter_by(domain_name=domain_name, record_type='CNAME').all()
        for record in records:
            if (record.property, record.record) in new_names:
                continue
            if ViewRecordDal.is_cname_used(record.id, domain_name):
                raise BadParam("Failed to delete %s because of using." % record.property,
                               msg_ch=u'CDN域名正在使用，不能修改')
            db.session.delete(record)
            log.info("Success to delete {0}".format(record.record))

    @staticmethod
    def _get_acitive_record(domain_name):
        states = ViewDomainNameState.query.filter_by(domain_name=domain_name, state='A').all()
        active_room = set()
        origin_active_room = set()
        for state in states:
            active_room.update(json.loads(state.enabled_rooms))
            origin_active_room.update(json.loads(state.origin_enabled_rooms))
        active_record = defaultdict(lambda: [])
        if active_room:
            records = ViewRecords.query.filter_by(domain_name=domain_name).filter(
                ViewRecords.property.in_(active_room)).all()
            for record in records:
                active_record[record.property].append(record.record)
        return dict(active_record), active_room | origin_active_room

    @staticmethod
    def _can_remove_room(active_room, rooms):
        can_remove = True
        cannot_remove_rooms = []
        for room in active_room:
            if room not in rooms or (not rooms[room]):
                can_remove = False
                cannot_remove_rooms.append(room)
        return can_remove, cannot_remove_rooms

    @staticmethod
    def insert_view_domain(username, domain_name, cnames, rooms):
        # 如果机房和cname配置都没有，不允许添加域名
        if (not cnames) and (not rooms):
            raise BadParam(message="No rooms and cnames conf.", msg_ch=u'请配置机房或CDN参数')

        if ViewRecordDal.get_view_domain_name(domain_name):
            raise BadParam('Domain already existed', msg_ch=u'域名已经存在')

        for item in NORMAL_TO_VIEW.keys():
            if domain_name.endswith(item):
                break
        else:
            raise BadParam('Invalid domain', msg_ch=u'可用的域名后缀: %s' % NORMAL_TO_VIEW.keys())
        view_domain, normal_zone = ViewRecordDal.create_view_domain(domain_name)
        cname_zone = NORMAL_TO_CNAME[normal_zone]

        # 检查普通域名中有domain_name记录
        # 如果没有，则添加CNAME记录
        # 如果有，A记录的话不允许添加域名，CNAME记录看下是不是CNAME到view_doamin
        normal_records = DnsRecord.query.filter_by(domain_name=domain_name).all()
        if normal_records:
            if len(normal_records) > 1 or normal_records[0].record_type == 'A':
                raise BadParam('Doamin %s already exist A record' % domain_name,
                               msg_ch=u'域名已经存在A记录，不能用作view域名')
            record = normal_records[0].record
            if record != view_domain:
                raise BadParam('Doamin %s already exist CNAME record: %s' % (domain_name, record),
                               msg_ch=u'域名已经存在CNAME记录: %s，不能用作view域名' % record)
        else:
            with db.session.begin(subtransactions=True):
                insert_record = DnsRecord(domain_name=domain_name, record=view_domain,
                                          zone_name=normal_zone, update_user=username,
                                          record_type='CNAME', ttl=CONF.view.cname_ttl)
                db.session.add(insert_record)
                ViewRecordDal.increase_serial_num(normal_zone)

        with db.session.begin(subtransactions=True):
            db.session.add(ViewDomainNames(
                domain_name=domain_name,
                cname=view_domain
            ))

        ViewRecordDal.insert_view_record(view_domain, cnames, rooms, cname_zone)

        with db.session.begin(subtransactions=True):
            isp_list = [item.name_in_english for item in ViewIsps.query.all()]
            for isp in isp_list:
                db.session.add(ViewDomainNameState(
                    domain_name=view_domain,
                    isp=isp
                ))
            # 新增域名 更新dnsmaster2
            ViewRecordDal.increase_serial_num(VIEW_ZONE)
            # ViewRecordDal.increase_serial_num(cname_zone)

    @staticmethod
    def update_view_domain(username, domain_name, cnames, rooms):
        view_domain = ViewRecordDal.get_view_domain_name(domain_name)
        if not view_domain:
            raise BadParam("No such domain name:%s" % domain_name, msg_ch=u'没有域名记录')

        ViewRecordDal._del_unused_cname(view_domain, cnames)
        cname_zone = ViewRecordDal.get_view_domain_zone(view_domain)
        # 获取当前激活的机房ip
        active_record, active_room = ViewRecordDal._get_acitive_record(view_domain)

        # 判断是否可以删除
        can_remove, room = ViewRecordDal._can_remove_room(active_room, rooms)
        if not can_remove:
            raise BadParam(message='room %s is using, can not delete', msg_ch=u'机房%s启用中，不能删除配置' % room)

        with db.session.begin(subtransactions=True):
            records = ViewRecords.query.filter_by(domain_name=view_domain, record_type='A')
            for record in records:
                db.session.delete(record)

        ViewRecordDal.insert_view_record(view_domain, cnames, rooms, cname_zone)

        # 判断是否需要reload
        need_reload = _need_reload_zone(active_record, rooms)
        log.info('update domain %s need reload: %s' % (domain_name, need_reload))
        if need_reload:
            ViewRecordDal.increase_serial_num(cname_zone)

    @staticmethod
    def upsert_view_domain(username, domain_name, rooms, cnames, action):
        cnames = {} if not cnames else cnames
        rooms = {} if not rooms else rooms

        mapper = {
            'insert': ViewRecordDal.insert_view_domain,
            'update': ViewRecordDal.update_view_domain
        }
        if action not in mapper:
            raise BadParam('action {0} not supperted'.format(action))

        _validate_domain_args(domain_name, rooms, cnames)

        # Update/Insert
        with db.session.begin(subtransactions=True):
            return mapper[action](username, domain_name, cnames, rooms)

    @staticmethod
    def _check_update_state_args(isp_dict, domain_name):
        record_properties = set()
        for item in ViewRecords.query.filter_by(domain_name=domain_name):
            if item.record_type == 'A':
                record_properties.add(item.property)

        cur_state_list = (ViewDomainNameState.query.filter_by(domain_name=domain_name).all())
        cur_state_dict = {item.isp: item for item in cur_state_list}

        for isp, conf in isp_dict.iteritems():
            state = cur_state_dict.get(isp, None)
            if not state:
                raise BadParam('Domain %s has no state record for isp: %s' % (domain_name, isp),
                               msg_ch=u'域名%s的运营商%s没有state配置' % (domain_name, isp))
            enabled_rooms = conf.get('rooms', [])
            if enabled_rooms:
                if not set(enabled_rooms).issubset(record_properties):
                    raise BadParam('Enabled room has no record for domain: %s' % domain_name,
                                   msg_ch=u'启用了没有配置ip的机房')
            cdn = conf.get('cdn', '')
            if cdn:
                res = ViewRecords.query.filter_by(domain_name=state.domain_name, record=cdn,
                                                  record_type='CNAME').first()
                if not res:
                    raise BadParam('Enabled cdn %s is invalid for domain: %s' % (cdn, domain_name),
                                   msg_ch=u'域名 %s cdn没有配置: %s' % (domain_name, cdn))
            if not enabled_rooms and not cdn:
                raise BadParam('rooms and cdn both null for isp %s' % isp, msg_ch=u'运营商%s无启用配置' % isp)

        need_update_isp = set()
        for isp, item in cur_state_dict.iteritems():
            state = item.state
            if state == "disabled":
                need_update_isp.add(isp)
            elif state == "A":
                if len(json.loads(item.enabled_rooms)) == 0:
                    need_update_isp.add(isp)
            elif not state.isdigit():
                need_update_isp.add(isp)

        error_isp = need_update_isp - set(isp_dict.keys())
        if error_isp:
            s = ' '.join(error_isp)
            raise BadParam(" isp %s state is disabled." % s, msg_ch=u'运营商%s没有启用配置' % s)


    @staticmethod
    def update_view_domain_state(domain_name, isp_dict):
        update_isps = isp_dict.keys()
        view_domain = ViewRecordDal.get_view_domain_name(domain_name)
        if not view_domain:
            raise BadParam('No such domain_name: %s' % domain_name, msg_ch=u'没有对应的view域名记录')

        op_before = ViewRecordDal.get_isp_enable(view_domain, update_isps)

        ViewRecordDal._check_update_state_args(isp_dict, view_domain)
        is_migrate = ViewRecordDal.is_migrate_domain(view_domain)

        with db.session.begin(subtransactions=True):
            """
            迁移状态的机房不更新原始记录
            """
            query = (ViewDomainNameState.query.
                     filter_by(domain_name=view_domain).
                     filter(ViewDomainNameState.isp.in_(update_isps)))
            for state in query:
                isp = state.isp
                conf = isp_dict[isp]
                enabled_rooms = conf.get('rooms', [])
                if enabled_rooms:
                    state.enabled_rooms = json.dumps(conf['rooms'])
                    state.state = 'A'
                    if not is_migrate:
                        state.origin_enabled_rooms = json.dumps(conf['rooms'])
                        state.origin_state = 'A'
                cdn = conf.get('cdn', '')
                if cdn:
                    res = ViewRecords.query.filter_by(domain_name=state.domain_name, record=cdn, record_type='CNAME').first()
                    state.enabled_rooms = json.dumps([])
                    state.state = str(res.id)
                    if not is_migrate:
                        state.enabled_rooms = json.dumps([])
                        state.origin_state = str(res.id)

            zone = ViewRecordDal.get_view_domain_zone(view_domain)
            ViewRecordDal.increase_serial_num(zone)

        return op_before

    @staticmethod
    @commit_on_success
    def delete_view_domain(domain_name):
        need_update = [VIEW_ZONE]

        need_update.append(ViewRecordDal.get_view_domain_zone(domain_name))
        ViewRecords.query.filter_by(domain_name=domain_name).delete()
        ViewDomainNameState.query.filter_by(domain_name=domain_name).delete()
        ViewDomainNames.query.filter_by(cname=domain_name).delete()

        record = DnsRecord.query.filter_by(record=domain_name).first()
        need_update.append(record.zone_name)
        db.session.delete(record)

        for update_zone in need_update:
            ViewRecordDal.increase_serial_num(update_zone)
