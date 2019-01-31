# -*- coding: utf-8 -*-

from __future__ import print_function
import json
import os
import re

import click
from flask_migrate import Migrate

from dnsdb import createApp
from dnsdb_common.dal import db
from dnsdb_common.dal.user import UserDal
from dnsdb_common.dal.models import *
from dnsdb_common.library.IPy import IP

app = createApp(app_env=os.environ.get('FLASK_ENV', 'beta'), app_kind='dnsdb', conf_dir=os.path.abspath('.'))
migrate = Migrate(app, db)


def parse_zone_conf(zone_conf, group_name):
    start = zone_conf.index("\"")
    zone_name = zone_conf[start + 1:]
    end = zone_name.index('\"')
    zone_name = zone_name[:end]

    # 2 正解 0 反解 1机房
    zone_priority = 2
    if 'ADDR' in zone_name:
        zone_priority = 0

    # 机房zone
    elif zone_name in []:
        zone_priority = 1
    return dict(zone_name=zone_name, zone_conf=zone_conf, zone_group=group_name, zone_type=zone_priority)


def parse_named_conf(filename, group_name):
    with open(filename) as f:
        content = f.read()
        zones = []
        start = content.index("zone ")
        header = content[:start].strip() + '\n'
        end = start
        close_count = 0
        while end < len(content):
            if content[end] == '{':
                close_count += 1
            if content[end] == '}':
                close_count -= 1
            if content[end] == ';' and close_count == 0:
                zones.append(parse_zone_conf(content[start:end + 1], group_name))
                content = content[end + 1:]
                if 'zone ' in content:
                    start = content.index("zone ")
                    end = start
                    continue
                else:
                    break
            end += 1
    return header, zones


def parse_zone_file(zone_name, zone_file, user, only_a=False):
    """
    1、删除以';'开头的注释行
    2、泛域名和非A/CNAME类型的域名保留在zone header中
    3、添加serial
    """
    header_pattern = re.compile(r'\s(TXT|MX|SOA|NS)\s|\$ORIGIN|;|\)|^[\$@\*]|^[\s\d]+$')
    delete_pattern = re.compile(r'^(;.*)?$')
    serial_pattern = re.compile(r'(\d+)(?=\s+; Serial)')

    is_add = True
    record_mapping = []

    records = []
    headers = []
    with open(zone_file) as f:
        for line in f:
            if header_pattern.search(line) is None:
                records.append(line.split())
            elif delete_pattern.search(line) is None:
                headers.append(line)

    header = serial_pattern.sub('pre_serial', ''.join(headers))

    for parts in records:
        if len(parts) != 4 and len(parts) != 5:
            is_add = False
            print(u'%s 记录格式错误： %s, 放弃添加该zone' % (zone_name, parts))
            break

        # 获得完整的域名
        name = parts[0] + '.' + zone_name
        # 如果是cname记录,去掉末尾的'.'
        record = parts[-1].rstrip('.')
        record_type = parts[-2]
        ttl = 0

        # 如果有ttl，解析它
        if len(parts) == 5:
            if 'm' in parts[1]:
                ttl = int(parts[1].replace('m', '')) * 60
            elif 'h' in parts[1]:
                ttl = int(parts[1].replace('h', '')) * 60 * 60
            else:
                ttl = int(parts[1])

        if record_type != 'A' and record_type != 'CNAME':
            header += ' '.join(parts) + '\n'
        if only_a and record_type != "A":
            continue
        record_mapping.append(dict(domain_name=name,
                                   record_type=record_type,
                                   zone_name=zone_name,
                                   update_user=user,
                                   record=record,
                                   ttl=ttl))
    return is_add, header, record_mapping


def _check_subnet_overlap_subnet(subnets):
    # subnet, start, end
    subnets = sorted(subnets, key=lambda x: x[1])
    last_index = len(subnets) - 1
    overlap_subnets = []
    for index, (subnet, start, end) in enumerate(subnets):
        if index == last_index:
            break
        if end > subnets[index + 1][1]:
            overlap_subnets.append((subnet, subnets[index + 1][0]))
    return overlap_subnets


