# -*- coding: utf-8 -*-

from __future__ import print_function
from dns_updater.utils.updater_util import *

TMP_DIR = CONF.etc.tmp_dir
ZONE_DIR = CONF.bind_conf.zone_dir


def _copy_named_files():
    zone_dir = ZONE_DIR
    tmp = os.path.join(TMP_DIR, 'var/named')
    make_dir(tmp)
    if os.system("cp -Rf %s/* %s/var/named/ >/dev/null 2>&1" % (zone_dir, TMP_DIR)) != 0:
        raise UpdaterErr("Failed to copy zone files to tmp_dir.")
    log.info("Copied named's files to %s.", TMP_DIR)

# Return the output from mkrdns which will be used extract all modified PTR zones.
def _build_PTR_records():
    debug_file = make_debugfile_path("mkrdns")
    if CONF.etc.env == 'dev':
        return debug_file
    if os.system("%s -rootdir %s %s >%s 2>&1" % (CONF.bind_conf.mkrdns,
                                                 TMP_DIR, get_named_path(), debug_file)) != 0:
        error_log = backup_debug_file(debug_file)
        raise UpdaterErr("mkrdns did not return success, see %s." % error_log)
    log.info("PTR zones has been built.")
    return debug_file


# Get all the PTR zones which should be reload.
def _get_modified_PTR_zones(mkrdns_output, zone_file_dict):
    pgrep = sp.Popen(split("grep 'Updating file' " + mkrdns_output), stdout=sp.PIPE, stderr=sp.PIPE)
    exit_code = pgrep.wait()
    if int(exit_code) != 0:
        log.info("No PTR zone needs to be reloaded.")
        return
    for buf in StringIO.StringIO(pgrep.communicate()[0]):
        ptn = re.match('^Updating file "(%s/var/named/[^"]*)".*' %
                       TMP_DIR, buf)
        if ptn is not None:
            zone_file = ptn.group(1)
            zone = zone_file.split('/')[-1]

            zonename = _build_zonename_for_PTR_zone(zone)
            zone_file_dict[zonename] = {
                'src': zone_file,
                'dst': os.path.join(ZONE_DIR, zone)
            }
            checkzone(zonename, zone_file)


def _build_zonename_for_PTR_zone(zone):
    tokens = zone.split(".")
    zonename = ""
    for j in range(len(tokens) - 2, -1, -1):
        zonename += tokens[j] + "."
    return zonename + "IN-ADDR.ARPA"


def handler():
    zone_list = DnsdbApi.get_update_zones(CONF.host_group)
    log.info('zones to update: %s' % zone_list)
    for name in zone_list:
        zone_file_dict = {}
        try:
            _copy_named_files()
            current_zonefile_path = os.path.join(ZONE_DIR, name)
            if not check_file_exists(current_zonefile_path):
                raise UpdaterErr('Zone file not exist: %s' % current_zonefile_path)

            tmp_zonefile_path = make_zone_file_from_dnsdb(name)
            if not is_need_update_zone(tmp_zonefile_path, current_zonefile_path):
                return
            checkzone(name, tmp_zonefile_path)
            zone_file_dict[name] = {
                'src': tmp_zonefile_path,
                'dst': current_zonefile_path
            }

            mkrdns_output = _build_PTR_records()
            _get_modified_PTR_zones(mkrdns_output, zone_file_dict)
            log.info('Update zones:\n %s' % json.dumps(zone_file_dict.keys(), indent=4))
            send_changes_to_opsteam(current_zonefile_path, tmp_zonefile_path)
            if DnsdbApi.can_reload():
                reload_and_backup_zones(zone_file_dict)
                DnsdbApi.update_zone_serial(name)
                log.info('update_zone_serial')
            return True
        except UpdaterErr as e:
            log.error(e.message)
        except Exception as e:
            log.exception(e)
