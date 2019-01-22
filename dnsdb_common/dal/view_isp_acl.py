# -*- coding: utf-8 -*-

from flask_login import current_user
from oslo.config import cfg
from dnsdb.deploy import start_deploy_job

from . import commit_on_success
from . import db
from .models import ViewAclSubnet
from .models import ViewIsps
from ..dal.host_group_conf import HostGroupConfDal
from ..library.IPy import IP
from ..library.exception import BadParam

CONF = cfg.CONF


def start_acl_deploy_job(user, acl_list, conf_type='acl'):
    acl_groups = CONF.etc.view_acl_group.split(',')
    hosts = {}
    unfinished = []
    for group in acl_groups:
        tmp = HostGroupConfDal.get_host_by_group(group)
        hosts[group] = tmp
        unfinished.extend(tmp)
    acl_files = ViewIspAclDal.get_acl_files(acl_list)
    deploy_info = dict(acl_files=acl_files, hosts=hosts)

    return start_deploy_job(user, deploy_info, conf_type, unfinished)


class ViewIspAclDal(object):
    @staticmethod
    def list_isp():
        return [item.json_serialize() for item in ViewIsps.query.all()]

    @staticmethod
    def get_acl_files(acl_list):
        acl_file = set()
        records = ViewIsps.query.filter(ViewIsps.acl_name.in_(acl_list))
        for record in records:
            if record.acl_file:
                acl_file.add(record.acl_file)
        return list(acl_file)

    @staticmethod
    def get_acl_file_content(acl_file):
        acl_names = [item.acl_name for item in ViewIsps.query.filter_by(acl_file=acl_file)]
        file_content = ''
        for acl in acl_names:
            subnets = (db.session.query(ViewAclSubnet.subnet).
                       filter_by(now_acl=acl).
                       order_by(ViewAclSubnet.updated_time.desc(), ViewAclSubnet.id))
            file_content += 'acl %s {\n' % acl
            for subnet in subnets:
                file_content += '%s;\n' % subnet.subnet
            file_content += '};\n'
        return file_content

    @staticmethod
    def list_acl_isp():
        return {item['acl_name']: item['name_in_chinese'] for item in ViewIspAclDal.list_isp() if item['acl_name']}

    @staticmethod
    def list_acl_subnet_by_ip(ip):
        # ip格式校验
        try:
            int_ip = IP(ip).ip
        except:
            raise BadParam('invalid ip: %s' % ip, msg_ch=u'错误的ip格式')

        items = ViewAclSubnet.query.filter(ViewAclSubnet.start <= int_ip).filter(
            ViewAclSubnet.end >= int_ip).order_by(ViewAclSubnet.start)
        return [item.json_serialize() for item in items]

    @staticmethod
    def get_migrate_subnet():
        return [item.json_serialize()
                for item in ViewAclSubnet.query.filter(ViewAclSubnet.origin_acl != ViewAclSubnet.now_acl)]

    @staticmethod
    @commit_on_success
    def add_acl_subnet(subnet, acl, username):
        if not ViewIsps.query.filter_by(acl_name=acl).first():
            raise BadParam('acl not in database: %s' % acl, msg_ch=u'ACL在dnsdb中无记录')
        try:
            subnet_obj = IP(subnet)
        except:
            raise BadParam('invalid subnet: %s' % subnet, msg_ch=u'网段格式错误: %s' % subnet)
        subnet = str(subnet_obj)
        start_ip = subnet_obj.ip
        end_ip = subnet_obj.broadcast().int()

        q1 = (ViewAclSubnet.query.filter_by(origin_acl=acl).
              filter(ViewAclSubnet.start <= start_ip).filter(ViewAclSubnet.end >= start_ip).first())
        q2 = (ViewAclSubnet.query.filter_by(origin_acl=acl).
              filter(ViewAclSubnet.start <= end_ip).filter(ViewAclSubnet.end >= end_ip).first())
        if q1 or q2:
            raise BadParam('subnet overlap with subnet in this acl', msg_ch=u'与运营商中已有网段交叉')

        db.session.add(ViewAclSubnet(
                subnet=subnet,
                start=start_ip,
                end=end_ip,
                origin_acl=acl,
                now_acl=acl,
                update_user=username
            ))
        start_acl_deploy_job(username, [acl])

    @staticmethod
    @commit_on_success
    def delete_acl_subnet(subnet_id, username):
        subnet = ViewAclSubnet.query.filter_by(id=subnet_id).first()
        if not subnet:
            raise BadParam('No such acl subnet record: %s' % subnet_id, msg_ch=u'没有对应的网段记录')
        db.session.delete(subnet)
        subnet_info = subnet.json_serialize(include=['subnet', 'origin_acl', 'now_acl'])

        origin = subnet_info['origin_acl']
        now = subnet_info['now_acl']
        start_acl_deploy_job(username, [now] if now == origin else [now, origin])
        return subnet_info

    @staticmethod
    @commit_on_success
    def add_isp(data):
        db.session.add(ViewIsps(**data))

    @staticmethod
    def update_isp(name_in_english, update_data, username):
        update_data['username'] = username
        return ViewIsps.query.filter_by(name_in_english=name_in_english).update(update_data)

    @staticmethod
    @commit_on_success
    def delete_isp(name_in_english):
        return ViewIsps.query.filter_by(name_in_english=name_in_english).delete()

    @staticmethod
    def migrate_acl(acl_subnet_id, to_acl):
        username = current_user.username
        if not ViewIsps.query.filter_by(acl_name=to_acl).first():
            raise BadParam('no such acl: %s' % to_acl, msg_ch=u'没有acl记录: %s' % to_acl)
        try:
            acl_subnet_id = int(acl_subnet_id)
        except Exception:
            raise BadParam('acl_subnet_id should be int: %d' % acl_subnet_id)

        with db.session.begin(subtransactions=True):
            try:
                acl_subnet = ViewAclSubnet.query.get(acl_subnet_id)
            except Exception:
                raise BadParam('No such acl_subnet with id: %d' % acl_subnet_id, msg_ch=u'没有网段记录: %s' % acl_subnet_id)

            from_acl = acl_subnet.now_acl
            if to_acl == from_acl:
                raise BadParam('Same isp, no need to migration', msg_ch=u'目标运营商和原运营商行相同，无需迁移')

            acl_subnet.now_acl = to_acl
            acl_subnet.update_user = username
            db.session.add(acl_subnet)

            # 更新acl
            start_acl_deploy_job(username, [from_acl, to_acl])
            acl_isp = ViewIspAclDal.list_acl_isp()
            op_after = {'from_isp': acl_isp[from_acl], 'to_isp': acl_isp[to_acl],
                        'subnet': acl_subnet.subnet, 'is_recover': to_acl == acl_subnet.origin_acl}
            return op_after
