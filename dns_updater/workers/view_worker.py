# -*- coding: utf-8 -*-

import datetime

from dns_updater.utils.updater_util import *

CONF = cfg.CONF

TMP_DIR = CONF.etc.tmp_dir
ZONE_DIR = CONF.bind_conf.zone_dir


def _make_zone_file_from_dnsdb(zone):
    zone_info = DnsdbApi.get_zone_info(zone)['data']
    serial = zone_info["serial_num"]
    record_dict = zone_info["records"]
    header = zone_info['header']

    isp_file_dict = {}
    for isp,  record_list in record_dict.items():
        tmp_dir = os.path.join(CONF.etc.tmp_dir, 'var/named', isp)
        make_dir(tmp_dir)
        tmp_zonefile_path = os.path.join(tmp_dir, zone)
        make_zone_file(zone, tmp_zonefile_path, serial, header, record_list)
        checkzone(zone, tmp_zonefile_path)
        isp_file_dict[isp] = {
            'src': tmp_zonefile_path,
            'dst': os.path.join(ZONE_DIR, isp, zone)
        }
        make_dir(os.path.join(ZONE_DIR, isp))
    return isp_file_dict


def _backup_debug_file(debug_file):
    error_log = debug_file + datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    shutil.copyfile(debug_file, error_log)
    return error_log


def _copy_and_reload(isp_file_dict, zone):
    for isp, file_info in isp_file_dict.items():
        if os.system("cp -f %s %s >/dev/null 2>&1" % (file_info['src'], file_info['dst'])) != 0:
            raise UpdaterErr("Failed to copy file: src: %s, dst: %s" % (file_info['src'], file_info['dst']))
        backup_file(isp, file_info['src'])

    if CONF.etc.env != 'dev':
        rndc_debugfile = make_debugfile_path("rndc")
        if os.system("%s reload >%s 2>&1" % (CONF.bind_conf.rndc, rndc_debugfile)) != 0:
            error_log = backup_debug_file(rndc_debugfile)
            raise UpdaterErr("Failed to reload:%s, see %s." % (zone, error_log))
    log.info("Reloaded %s." % zone)
    return True


def _send_all_changes_to_opsteam(isp_file_dict):
    diff_content = ''
    for isp, files in isp_file_dict.items():
        diff = get_file_diff(files['dst'], files['src'])
        if diff:
            diff_content += diff + "\n"*3

    send_zone_diff_email(diff_content)


def handler():
    zone_list = DnsdbApi.get_update_zones(CONF.host_group)
    for zone_name in zone_list:
        try:
            isp_file_dict = _make_zone_file_from_dnsdb(zone_name)
            _send_all_changes_to_opsteam(isp_file_dict)
            if DnsdbApi.can_reload():
                _copy_and_reload(isp_file_dict, zone_name)
                DnsdbApi.update_zone_serial(zone_name)
        except Exception as e:
            log.exception(e)
            send_alarm_email(u'zone %s 更新失败\n原因: %s' % (zone_name, e))
