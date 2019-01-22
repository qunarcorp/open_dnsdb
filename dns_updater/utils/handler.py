# -*- coding: utf-8 -*-

from dns_updater.utils.updater_util import DnsdbApi
from dnsdb_common.library.log import getLogger
from dns_updater.utils.updater_util import send_alarm_email
log = getLogger(__name__)

from dns_updater.utils.tool_classes import GenericWorker


class WatchZone(GenericWorker):
    def __init__(self, interval, queue_name):
        super(WatchZone, self).__init__(interval)
        self.queue_name = queue_name
        # todo 根据queue获取handle
        self.zone_handler = lambda x: x

    def handler(self):
        log.info('%s worker start' % self.queue_name)
        try:
            zones = DnsdbApi.get_update_zones(self.queue_name)
            if zones:
                self.zone_handler(zones)
        except Exception as e:
            log.exception(e)
            send_alarm_email(u"[CRITICAL] Failed to handle zone update of %s, because: %s" %
                             (self.queue_name, e.message))

