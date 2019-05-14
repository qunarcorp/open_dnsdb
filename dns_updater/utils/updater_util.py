# -*- coding: utf-8 -*-

import io
import json
import os
import re
import shutil
import socket
import subprocess as sp
from datetime import datetime
from shlex import split

from oslo_config import cfg

from dnsdb_common.library.api import Api
from dnsdb_common.library.email_util import send_email
from dnsdb_common.library.exception import UpdaterErr
from dnsdb_common.library.log import getLogger
from dnsdb_common.library.utils import make_tmp_dir

log = getLogger(__name__)

CONF = cfg.CONF


def run_command_with_code(cmd, check_exit_code=True):
    """Runs a command in an out-of-process shell.

    Returns the output of that command. Working directory is self.root.
    """

    proc = sp.Popen(split(cmd), stdout=sp.PIPE, stderr=sp.PIPE, encoding='utf-8')
    output = proc.communicate()[0]
    retcode = proc.returncode
    if check_exit_code and retcode != 0:
        raise UpdaterErr('Command "%s" failed.\n%s' % (cmd, output))
    log.info('Command "%s" success.' % ' '.join(cmd))
    return output, retcode

def check_necessary_options():
    needed_conf_options = {
        'etc': ["log_dir", "tmp_dir", "backup_dir", "pidfile", 'env'],
        'MAIL': ['from_addr', 'server', 'port', 'info_list', 'alert_list'],
    }

    for section, options in needed_conf_options.items():
        if not hasattr(CONF, section):
            raise UpdaterErr(message=section + " section not found.")

        sec = getattr(CONF, section)
        for op in options:
            if not hasattr(sec, op):
                raise UpdaterErr(message="%s.%s option not found." % (section, op))

            if op.endswith('_dir'):
                dir_path = getattr(sec, op)
                if not os.path.exists(dir_path):
                    try:
                        make_tmp_dir(dir_path)
                    except Exception as e:
                        raise UpdaterErr(message='make directory error: %s, reason: %s'
                                                 % (dir_path, e))
                if not os.path.isdir(dir_path):
                    raise UpdaterErr(message='%s=%s need to be a directory, pleace change etc/beta/dnsdb-updater.conf'
                                             % (op, dir_path))



def get_self_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def _dnsdb_resp_wrapper(resp, req):
    try:
        resp = resp.json()
    except Exception as ex:
        raise UpdaterErr(
            u'DnsdbApi request error: %s' % ex, 500, detail=dict(
                request=req, ex=str(ex), reason=resp.reason,
                status=resp.status_code),
            msg_ch=u'DnsdbApi调用失败')
    if int(resp.get('status', 200)) != 200 or resp.get('errcode', 0) != 0:
        raise UpdaterErr(u'DnsdbApi调用失败: %s' % json.dumps(resp), 400, json.dumps(resp))
    return resp


def get_group_name():
    return CONF.host_group


class DnsdbApi(object):
    api = Api(CONF.api.dnsdbapi_url, resp_wrapper=_dnsdb_resp_wrapper)

    @staticmethod
    def get_host_group():
        return DnsdbApi.api.get_form('/get/host_group',
                                     data={"host_ip": get_self_ip()})

    @staticmethod
    def update_host_md5(host_ip, named_conf_md5):
        return DnsdbApi.api.post_json('/update/host_conf_md5',
                                      data={"host_ip": host_ip,
                                            'host_conf_md5': named_conf_md5})

    @staticmethod
    def get_named_conf(group_name):
        return DnsdbApi.api.get_form('/get/named_conf',
                                     data={"group_name": group_name})

    @staticmethod
    def can_reload(group_name=None):
        if group_name is None:
            group_name = get_group_name()
        return DnsdbApi.api.get_form('/get/reload_status',
                                     data={'group_name': group_name})

    @staticmethod
    def get_acl_content(acl_file):
        return DnsdbApi.api.get_form('/get/acl_file',
                                     data={'acl_file': acl_file})

    @staticmethod
    def update_deploy_info(deploy_id, is_success, msg):
        return DnsdbApi.api.post_json('/update/deploy_info',
                                      data={'deploy_id': deploy_id,
                                            'host': CONF.host_ip,
                                            'is_success': is_success,
                                            'msg': msg})

    @staticmethod
    def get_update_zones(group_name):
        try:
            resp = DnsdbApi.api.get_form('/get/update_zones',
                                         data={'group_name': group_name})
            return resp['data']
        except Exception as e:
            log.error(e)
            return []

    @staticmethod
    def get_zone_info(zone):
        return DnsdbApi.api.get_form('/get/zone_info',
                                     data={"zone_name": zone})

    @staticmethod
    def update_zone_serial(zone):
        return DnsdbApi.api.post_json('/update/zone_serial', data={"zone_name": zone})


def make_dir(dst_dir):
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    elif not os.path.isdir(dst_dir):
        return False
    return True


def check_file_exists(filepath):
    if not os.path.exists(filepath):
        return False
    return True


def get_file_diff(src, dst):
    output, retcode = run_command_with_code("diff -u %s %s" % (src, dst), check_exit_code=False)
    if retcode is None or retcode == 0:
        return ''
    return output


def get_named_path():
    named_dir = CONF.bind_conf.named_dir
    return os.path.join(named_dir, 'named.conf')


