# -*- coding: utf-8 -*-
from dnsdb_common.library.IPy import IP
from dnsdb_common.library.exception import BadParam
from . import commit_on_success
from . import db
from .models import DnsColo
from .models import DnsRecord
from .models import IpPool
from .models import Subnets


class SubnetIpDal(object):
    @staticmethod
    def get_colo_by_group(group):
        return [record.colo_name
                for record in
                db.session.query(DnsColo.colo_name).filter_by(colo_group=group).order_by(DnsColo.colo_name)]

    @staticmethod
    def list_region(**condition):
        q = Subnets.query
        if condition:
            q = q.filter_by(**condition)
        return [item.json_serialize() for item in q.order_by(Subnets.region_name, Subnets.subnet)]

    @staticmethod
    def get_region_by_ip(ip):
        record = IpPool.query.filter_by(fixed_ip=ip).first()
        if not record:
            raise BadParam('no such ip: %s' % ip, msg_ch=u'没有对应的ip记录')
        return SubnetIpDal.get_region_by_name(record.region)

    @staticmethod
    def get_region_by_name(region):
        record = Subnets.query.filter_by(region_name=region).first()
        if not record:
            raise BadParam('no such subnet with region_name: %s' % region, msg_ch=u'没有对应的网段记录')
        return record.json_serialize()

    @staticmethod
    def is_intranet_region(region):
        record = Subnets.query.filter_by(region_name=region).first()
        if not record:
            raise BadParam('no such subnet with region_name: %s' % region, msg_ch=u'没有对应的网段记录')
        return record.intranet

    @staticmethod
    def is_ip_exist(record):
        return IpPool.query.filter_by(fixed_ip=record).first() is not None

    @staticmethod
    def get_subnet_ip(region):
        records = IpPool.query.outerjoin(DnsRecord, DnsRecord.record == IpPool.fixed_ip).add_columns(
            IpPool.fixed_ip, IpPool.allocated,
            DnsRecord.domain_name).filter(IpPool.region == region).order_by(IpPool.fixed_ip)
        result = [{"ip": item.fixed_ip, "domain": item.domain_name} for item in records]
        return result

    @staticmethod
    def add_subnet(subnet, region, colo, comment, username):
        subnet = IP(subnet)
        intranet = subnet.iptype() == 'PRIVATE'
        net_id = subnet.net()
        broadcast_ip = subnet.broadcast()
        ips_dict_list = []
        for i in subnet:
            if i == net_id or i == broadcast_ip:
                continue
            ips_dict_list.append({
                'region': region,
                'fixed_ip': str(i)
            })
        try:
            with db.session.begin(subtransactions=True):
                subnet_item = Subnets(
                    region_name=region,
                    subnet=subnet.strCompressed(),
                    create_user=username,
                    intranet=intranet,
                    colo=colo
                )
                if comment:
                    subnet_item.comment = comment
                db.session.add(subnet_item)
                db.session.bulk_insert_mappings(IpPool, ips_dict_list)
        except Exception:
            raise BadParam('Ip conflict with other regions', msg_ch=u'和已有的网段有交叉，请检查后重试')

    @staticmethod
    @commit_on_success
    def delete_subnet(subnet, region):
        record = Subnets.query.filter_by(region_name=region, subnet=subnet).first()
        if not record:
            raise BadParam('Region does not exist: %s' % region, msg_ch=u'网段不存在')
        # 删除一个region
        ip_records = SubnetIpDal.get_subnet_ip(region)
        if filter(lambda x: x['domain'], ip_records):
            raise BadParam('Region %s has records,delete failed!' % region, msg_ch=u'网段正在使用中，不允许删除')

        Subnets.query.filter_by(region_name=region, subnet=subnet).delete()
        IpPool.query.filter_by(region=region).delete()


    @staticmethod
    @commit_on_success
    def rename_subnet(old_region, new_region, username):
        if Subnets.query.filter_by(region_name=new_region).first():
            raise BadParam("Region %s existed, rename %s failed" % (new_region, old_region),
                           msg_ch=u'%s已经存在' % new_region)
        if not Subnets.query.filter_by(region_name=old_region).first():
            raise BadParam("Region %s does not existed, rename failed" % old_region,
                           msg_ch=u'%s不存在' % old_region)
        Subnets.query.filter(Subnets.region_name == old_region).update({
            "region_name": new_region
        })
        IpPool.query.filter(IpPool.region == old_region).update({
            'region': new_region
        })

    @staticmethod
    def get_subnets_by_condition(**kwargs):
        session = db.session
        query = session.query(Subnets)
        if kwargs:
            query = query.filter_by(**kwargs)
        return query.order_by(Subnets.region_name, Subnets.subnet).all()

    @staticmethod
    def get_region_domains(region_name, limit):
        sql = """SELECT tb_record.name FROM tb_ippool LEFT JOIN tb_record\
                                ON tb_record.records = host(tb_ippool.fixed_ips)
                                WHERE tb_ippool.region = '%(region)s' and tb_record.name is not null
                                limit %(limit)d;""" % {'region': region_name, 'limit': limit}
        return db.session.execute(sql).fetchall()

    @staticmethod
    def bulk_update_subnet(update_mapping):
        session = db.session
        with session.begin(subtransactions=True):
            session.bulk_update_mappings(Subnets, update_mapping)
