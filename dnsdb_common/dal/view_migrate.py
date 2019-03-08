# -*- coding: utf-8 -*-

import json
from collections import defaultdict
from datetime import datetime

import sqlalchemy

from dnsdb.constant.constant import NORMAL_TO_CNAME
from .models import DnsSerial
from .models import ViewDomainNameState
from .models import ViewIspStatus
from .models import ViewIsps
from .models import ViewMigrateDetail
from .models import ViewMigrateHistory
from .models import ViewRecords
from ..dal import commit_on_success, db
from ..library.exception import DnsdbException, BadParam
from ..library.log import setup, getLogger

setup("dnsdb")
log = getLogger(__name__)


class MigrateDal(object):
    @staticmethod
    @commit_on_success
    def increase_serial_num(zone_list):
        log.info('increase_serial_num: %s', zone_list)
        for zone_name in zone_list:
            serials = DnsSerial.query.filter_by(zone_name=zone_name).all()
            if len(serials) != 1:
                raise BadParam('Zone serial should be unique: %s' % zone_name, msg_ch=u'zone serial记录不存在或者不唯一')
            serial = serials[0]
            serial.serial_num += 1

    @staticmethod
    def get_isp_trans():
        return {record.name_in_english: record.name_in_chinese
                for record in ViewIsps.query}

    @staticmethod
    def get_all_abnormal_isps(key=None, value=None):
        if key is None:
            return ViewIspStatus.query.filter_by(closed=False).order_by(ViewIspStatus.id.desc()).all()
        result_dict = {}
        for status in ViewIspStatus.query.filter_by(closed=False):
            k_v = getattr(status, key)
            v_v = getattr(status, value)
            result_dict.setdefault(k_v, set())
            result_dict[k_v].add(v_v)
        return result_dict

    @staticmethod
    def get_view_domain_rooms():
        domain_rooms = {}
        query = ViewRecords.query.filter_by(record_type='A')
        for result in query.all():
            domain_rooms.setdefault(result.domain_name, set())
            domain_rooms[result.domain_name].add(result.property)
        return domain_rooms

    @staticmethod
    def get_history_info(history_id):
        return ViewMigrateHistory.query.get(history_id)

    @staticmethod
    def get_migrated_history():
        return ViewMigrateHistory.query.filter_by(state='migrated').all()

    @staticmethod
    def get_last_few_history(limit):
        return ViewMigrateHistory.query.order_by(ViewMigrateHistory.id.desc()).limit(limit).all()

    @staticmethod
    def add_migrate_history(migrate_rooms, migrate_isps, dst_rooms, state, cur, length, rtx_id):
        with db.session.begin(subtransactions=True):
            history = ViewMigrateHistory(migrate_rooms, migrate_isps, dst_rooms, state, cur, length,
                                         rtx_id)
            db.session.add(history)
        return history.id

    @staticmethod
    def delete_history_by_id(history_id):
        session = db.session
        with session.begin(subtransactions=True):
            history = session.query(ViewMigrateHistory).get(history_id)
            if history is None:
                log.error('delete_history_by_id error: no ViewMigrateHistory to Delete: %s' % history_id)
                return False, 'No ViewMigrateHistory to Delete: %s' % history_id
            session.delete(history)
        return True, ''

    @staticmethod
    @commit_on_success
    def update_history_total(history_id, length):
        history = ViewMigrateHistory.query.filter(
            ViewMigrateHistory.id == history_id).with_for_update(of=ViewMigrateHistory).first()
        history.all += length

    @staticmethod
    @commit_on_success
    def update_history_count(history_id, count):
        history = ViewMigrateHistory.query.filter(
            ViewMigrateHistory.id == history_id).with_for_update(of=ViewMigrateHistory).first()
        history.cur += count
        if history.all == history.cur:
            history.state = 'migrated'
            history.update_at = datetime.now()

    @staticmethod
    @commit_on_success
    def update_history_by_id(history_id, **kwargs):
        count = ViewMigrateHistory.query.filter_by(id=history_id).update(kwargs)
        return count

    @staticmethod
    @commit_on_success
    def add_or_update_abnormal_isp(user, isp, room):
        count = ViewIspStatus.query.filter_by(isp=isp, room=room, closed=False).update({
            'is_health': False
        })
        if count:
            return True, 'update'
        db.session.add(ViewIspStatus(isp=isp, room=room, update_user=user))
        return True, 'add'

    @staticmethod
    @commit_on_success
    def add_batch_abnormal_isp(user, isp_rooms_dict):
        for isp, rooms in isp_rooms_dict.items():
            for room in rooms:
                MigrateDal.add_or_update_abnormal_isp(user, isp, room)

    @staticmethod
    def list_migrate_domain_by_isp(to_migrate_dict, dst_rooms):
        isp_migrate_domains = {}

        # 得到所有域名与对应机房的结果
        domain_rooms = MigrateDal.get_view_domain_rooms()

        # 符合迁移条件的域名与机房的结果
        for isp, migrate_rooms in to_migrate_dict.items():
            migrate_domains_list = []
            rules = set()
            # 只迁移A记录
            q = (ViewDomainNameState.query.
                 filter_by(isp=isp, state='A').
                 order_by(ViewDomainNameState.domain_name))
            for result in q:
                origin_enabled_rooms = set(json.loads(result.enabled_rooms))
                actual_migrate_rooms = origin_enabled_rooms & migrate_rooms
                if not actual_migrate_rooms:
                    continue

                # 根据迁移规则得到迁移机房列表
                domain = result.domain_name

                after_rooms = [dst_room for dst_room in dst_rooms
                               if dst_room in domain_rooms[domain] and dst_room not in migrate_rooms]

                migrate_domains_list.append({
                    'domain_name': domain,
                    'cur': ','.join(sorted(actual_migrate_rooms)),
                    'after': ','.join(sorted(after_rooms)),
                    'after_enabled_rooms': after_rooms,
                    'eisps': isp
                })

            isp_migrate_domains[isp] = migrate_domains_list

        return isp_migrate_domains

    @staticmethod
    def list_migrate_domain(src_rooms, dst_rooms, to_migrate_isps):
        migrated_isp_rooms = MigrateDal.get_all_abnormal_isps(key='isp', value='room')
        to_migrate_dict = {isp: set(src_rooms) | migrated_isp_rooms.get(isp, set())
                           for isp in to_migrate_isps}

        isp_migrate_domains = MigrateDal.list_migrate_domain_by_isp(to_migrate_dict, dst_rooms)

        domains_cur_after_isps = {}
        for isp, domains in isp_migrate_domains.items():
            for domain_info in domains:
                if not domain_info['cur']:
                    continue
                domain = domain_info['domain_name']
                domains_cur_after_isps.setdefault(domain, defaultdict(list))
                domains_cur_after_isps[domain][(domain_info['cur'], domain_info['after'])].append(domain_info['eisps'])

        domain_isps = []
        trans = MigrateDal.get_isp_trans()
        for domain, rule_isps in domains_cur_after_isps.items():
            for (cur, after), isps in rule_isps.items():
                domain_isps.append({
                    'domain_name': domain,
                    'cur': cur,
                    'after': after,
                    'isps': sorted([trans[eisp] for eisp in isps if eisp])
                })
        return sorted(domain_isps, key=lambda x: x['domain_name'])

    @staticmethod
    def create_migrage_history(username):
        history_id = MigrateDal.add_migrate_history('', '', '', 'migrating', 1, 1, username)
        try:
            ing_count = ViewMigrateHistory.query.filter(
                ViewMigrateHistory.state.in_(ViewMigrateHistory.check_states)).count()
            if ing_count > 1:
                raise DnsdbException('migrate running', msg_ch=u'有正在进行的迁移，请稍后重试')
        except Exception:
            # 删掉占位的历史记录
            MigrateDal.delete_history_by_id(history_id)
            raise
        return history_id

    @staticmethod
    @commit_on_success
    def migrate_domains(domain_infos, history_id):
        # tb_view_domain_name_state 主键 (domain_name, isp)
        for domain_info in domain_infos:
            enabled_rooms = domain_info['after_enabled_rooms']
            cur_state = (ViewDomainNameState.query.
                         filter_by(domain_name=domain_info['domain_name'],
                                   isp=domain_info['eisps'])).first()
            # 记录历史状态信息
            migrate_state = ViewMigrateDetail(migrate_id=history_id, domain_name=cur_state.domain_name,
                                              before_enabled_server_rooms=cur_state.enabled_rooms,
                                              after_enabled_server_rooms=json.dumps(enabled_rooms),
                                              isp=cur_state.isp, before_state=cur_state.state,
                                              after_state='A')
            db.session.add(migrate_state)
            cur_state.enabled_rooms = json.dumps(enabled_rooms)
            cur_state.state = 'A'
        MigrateDal.update_history_count(history_id, len(domain_infos))

    @staticmethod
    @commit_on_success
    def onekey_recover_rooms():
        with db.session.begin(subtransactions=True):
            (ViewIspStatus.query.filter_by(closed=False).
             update({"closed": True,
                     "is_health": True}))
            ViewMigrateHistory.query.filter_by(state='migrated').update({'state': 'recovered'})
            q = ViewDomainNameState.query.filter(sqlalchemy.or_(
                ViewDomainNameState.origin_enabled_rooms != ViewDomainNameState.enabled_rooms,
                ViewDomainNameState.origin_state != ViewDomainNameState.state
            ))
            if q.count() == 0:
                raise BadParam('no domain to recover', msg_ch=u'没有可恢复的域名')
            for item in q:
                item.enabled_rooms = item.origin_enabled_rooms
                item.state = item.origin_state
            MigrateDal.increase_serial_num(NORMAL_TO_CNAME.values())

    @staticmethod
    def get_view_migrate_detail(migrate_id, domain, page, page_size):
        detail_list = []
        migrate_rules = ViewMigrateHistory.query.filter(
            ViewMigrateHistory.id == migrate_id).first().dst_rooms
        query = ViewMigrateDetail.query.filter(ViewMigrateDetail.migrate_id == migrate_id)
        if domain != '':
            query = query.filter(ViewMigrateDetail.domain_name.like('%{}%'.format(domain)))
        total = query.count()
        details = query.order_by(ViewMigrateDetail.domain_name).offset(page_size * (page - 1)).limit(page_size).all()
        trans = MigrateDal.get_isp_trans()
        for detail in details:
            detail_list.append({
                'domain_name': detail.domain_name,
                'isp': trans[detail.isp],
                'before_enabled_server_rooms': ','.join(sorted(json.loads(detail.before_enabled_server_rooms))),
                'after_enabled_server_rooms': ','.join(sorted(json.loads(detail.after_enabled_server_rooms)))
            })
        return {'total': total, 'migrate_rules': ','.join(sorted(json.loads(migrate_rules))), 'detail': detail_list}
