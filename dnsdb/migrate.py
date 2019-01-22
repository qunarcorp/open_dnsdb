# -*- coding: utf-8 -*-

import threading
import json
from oslo.config import cfg

from dnsdb import get_flask_app
from dnsdb.constant.constant import ZONE_MAP
from dnsdb_common.dal.view_migrate import MigrateDal
from dnsdb_common.library.log import setup, getLogger
from dnsdb_common.library.exception import BadParam

setup("dnsdb")
log = getLogger(__name__)

CONF = cfg.CONF

def format_history(histories):
    history_list = []
    trans = MigrateDal.get_isp_trans()
    for history in histories:
        history_list.append({
            'id': history.id,
            'migrate_rooms': sorted(json.loads(history.migrate_rooms)),
            'dst_rooms': sorted(json.loads(history.dst_rooms)),
            'migrate_isps': sorted([trans[isp] for isp in json.loads(history.migrate_isps)]),
            'cur': history.cur,
            'all': history.all,
            'state': history.state,
            'rtx_id': history.rtx_id,
            'update_at': history.updated_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    return history_list

def get_migrate_info(history_id):
    try:
        history_id = int(history_id)
    except Exception:
        raise BadParam('id should be int')
    return format_history([MigrateDal.get_history_info(history_id)])

def migrate_rooms(src_rooms, dst_rooms, to_migrate_isps, username):
    history_id = MigrateDal.create_migrage_history(username)

    migrated_isp_rooms = MigrateDal.get_all_abnormal_isps(key='isp', value='room')
    to_migrate_dict = {isp: set(src_rooms) | migrated_isp_rooms.get(isp, set())
                       for isp in to_migrate_isps}

    migrate_isp_domains = MigrateDal.list_migrate_domain_by_isp(to_migrate_dict, dst_rooms)

    has_migrate_domains = False
    for isp, migrate_domains_list in migrate_isp_domains.iteritems():
        migrate_domains_list = [domain for domain in migrate_domains_list if domain['after_enabled_rooms']]
        if len(migrate_domains_list) == 0:
            continue
        has_migrate_domains = True
        MigrateDal.update_history_total(history_id, len(migrate_domains_list))
        m_thread = MigrateThread(username, history_id, migrate_domains_list)
        m_thread.start()

    if has_migrate_domains:
        MigrateDal.add_batch_abnormal_isp(username, to_migrate_dict)
        # send_alert_email("[FROM DNSDB]: 机房{}上运营商{}迁移到{}啦.".format(src_rooms, to_migrate_isps, dst_rooms))
        MigrateDal.update_history_by_id(history_id,
                                        migrate_rooms=json.dumps(src_rooms),
                                        migrate_isps=json.dumps(to_migrate_isps),
                                        dst_rooms=json.dumps(dst_rooms),
                                        migrate_info=json.dumps({}))
    else:
        MigrateDal.delete_history_by_id(history_id)
        raise BadParam("no domain can migrate, isp_rooms: %s"
                       % to_migrate_dict, msg_ch=u'没有可迁移的机房')

    history_info = get_migrate_info(history_id)
    return history_info

def list_migrate_history():
    return format_history(MigrateDal.get_last_few_history(limit=15))


class MigrateThread(threading.Thread):
    def __init__(self, rtx_id, migrate_history_id, migrate_domain_list):
        super(MigrateThread, self).__init__()
        self.app = get_flask_app()
        self.step = 100
        self.rtx_id = rtx_id
        self.migrate_history_id = migrate_history_id
        self.migrate_domain_list = migrate_domain_list

    def run(self):
        with self.app.app_context():
            for i in range(0, len(self.migrate_domain_list), self.step):
                try:
                    MigrateDal.migrate_domains(self.migrate_domain_list[i: i + self.step], self.migrate_history_id)
                except Exception as e:
                    log.error('migrate rooms failed:%s' % e)
                    MigrateDal.update_history_by_id(self.migrate_history_id, state='error')
                    return
            # 更新serial
            MigrateDal.increase_serial_num(ZONE_MAP.keys())
