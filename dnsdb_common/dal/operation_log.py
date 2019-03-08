# -*- coding: utf-8 -*-

import json
from datetime import datetime
from datetime import timedelta

from . import db, commit_on_success
from .models import OperationLog
from .models import OperationLogDetail


def format_time(time_str, time_type):
    if time_type == 'start':
        t = datetime.strptime(time_str, '%Y-%m-%d')
    else:
        t = datetime.strptime(time_str, '%Y-%m-%d')
        t = t + timedelta(days=1)
    return t.strftime('%Y-%m-%d %H:%M:%S')


class OperationLogDal(object):
    @staticmethod
    def insert_operation_log_with_dict(rtx_id, op_domain, op_type, op_before, op_after, op_result, reason=None):
        session = db.session
        with session.begin(subtransactions=True):
            item = OperationLog(
                rtx_id=rtx_id,
                op_domain=op_domain,
                op_type=op_type,
                op_before=json.dumps(op_before),
                op_after=json.dumps(op_after),
                op_time=datetime.now(),
                op_result=op_result
            )
            session.add(item)

        if op_result == 'fail' and reason is not None:
            OperationLogDal.add_log_detail(OperationLog.id, reason)
        return item.id

    @staticmethod
    def add_log_detail(log_id, reason):
        session = db.session
        if not isinstance(reason, str):
            reason = str(reason)
        if len(reason) > 1024:
            reason = reason[:1024]
        with session.begin(subtransactions=True):
            session.add(OperationLogDetail(
                log_id=log_id,
                detail=reason
            ))

    @staticmethod
    def list_operation_log(condition):
        query = OperationLog.query
        if condition['start_time'] != '' and condition['start_time'] != '':
            query = query.filter(
                OperationLog.op_time.between(format_time(condition['start_time'], 'start'),
                                             format_time(condition['end_time'], 'end')))
        if 'domain' in condition:
            query = query.filter(OperationLog.op_domain == condition['domain'])
        if 'type' in condition:
            query = query.filter(OperationLog.op_type == condition['type'])
        if 'rtx_id' in condition:
            query = query.filter(OperationLog.rtx_id == condition['rtx_id'])
        total = query.count()
        logs = query.order_by(OperationLog.op_time.desc()).offset(
            condition['page_size'] * (condition['page'] - 1)).limit(
            condition['page_size']).all()
        result = []
        for log in logs:
            result.append(log.json_serialize())

        return {'total': total, 'logs': result}

    @staticmethod
    def get_log_detail(log_id):
        item = OperationLogDetail.query.filter_by(log_id=log_id).first()
        if not item:
            return ''
        return item.detail

    @staticmethod
    def create_deploy_job(user, deploy_info, conf_type, unfinished):
        return OperationLogDal.insert_operation_log_with_dict(user, conf_type,
                                                              'conf_deploy', deploy_info,
                                                              dict(successed=[], failed={}, unfinished=unfinished), 'wait')

    @staticmethod
    def get_deploy_job(job_id):
        return OperationLog.query.get(job_id)

    @staticmethod
    def reset_deploy_job(user, job_id):
        item = OperationLog.query.get(job_id)
        if not item:
            return item

        op_info = json.loads(item.op_before)
        op_domain = item.op_domain
        unfinished = []
        if op_domain == 'named.conf':
            for group, info in op_info.items():
                unfinished.extend(info['hosts'])
        elif op_domain == 'acl':
            for group, hosts in op_info.get('hosts', {}).items():
                unfinished.extend(hosts)
        elif op_domain == 'zone':
            unfinished.extend(op_info.get('hosts', []))

        data = dict(op_time=datetime.now(), op_result='wait', op_after=json.dumps(dict(successed=[], failed={}, unfinished=unfinished)))
        return OperationLogDal.update_opration_log(job_id, data)

    @staticmethod
    @commit_on_success
    def update_opration_log(job_id, data):
        return OperationLog.query.filter_by(id=job_id).update(data)

    @staticmethod
    def update_deploy_info(deploy_id, host, is_success, msg):
        # json.dumps(dict(success=[], failed={}, unfinish=[]))
        job = OperationLogDal.get_deploy_job(deploy_id)
        op_after = json.loads(job.op_after)
        success = op_after.get('successed', [])
        unfinish = op_after.get('unfinished', [])
        failed = op_after.get('failed', {})

        if host in unfinish:
            unfinish.remove(host)
            op_after['unfinished'] = unfinish

        if is_success:
            success.append(host)
            op_after['successed'] = success
        else:
            failed[host] = msg
            op_after['failed'] = failed

        data = dict(op_after=json.dumps(op_after))
        if not unfinish:
            data['op_result'] = 'ok'
            if failed:
                data['op_result'] = 'fail'
        OperationLogDal.update_opration_log(deploy_id, data)
