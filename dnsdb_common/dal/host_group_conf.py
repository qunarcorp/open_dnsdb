# -*- coding: utf-8 -*-

import os
import tempfile
from collections import OrderedDict
from hashlib import md5

from oslo_config import cfg

from . import db, commit_on_success
from .models import DnsHeader
from .models import DnsHost
from .models import DnsHostGroup
from .models import DnsNamedConf
from .models import DnsSerial
from .models import DnsZoneConf
from .models import DnsRecord
from ..library.exception import BadParam, DnsdbException
from ..library.utils import is_valid_ip_format, is_valid_domain_name
from dnsdb.deploy import start_deploy_job

CONF = cfg.CONF

def start_named_deploy(username, group_md5_conf):
    unfinished = []
    for group, info in group_md5_conf.items():
        unfinished.extend(info['hosts'])
    job_id = start_deploy_job(username, group_md5_conf, 'named.conf', unfinished)
    return job_id

def start_zone_header_deploy(user, group, zone_name, conf_type='zone'):
    hosts = HostGroupConfDal.get_host_by_group(group)
    deploy_info = dict(hosts=hosts, group=group, zone=zone_name)

    return start_deploy_job(user, deploy_info, conf_type, hosts)

class HostGroupConfDal:
    @staticmethod
    def check_host(hostname, ip):
        is_valid_domain_name(hostname)
        is_valid_ip_format(ip)
        if DnsHost.query.filter_by(host_name=hostname).first():
            raise BadParam('Hostname exist, %s' % hostname, msg_ch=u'主机已经存在:%s' % hostname)
        if DnsHost.query.filter_by(host_ip=ip).first():
            raise BadParam('ip already exist: %s' % ip, msg_ch=u'ip为%s的主机已经存在' % ip)

    @staticmethod
    def get_group_by_ip(host_ip):
        item = DnsHost.query.filter_by(host_ip=host_ip).first()
        if not item:
            raise BadParam('No such ip record: %s' % host_ip, msg_ch=u'请先将ip %s 写入数据库' % host_ip)
        return item.host_group

    @staticmethod
    @commit_on_success
    def update_host_conf_md5(host_ip, host_conf_md5):
        return DnsHost.query.filter_by(host_ip=host_ip).update({
            'host_conf_md5': host_conf_md5
        })

    @staticmethod
    def get_not_update_host(conf_md5, group):
        return [item.host_name
                for item in DnsHost.query.filter_by(host_group=group).filter(DnsHost.host_conf_md5 != conf_md5)]

    @staticmethod
    def get_host_by_group(group):
        host_list = DnsHost.query.filter_by(host_group=group).all()
        if not host_list:
            raise BadParam('No hosts in the host group: %s' % group)
        host_list = [host.host_ip for host in host_list]
        return host_list

    @staticmethod
    def get_group_by_name(group_name):
        item = DnsHostGroup.query.filter_by(group_name=group_name).first()
        if not item:
            raise BadParam('No such group: %s' % group_name)
        return item

    @staticmethod
    def get_host_group():
        return [{'group_name': item.group_name} for item in DnsHostGroup.query.order_by(DnsHostGroup.group_name).all()]

    @staticmethod
    def list_host_group():
        groups = []
        for group in DnsHostGroup.query.order_by(DnsHostGroup.group_name):
            group_name = group.group_name
            groups.append({'group_name': group_name,
                           'conf_md5': group.group_conf_md5,
                           'reload_status': group.reload_status,
                           'has_conf': bool(DnsNamedConf.query.filter_by(name=group_name).first()),
                           'hosts': [host.json_serialize() for host in DnsHost.query.filter_by(host_group=group_name)]})
        return groups

    @staticmethod
    @commit_on_success
    def add_host_group(group_name, group_type, hosts):
        if DnsHostGroup.query.filter_by(group_name=group_name).first():
            raise BadParam('Host group with name %s already exist.' % group_name, msg_ch=u'主机组%s已经存在' % group_name)
        db.session.add(DnsHostGroup(group_name=group_name, group_type=group_type))
        if hosts:
            db.session.bulk_insert_mappings(DnsHost, hosts)

    @staticmethod
    @commit_on_success
    def delete_host_group(group_name):
        hosts = ['{} {}'.format(host.host_name, host.host_ip) for host in
                 DnsHost.query.filter_by(host_group=group_name).all()]
        if hosts:
            DnsHost.query.filter_by(host_group=group_name).delete()
        DnsHostGroup.query.filter_by(group_name=group_name).delete()
        return hosts

    @staticmethod
    @commit_on_success
    def add_host(group_name, host_name, host_ip):
        try:
            db.session.add(DnsHost(host_name=host_name, host_ip=host_ip, host_group=group_name))
        except Exception as e:
            raise BadParam(e.message, msg_ch='主机名和ip必须唯一')

    @staticmethod
    @commit_on_success
    def delete_host(group_name, host_name):
        if not DnsHost.query.filter_by(host_name=host_name, host_group=group_name).first():
            raise BadParam('No such host: hostname: %s, group: %s' % (host_name, group_name),
                           msg_ch=u'主机不存在')
        DnsHost.query.filter_by(host_name=host_name, host_group=group_name).delete()

    @staticmethod
    def get_named_conf_header(group_name):
        conf = DnsNamedConf.query.filter_by(name=group_name).first()
        if not conf:
            raise BadParam('Can\'t named.conf header for hostgroup: %s' % group_name)
        return conf.conf_content

    @staticmethod
    def check_named_conf(group_name, named_conf):
        tmp_file = tempfile.mktemp(prefix=group_name, dir='/tmp')
        with open(tmp_file, 'w') as f:
            f.write(named_conf)

        if CONF.etc.env != 'dev':
            err_file = tempfile.mktemp(prefix='err_', dir='/tmp')
            if os.system('named-checkconf %s >%s 2>&1 ' % (tmp_file, err_file)) != 0:
                with open(err_file) as f:
                    err = f.read()
                    raise BadParam('Syntax check error for group: %s, ,err: %s' % (group_name, err))

    @staticmethod
    def build_complete_named_conf(group_name, named_conf=None):
        if named_conf is None:
            named_conf = HostGroupConfDal.get_named_conf_header(group_name)
        zone_confs = DnsZoneConf.query.filter_by(zone_group=group_name).order_by(DnsZoneConf.zone_type).all()
        for zone_conf in zone_confs:
            named_conf += '\n'
            named_conf += zone_conf.zone_conf
        HostGroupConfDal.check_named_conf(group_name, named_conf)
        return named_conf

    @staticmethod
    def build_check_conf(group, zone_name, zone_conf):
        named_conf_header = HostGroupConfDal.get_named_conf_header(group)
        for item in DnsZoneConf.query.filter_by(zone_group=group).filter(DnsZoneConf.zone_name != zone_name):
            named_conf_header += '\n'
            named_conf_header += item.zone_conf
        named_conf_header += '\n'
        named_conf_header += zone_conf
        return named_conf_header

    @staticmethod
    @commit_on_success
    def update_named_conf(group_name, conf_content, username):
        conf = DnsNamedConf.query.filter_by(name=group_name).first()
        if not conf:
            raise BadParam('Can\'t find %s named.conf!' % group_name)

        if md5(conf.conf_content).hexdigest() == md5(conf_content).hexdigest():
            raise BadParam('No change')

        named_conf = HostGroupConfDal.build_complete_named_conf(group_name, conf_content)
        group_conf_md5 = md5(named_conf).hexdigest()
        conf.conf_content = conf_content

        # 生成md5写入到数据库中
        DnsHostGroup.query.filter_by(group_name=group_name).update(
            {'group_conf_md5': group_conf_md5}
        )
        hosts = HostGroupConfDal.get_host_by_group(group_name)
        deploy_info = {group_name: {'md5': group_conf_md5, 'hosts': hosts}}
        job_id = start_named_deploy(username, deploy_info)
        return group_conf_md5, job_id

    @staticmethod
    def list_named_zone():
        zone_dict = OrderedDict()
        for item in DnsZoneConf.query.order_by(DnsZoneConf.zone_type, DnsZoneConf.zone_name, DnsZoneConf.zone_group):
            if item.zone_name not in zone_dict:
                zone_dict[item.zone_name] = []
            zone_dict[item.zone_name].append(item.zone_group)
        return [{'zone_name': k, 'zone_group': v} for k, v in zone_dict.items()]

    @staticmethod
    def get_named_zone(zone_name):
        items = DnsZoneConf.query.filter_by(zone_name=zone_name).all()
        if not items:
            raise BadParam('Zone %s has not conf' % zone_name)
        return dict(zone_type=items[0].zone_type,
                    zone_conf=[{'group': item.zone_group, 'conf': item.zone_conf}
                               for item in DnsZoneConf.query.filter_by(zone_name=zone_name)])

    @staticmethod
    def check_zone_conf(group, zone_name, zone_conf):
        name_conf = HostGroupConfDal.build_check_conf(group, zone_name, zone_conf)
        # use named-checkconf tool to check these conf
        HostGroupConfDal.check_named_conf(group, name_conf)

    @staticmethod
    def update_group_reload_status(group_name, reload_status):
        return DnsHostGroup.query.filter_by(group_name=group_name).update({
            'reload_status': reload_status
        })

    @staticmethod
    @commit_on_success
    def update_group_conf_md5(host_groups):
        group_md5_dict = {}
        for group in host_groups:
            group_md5_dict[group] = {}
            named_conf = HostGroupConfDal.build_complete_named_conf(group)
            conf_md5 = md5(named_conf).hexdigest()
            DnsHostGroup.query.filter_by(group_name=group).update({
                'group_conf_md5': md5(named_conf).hexdigest()
            })
            group_md5_dict[group]['hosts'] = HostGroupConfDal.get_host_by_group(group)
            group_md5_dict[group]['md5'] = conf_md5
        return group_md5_dict

    @staticmethod
    def add_named_zone(zone_name, zone_type, conf_dict, add_header, username):
        conf = DnsZoneConf.query.filter_by(zone_name=zone_name).first()
        if conf:
            raise BadParam('zone %s exists' % zone_name)

        zone_group = conf_dict.keys()
        master_groups = [group for group in zone_group if group.lower().endswith('master')]
        if len(master_groups) > 1 or not master_groups:
            raise BadParam('zone must and can only exist in one Master group', msg_ch=u'zone能且只能存在于一组master主机中')
        master_group = master_groups[0]
        with db.session.begin(subtransactions=True):
            for group, zone_conf in conf_dict.items():
                HostGroupConfDal.check_zone_conf(group, zone_name, zone_conf)
                db.session.add(DnsZoneConf(zone_name=zone_name,
                                           zone_conf=zone_conf,
                                           zone_type=zone_type,
                                           zone_group=group))

            group_md5_dict = HostGroupConfDal.update_group_conf_md5(conf_dict.keys())

            if add_header:
                file_name = '../etc/template/zone_header'
                # add template header
                with open(file_name) as f:
                    header = f.read()
                    if len(header) == 0:
                        raise DnsdbException('Can\'t find template header: %s' % file_name)
                    header = header.replace('zone_name', zone_name)
                    header = DnsHeader(zone_name=zone_name, header_content=header)
                    db.session.add(header)

                if zone_type != 0:
                    # add zone serial
                    serial = DnsSerial(zone_name=zone_name,
                                       serial_num=3000000000,
                                       update_serial_num=3000000000,
                                       zone_group=master_groups[0])
                    db.session.add(serial)

        start_zone_header_deploy(username, master_group, zone_name)
        job_id = start_named_deploy(username, group_md5_dict)
        return job_id

    @staticmethod
    @commit_on_success
    def update_named_zone(zone_name, zone_type, conf_dict, username):
        before_items = DnsZoneConf.query.filter_by(zone_name=zone_name).all()
        if not before_items:
            raise BadParam('zone %s not exist' % zone_name)

        update_zone_type = zone_type != before_items[0].zone_type

        before_conf = {item.zone_group: item.zone_conf for item in before_items}
        delete_groups = set(before_conf.keys()) - set(conf_dict.keys())
        for group in delete_groups:
            DnsZoneConf.query.filter_by(zone_name=zone_name, zone_group=group).delete()
        update_group = set()
        for group, zone_conf in conf_dict.items():
            HostGroupConfDal.check_zone_conf(group, zone_name, zone_conf)
            if group not in before_conf:
                update_group.add(group)
                db.session.add(DnsZoneConf(zone_name=zone_name,
                                           zone_conf=zone_conf,
                                           zone_type=zone_type,
                                           zone_group=group))
            elif before_conf[group] != zone_conf:
                update_group.add(group)
                DnsZoneConf.query.filter_by(zone_name=zone_name, zone_group=group).update({
                    'zone_conf': zone_conf
                })
        group_need_update = delete_groups | update_group

        if update_zone_type:
            group_need_update = set(before_conf.keys()) | set(conf_dict.keys())
            DnsZoneConf.query.filter_by(zone_name=zone_name).update({
                'zone_type': zone_type
            })

        if not group_need_update:
            raise BadParam('No change', msg_ch=u'没有要更新的配置')

        group_md5_dict = HostGroupConfDal.update_group_conf_md5(group_need_update)

        return start_named_deploy(username, group_md5_dict)

    @staticmethod
    @commit_on_success
    def delete_named_zone(zone, username):
        group_need_update = {item.zone_group: item.zone_conf for item in DnsZoneConf.query.filter_by(zone_name=zone)}

        DnsRecord.query.filter_by(zone_name=zone).delete()
        DnsSerial.query.filter_by(zone_name=zone).delete()
        DnsHeader.query.filter_by(zone_name=zone).delete()
        DnsZoneConf.query.filter_by(zone_name=zone).delete()

        group_md5_dict = HostGroupConfDal.update_group_conf_md5(group_need_update.keys())
        return group_need_update, start_named_deploy(username, group_md5_dict)