def parse_acl_file(file_name):
    # check if all ecs-subnets match the normal ones
    subnets = []
    split_pattern = re.compile(r'[ ;]')
    with open(file_name) as f:
        for line in f:
            if ('ecs' in line) or ("{" in line) or ('}' in line) or ('#' in line):
                continue
            net = IP(split_pattern.split(line)[0])
            subnets.append((str(net), net.ip, net.broadcast().int()))
    overlap_subnets = _check_subnet_overlap_subnet(subnets)
    return overlap_subnets, subnets


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role,
                DnsZoneConf=DnsZoneConf, DnsNamedConf=DnsNamedConf, DnsHostGroup=DnsHostGroup,
                DnsSerial=DnsSerial, DnsHeader=DnsHeader, DnsColo=DnsColo,
                ViewAclSubnet=ViewAclSubnet, ViewIsps=ViewIsps,
                UserDal=UserDal)


@app.cli.command()
def deploy():
    """Run deployment tasks."""
    db.create_all()
    # create or update user roles
    db.session.begin(subtransactions=True)
    Role.insert_roles()
    UserDal.add_user('test', '', '123456', 1)


@app.cli.command()
@click.option('--group_name', help='HostGroup for this named.conf', default=None)
@click.option('--file_path', default=None, help='Path of file named.conf')
def import_named_conf(group_name, file_path):
    """
    导入某个主机组的named.conf文件
    """
    if not DnsHostGroup.query.filter_by(group_name=group_name).first():
        print(u'主机组%s不存在，请添加主机配置' % group_name)
        return
    if DnsNamedConf.query.filter_by(name=group_name).first():
        print(u'主机组named.conf配置已存在，不允许重复导入')
        return
    header, zones = parse_named_conf(file_path, group_name)
    named_conf = DnsNamedConf(name=group_name, conf_content=header)
    with db.session.begin(subtransactions=True):
        db.session.add(named_conf)
        db.session.bulk_insert_mappings(DnsZoneConf, zones)


@app.cli.command()
@click.option('--zone_dir', help='Directory of zone files')
@click.option('--zone_group', help='HostGroup who manage these zones')
@click.option('--user', help='User name')
def import_zone_records(zone_dir, zone_group, user):
    """
    导入zone到dnsdb, 以zone名命名zone文件
    zone文件中代表serial_num的一行必须是如下格式：
        '3000000026  ; Serial'
    """
    if not DnsHostGroup.query.filter_by(group_name=zone_group).first():
        print(u'主机组%s不存在，请添加主机配置' % zone_group)
        return
    for zone_name in os.listdir(zone_dir):
        if DnsHeader.query.filter_by(zone_name=zone_name).first():
            print(u'%s在DNSDB中已存在，放弃添加该zone' % zone_name)
            continue
        is_add, header, record_mapping = parse_zone_file(zone_name, os.path.join(zone_dir, zone_name), user)
        if not is_add:
            continue

        origin = re.search(r'\$ORIGIN\s+([^\s]+)\s?', header)
        if origin and origin.group(1).strip('.') != zone_name:
            print(u'%s: zone文件名称和文件中"$ORIGIN"定义的zone不同，放弃添加该zone' % zone_name)
            continue
        ttl = re.search(r'\$TTL\s+(\d+)\s?', header)
        if not ttl:
            print(u'无法获取zone的ttl，放弃添加该zone' % zone_name)
            continue
        with db.session.begin(subtransactions=True):
            db.session.add(DnsHeader(zone_name=zone_name, header_content=header))
            db.session.add(DnsSerial(zone_name=zone_name, zone_group=zone_group,
                                     serial_num=3000000000, update_serial_num=3000000000))
            db.session.bulk_insert_mappings(DnsRecord, record_mapping)
        print(u'添加zone %s 管理成功' % zone_name)


