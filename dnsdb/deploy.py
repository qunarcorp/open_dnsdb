# -*- coding: utf-8 -*-

import json
import threading
import time

from flask import Flask
from oslo.config import cfg

from dnsdb_common.dal import db
# from dnsdb_common.dal.host_group_conf import HostGroupConfDal
from dnsdb_common.dal.operation_log import OperationLogDal
from dnsdb_common.library.api import DnsUpdaterApi
from dnsdb_common.library.email_util import send_alert_email
from dnsdb_common.library.exception import DnsdbException
from dnsdb_common.library.log import setup, getLogger

setup('dnsdb')
log = getLogger(__name__)

CONF = cfg.CONF


def get_flask_app(flask_conf):
    app = Flask(__name__)
    app.config.from_object(flask_conf)
    db.init_app(app)
    return app


class DeployException(DnsdbException):
    def __init__(self, message='Notify deploy conf file error', errcode=500, detail=None, msg_ch=u''):
        super(DeployException, self).__init__(message, errcode, detail, msg_ch)


class DeployThread(threading.Thread):
    def __init__(self, job_id, is_retry=False):
        super(DeployThread, self).__init__()
        self.is_retry = is_retry
        self.state = 'wait'
        self.job_id = job_id
        self.done_host = []
        self.app = get_flask_app(CONF.flask_conf)
        self.deploy_info = {}
        self.deploy_type = ''
        self.expire = 120  # 任务超时时间2分钟
        self.unfinished = {}
        self.notify_failed = []

    # def check_update(self):
    #     event = threading.Event()
    #     while self.expire > 0:
    #         print 'check update'
    #         for group_name in self.unfinished.keys():
    #             info = self.deploy_info[group_name]
    #             conf_md5 = info['md5']
    #             hosts = HostGroupConfDal.get_not_update_host(conf_md5, group_name)
    #             if hosts:
    #                 self.unfinished[group_name] = hosts
    #             else:
    #                 self.unfinished.pop(group_name, None)
    #
    #         if not self.unfinished:
    #             break
    #         event.wait(10)
    #         self.expire -= 10

    def check_normal_update(self):
        time.sleep(self.expire)
        job = OperationLogDal.get_deploy_job(self.job_id)
        if job.op_result == 'start':
            OperationLogDal.update_opration_log(self.job_id, {'op_result': 'fail'})

    def update_depoly_job(self):
        job = OperationLogDal.get_deploy_job(self.job_id)
        data = dict(op_result='ok')
        data['op_after'] = json.loads(job.op_after)
        print json.dumps(data['op_after'], indent=4)
        if self.unfinished:
            data['op_result'] = 'fail'
            data['op_after']['unfinished'] = self.unfinished
            data['op_after'] = json.dumps(data['op_after'])
            send_alert_email(u'主机更新named.conf失败, 主机信息:\n%s' % json.dumps(self.unfinished, indent=4))
        OperationLogDal.update_opration_log(self.job_id, data)

    def update_named_conf(self):
        self.unfinished = {}
        for group_name, info in self.deploy_info.iteritems():
            conf_md5 = info['md5']
            hosts = info['hosts']
            for host_ip in hosts:
                try:
                    print DnsUpdaterApi(host_ip=host_ip).notify_update(self.deploy_type, group_name,
                                                                       group_conf_md5=conf_md5, deploy_id=self.job_id)
                except Exception as e:
                    log.error('notify %s to update %s failed, %s' % (host_ip, self.deploy_type, e))
                    self.notify_failed.append(host_ip)
            self.unfinished[group_name] = hosts

    def update_acl(self):
        hosts = self.deploy_info.get('hosts', {})
        acl_files = self.deploy_info.get('acl_files', [])
        if not hosts or not acl_files:
            OperationLogDal.update_opration_log(self.job_id, {'op_result': 'ok'})
        for group_name, hosts in hosts.iteritems():
            for host in hosts:
                try:
                    print DnsUpdaterApi(host_ip=host).notify_update(self.deploy_type, group_name,
                                                                    deploy_id=self.job_id, acl_files=acl_files)
                except Exception as e:
                    log.error('notify %s to update %s failed, %s' % (host, self.deploy_type, e))
                    self.notify_failed.append(e)

    def run(self):
        with self.app.app_context():
            job = OperationLogDal.get_deploy_job(self.job_id)
            if not job or job.op_result != 'wait':
                raise DeployException('No deploy job id=%s or job state=wait.' % self.job_id)
            OperationLogDal.update_opration_log(self.job_id, {
                'op_result': 'start'
            })
            self.deploy_info = json.loads(job.op_before)
            self.deploy_type = job.op_domain
            if job.op_domain == 'named.conf':
                self.update_named_conf()
            elif job.op_domain == 'acl':
                self.update_acl()
            if self.notify_failed:
                pass
            self.check_normal_update()


def start_deploy_job(user, deploy_info, conf_type, unfinished):
    job_id = OperationLogDal.create_deploy_job(user, deploy_info, conf_type, unfinished)
    thread = DeployThread(job_id)
    thread.start()
    return job_id


def retry_deploy_job(job_id, username):
    if not OperationLogDal.reset_deploy_job(username, job_id):
        raise DeployException('Reset deploy job %s failed' % job_id)
    thread = DeployThread(job_id, is_retry=True)
    thread.start()
    return dict(code=0, data='ok')
