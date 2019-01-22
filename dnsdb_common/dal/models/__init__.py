# -*- coding: utf-8 -*-

from datetime import date
from datetime import datetime

from dnsdb_common.library.exception import BadParam

from .. import db

db.Model = db.Model

__all__ = [
    "AnonymousUser",
    "AuditTimeMixin",
    "DeployHistory",
    "DnsHeader",
    "DnsHost",
    "DnsHostGroup",
    "OperationLog",
    "OperationLogDetail",
    "DnsNamedConf",
    "DnsRecord",
    "DnsSerial",
    "DnsZoneConf",
    "IpPool",
    "DnsColo",
    "Role",
    "Subnets",
    "User",
    "ViewAclCityCode",
    "ViewAclMigrateHistory",
    "ViewAclSubnet",
    "ViewConfigs",
    "ViewDomainNameState",
    "ViewDomainNames",
    "ViewIspStatus",
    "ViewIsps",
    "ViewMigrateDetail",
    "ViewMigrateHistory",
    "ViewRecords",
    "ViewSwitchIpDetail",
    "ViewSwitchIpHistory"
]


class JsonMixin(object):
    def json_serialize(self, include=None, exclude=None):
        def __format(val):
            if isinstance(val, datetime):
                return val.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(val, date):
                return val.strftime('%Y-%m-%d')
            return val

        filter_func = None
        if include is not None:
            if not isinstance(include, (list, tuple)):
                raise BadParam('param <include> should be [list, tuple]')
            filter_func = lambda x: x in include
        elif exclude is not None:
            if not isinstance(exclude, (list, tuple)):
                raise BadParam('param <exclude> should be [list, tuple]')
            filter_func = lambda x: x not in include

        fields = self.__mapper__.mapped_table.columns.keys()
        if filter_func is not None:
            fields = filter(filter_func, fields)
        return dict(((f, __format(getattr(self, f))) for f in fields))


class AuditTimeMixin(object):
    created_time = db.Column(db.DateTime, default=datetime.now)
    updated_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


from .deploy_history import DeployHistory
from .dns_header import DnsHeader
from .dns_host import DnsHost
from .dns_host_group import DnsHostGroup
from .operation_log import OperationLog
from .operation_log_detail import OperationLogDetail
from .dns_named_conf import DnsNamedConf
from .dns_record import DnsRecord
from .dns_serial import DnsSerial
from .dns_zone_conf import DnsZoneConf
from .ippool import IpPool
from .dns_colos import DnsColo
from .subnets import Subnets
from .user import AnonymousUser
from .user import Role
from .user import User
from .view_acl_city_code import ViewAclCityCode
from .view_acl_migrate_history import ViewAclMigrateHistory
from .view_acl_subnets import ViewAclSubnet
from .view_config import ViewConfigs
from .view_domain_name_state import ViewDomainNameState
from .view_domain_names import ViewDomainNames
from .view_isp_status import ViewIspStatus
from .view_isps import ViewIsps
from .view_migrate_detail import ViewMigrateDetail
from .view_migrate_history import ViewMigrateHistory
from .view_records import ViewRecords
from .view_switch_ip_detail import ViewSwitchIpDetail
from .view_switch_ip_history import ViewSwitchIpHistory