@app.cli.command()
@click.option('--zone_file', help='zone file path')
@click.option('--zone_group', help='HostGroup who manage these zones')
@click.option('--user', help='User name')
def import_view_records(zone_file, zone_group, user):
    """
    导入zone到dnsdb, 以zone名命名zone文件
    zone文件中代表serial_num的一行必须是如下格式：
        '3000000026  ; Serial'
    """
    zone_name = zone_file.strip().split('/')[-1]
    is_add, header, record_mapping = parse_zone_file(zone_name, zone_file, user, only_a=True)
    with db.session.begin(subtransactions=True):
        db.session.add(DnsHeader(zone_name=zone_name, header_content=header))
        db.session.add(DnsSerial(zone_name=zone_name, zone_group=zone_group,
                                 serial_num=3000000000, update_serial_num=3000000000))
        if record_mapping:
            db.session.bulk_insert_mappings(DnsRecord, record_mapping)


@app.cli.command()
@click.option('--zone', help='name of zone')
def delete_zone(zone):
    with db.session.begin(subtransactions=True):
        DnsHeader.query.filter_by(zone_name=zone).delete()
        DnsSerial.query.filter_by(zone_name=zone).delete()
        DnsRecord.query.filter_by(zone_name=zone).delete()


@app.cli.command()
@click.option('--colos', help=u'机房，以逗号隔开 "bj1,bj2"')
@click.option('--group', default='subnet', help=u'机房所属配置组, 默认 subnet（用于ip管理）')
@click.option('--user', default='admin', help=u'用户名, 默认 admin')
def add_colo_config(colos, user, group):
    if colos is None:
        print(u'缺少必要的参数: --colos')
        return
    colos = colos.split(',')
    exist = [item.colo_name for item in DnsColo.query.filter_by(colo_group=group)]
    colo_mapping = [dict(colo_name=item, colo_group=group, create_user=user) for item in set(colos) - set(exist)]
    with db.session.begin(subtransactions=True):
        db.session.bulk_insert_mappings(DnsColo, colo_mapping)


@app.cli.command()
@click.option('--acl_dir', help='acl file')
@click.option('--user', help='user name', default='admin')
def import_acl_subnet(acl_dir, user, add_overlap=True):
    if not acl_dir:
        print(u'缺少必要的参数: --acl_dir')
        return

    isp_config = [
        # dict(name_in_english='chinanet', abbreviation='ct',
        #      name_in_chinese=u'中国电信', acl_name='CHINANET', acl_file='CHINANET.acl', username=user)
    ]

    if isp_config:
        with db.session.begin(subtransactions=True):
            db.session.bulk_insert_mappings(ViewIsps, isp_config)
        print('add isp conf success')

    has_effect = False
    overlap = {}
    for item in ViewIsps.query.all():
        acl_file = item.acl_file
        if not acl_file:
            continue
        acl_name = item.acl_name
        acl_path = os.path.join(acl_dir, acl_file)
        if not os.path.exists(acl_path):
            continue
        if ViewAclSubnet.query.filter_by(origin_acl=acl_name).first():
            print('There already have subnet for %s in database' % acl_name)
            continue

        overlap_subnets, subnets = parse_acl_file(acl_path)
        if overlap_subnets:
            overlap[acl_file] = overlap_subnets
            if not add_overlap:
                continue

        subnet_mapping = []
        for subnet, start, end in subnets:
            subnet_mapping.append(dict(
                subnet=subnet,
                start=start,
                end=end,
                origin_acl=acl_name,
                now_acl=acl_name,
                update_user=user
            ))
        with db.session.begin(subtransactions=True):
            db.session.bulk_insert_mappings(ViewAclSubnet, subnet_mapping)
        print('Import acl_file %s success' % acl_file)
        has_effect = True

    if overlap:
        print('There are overlap_subnets in files:'.format(overlap.keys()))
        print(json.dumps(overlap, indent=4))

    if not has_effect:
        print('Import no acl file.')