def backup_file(file_type, file_path):
    dst_dir = os.path.join(CONF.etc.backup_dir, file_type)
    if not make_dir(dst_dir):
        log.error('Cannot make dir %s to backup %s' % (dst_dir, file_path))
    dst_file = '{}_{}'.format(file_path.split('/')[-1], datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f'))
    dst = os.path.join(dst_dir, dst_file)
    if os.system("cp -f %s %s >/dev/null 2>&1" % (file_path, dst)) != 0:
        log.error('Backup file %s failed' % file_path)
    log.info('Backup file %s success' % file_path)


def send_zone_diff_email(content):
    send_email('DNS_zone_edit from Dnsmaster %s' % CONF.host_group, content)


def send_alarm_email(content):
    send_email("[DNSDB-UPDATER alarm: %s]" % CONF.host_group, content, receivers=CONF.MAIL.alert_list)


def _make_tmp_zone_filepath(name):
    return os.path.join(CONF.etc.tmp_dir, 'var/named', name)


def make_zone_file(zone, filename, serial, header, record_list):
    try:
        with open(filename, 'w') as f:
            f.writelines(header)
        run_command_with_code('sed -i "s/pre_serial/%s/" %s' % (str(serial), filename))

        with open(filename, 'a') as f:
            for item in record_list:
                name = item["name"].replace("." + zone, "")
                record = item["record"]
                if item["type"] == 'CNAME':
                    record = record + "."
                ttl = 0
                if "ttl" in item:
                    ttl = int(item["ttl"])
                if ttl == 0:
                    f.write("%s \t IN \t %s \t %s\n" % (name, item["type"], record))
                else:
                    f.write("%s \t %d \t IN \t %s \t %s\n" % (name, int(ttl), item["type"], record))
    except Exception as e:
        log.error(e)
        raise UpdaterErr('Create zone file failed: %s' % e)


def make_zone_file_from_dnsdb(zone):
    zone_info = DnsdbApi.get_zone_info(zone)['data']
    serial = zone_info["serial_num"]
    record_list = zone_info["records"]
    header = zone_info['header']
    tmp_zonefile_path = _make_tmp_zone_filepath(zone)
    make_zone_file(zone, tmp_zonefile_path, serial, header, record_list)
    return tmp_zonefile_path


def is_file_changed_too_much(src, dst):
    output, retcode = run_command_with_code("diff %s %s" % (src, dst), check_exit_code=False)
    if retcode is None:
        log.error("CRITICAL, retcode is NONE.")
        return True
    if retcode == 0:
        log.info("diff reported that nothing has been changed.")
        return False
    counter = 0
    threshold = CONF.etc.threshold
    for buf in io.StringIO(output):
        counter = counter + 1
    if counter > threshold:
        log.info("Too many changes made to %s" % src)
        return True
    log.info("Changes to %s are acceptable." % src)
    return False


def _get_serial_from_zone_file(path):
    grep_ouput, exit_code = run_command_with_code("grep -i 'serial' %s" % path)
    pattern = re.match('^[^\d]*(\d*).*', grep_ouput)
    if pattern is None:
        raise UpdaterErr("Unable grep serial.")
    current_serial = pattern.group(1)
    log.info("Got serial %s from %s." % (current_serial, path))
    return current_serial


def is_need_update_zone(tmp_zonefile_path, current_zonefile_path):
    new_serial = _get_serial_from_zone_file(tmp_zonefile_path)
    current_serial = _get_serial_from_zone_file(current_zonefile_path)
    if int(new_serial) > int(current_serial):
        log.info("Current serial is %s, serial in request is %s, need update." % (current_serial, new_serial))
        return True
    log.info("Current serial is %s, serial in request is %s, need no update." % (current_serial, new_serial))
    return False


def make_debugfile_path(prog):
    return ''.join([CONF.etc.log_dir, "/", prog, ".log"])


def backup_debug_file(debug_file):
    error_log = debug_file + datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    shutil.copyfile(debug_file, error_log)
    return error_log


def checkzone(zone, zonefile_path):
    if CONF.etc.env == 'dev':
        return
    cmd = CONF.bind_conf.named_zonecheck
    debug_file = make_debugfile_path("named-checkzone")
    if os.system("%s -k fail %s %s >%s 2>&1" % (cmd, zone, zonefile_path, debug_file)) != 0:
        error_log = backup_debug_file(debug_file)
        raise UpdaterErr("zone syntax check did not return success for %s, see %s." % (zone, error_log))
    log.info("named-checkzone said %s is ok." % zone)


def send_changes_to_opsteam(src, dst):
    diff_content = get_file_diff(src, dst)
    if diff_content:
        send_zone_diff_email(diff_content)


def reload_and_backup_zones(zone_file_dict):
    for zone, file_info in zone_file_dict.items():
        if os.system("cp -f %s %s >/dev/null 2>&1" % (file_info['src'], file_info['dst'])) != 0:
            raise UpdaterErr("Failed to copy file: src: %s, dst: %s" % (file_info['src'], file_info['dst']))

        if CONF.etc.env != 'dev':
            rndc_debugfile = make_debugfile_path("rndc")
            if os.system("%s reload %s >%s 2>&1" % (CONF.bind_conf.rndc, zone, rndc_debugfile)) != 0:
                error_log = backup_debug_file(rndc_debugfile)
                raise UpdaterErr("Failed to reload:%s, see %s." % (zone, error_log))
        log.info("Reloaded %s." % zone)
        backup_file(zone, file_info['src'])
