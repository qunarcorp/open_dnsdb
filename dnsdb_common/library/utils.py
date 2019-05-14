#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
import ipaddress
import os
import re
import socket
from importlib import import_module

from oslo_config import cfg

from dnsdb_common.dal import db
from dnsdb_common.dal.models import DnsHeader
from dnsdb_common.dal.models import DnsSerial
from dnsdb_common.library.exception import DnsdbException, BadParam
from dnsdb_common.library.log import getLogger

log = getLogger(__name__)

CONF = cfg.CONF

IP_PATTERN = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")


def has_no_mx_txt_record(zone, domain_name):
    session = db.session
    zone_header = session.query(DnsHeader.header_content).filter(DnsHeader.zone_name == zone).first()
    if not zone_header:
        return False, 'No such zone header: %s' % zone
    # 是否存在MX TXT记录
    pattern = r'\s{0}[\s\d]+IN\s+MX|\s{0}[\s\d]+IN\s+TXT'.format(domain_name.replace('.' + zone, ''))
    if re.search(pattern, zone_header[0]):
        return False, '%s has mx or txt record in zone: %s' % (domain_name, zone)
    return True, 'ok'


def is_valid_domain_name_v2(domain_name):
    if domain_name is None or not is_string(domain_name):
        raise BadParam("None str type:%s." % domain_name, msg_ch=u'域名参数为空')
    if len(domain_name) > 256:
        raise BadParam("Domain name %s is too long." % domain_name, msg_ch=u'域名长度需小于256')
    if len(domain_name.split(".")) < 2:
        raise BadParam("not enough level:%s" % domain_name, msg_ch=u'域名至少是一个二级域名')
    if re.match("^(\*\.)?([0-9a-zA-Z][-0-9a-zA-Z]{0,63}\.)+[a-z]{0,63}$", domain_name) is None or domain_name.find(
            "-.") != -1:
        raise BadParam("Invalid formation:%s" % domain_name, msg_ch=u'域名中只能包含[-.0-9a-zA-Z], %s' % domain_name)
    return True


def is_valid_domain_name(domain_name):
    is_valid_domain_name_v2(domain_name)
    if domain_name.startswith('*.'):
        raise BadParam('Domain name cannot include "*"', msg_ch='域名中不能包含 *')
    return True

def format_ip(ip):
    try:
        ip = ipaddress.ip_address(ip)
    except Exception as e:
        raise BadParam('Invalid ip format: %s' % e, msg_ch='ip格式错误')
    return str(ip), ip.version

def format_ipv4(ip):
    if '.' not in ip:
        raise BadParam('Invalid IPv6 format', msg_ch='IPv4格式错误')
    try:
        ip = ipaddress.ip_address(ip)
    except Exception as e:
        raise BadParam('Invalid ip format: %s' % e, msg_ch='ip格式错误')
    return str(ip)


def format_ipv6(ip):
    if ':' not in ip:
        raise BadParam('Invalid IPv6 format', msg_ch='IPv6格式错误')
    try:
        ip = ipaddress.ip_address(ip)
    except Exception as e:
        raise BadParam('Invalid ip format: %s' % e, msg_ch='ip格式错误')
    return str(ip)


def get_ip_int_str(ip, is_ipv6):
    str_ip = str(int(ip))
    length = 10
    if is_ipv6:
        length = 39
    return '0' * (length - len(str_ip)) + str_ip


def format_subnet(subnet):
    try:
        subnet_obj = ipaddress.ip_network(subnet)
    except:
        raise BadParam('invalid subnet: %s' % subnet, msg_ch='网段格式错误: %s' % subnet)
    start_ip = subnet_obj.network_address
    end_ip = subnet_obj.broadcast_address
    is_ipv6 = (subnet_obj.version == 6)
    return str(subnet_obj), is_ipv6, float(int(start_ip)), float(int(end_ip))


def is_valid_ip_bysocket(ip):
    if not ip or '\x00' in ip:
        # getaddrinfo resolves empty strings to localhost, and truncates
        # on zero bytes.
        return False
    try:
        res = socket.getaddrinfo(ip, 0, socket.AF_UNSPEC,
                                 socket.SOCK_STREAM,
                                 0, socket.AI_NUMERICHOST)
        return bool(res)
    except socket.gaierror as e:
        if e.args[0] == socket.EAI_NONAME:
            return False
        raise


def is_string(s):
    return isinstance(s, str)


def select_best_matched_domain(db, domain_name):
    if not db.execute_sql("SELECT zone_name FROM tb_dns_serial"):
        log.error("Failed to select zone_name from tb_dns_serial.")
        return False, "DB ERROR."
    ok, result = db.fetchall()
    if not ok:
        log.error("Failed to fetch result.")
        return False, "DB ERROR."
    best_matched_domain = None
    deepest_domain_level = 0
    for i in result:
        if domain_name.endswith(i[0]):
            domain_level_len = len(i[0].split("."))
            if domain_level_len > deepest_domain_level:
                deepest_domain_level = domain_level_len
                best_matched_domain = i[0]
    if best_matched_domain is None:
        log.error("No domain contains this domain name:%s." % (domain_name))
        return False, "No domain contains this domain name."
    return True, best_matched_domain


def format_time(time_str, time_type):
    if time_type == 'start':
        t = datetime.datetime.strptime(time_str, '%Y-%m-%d')
    else:
        t = datetime.datetime.strptime(time_str, '%Y-%m-%d')
        t = t + datetime.timedelta(days=1)
    return t.strftime('%Y-%m-%d %H:%M:%S')


def get_obj_name(obj):
    return '.'.join((obj.__module__, obj.__name__))


def get_obj_by_name(obj_name):
    try:
        module_name, name = obj_name.rsplit('.', 1)
        module_obj = import_module(module_name)
        return getattr(module_obj, name)
    except Exception:
        raise DnsdbException('Get object %s failed.' % obj_name)


def is_valid_cname(cname):
    session = db.session
    if is_valid_domain_name_v2(cname) and not cname.startswith('*.'):
        zones = set([zone[0] for zone in session.query(DnsSerial.zone_name).all()])
        for index in range(1, len(cname.split('.'))):
            if cname.split('.', index)[-1] in zones:
                return True
    return False


def get_dict_from_table(obj):
    res = {}
    for k, v in obj.__dict__.items():
        if not k.startswith('_'):
            res[k] = v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v, datetime.datetime) else v
    return res


def make_tmp_dir(tmp_dir):
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)
    return tmp_dir
