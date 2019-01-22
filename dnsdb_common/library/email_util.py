# -*- coding: utf-8 -*-

import smtplib
from email.header import Header
from email.mime.text import MIMEText

from oslo.config import cfg

from ..library.log import getLogger
log = getLogger(__name__)

CONF = cfg.CONF


def send_email(subject, content, sender=None, receivers=None):
    if content is None:
        content = ""
    msg = MIMEText(content, 'plain', 'utf-8')
    if sender is None:
        sender = CONF.MAIL.from_addr
    elif isinstance(sender, (str, unicode)):
        raise TypeError('sender should be str type.')
    if receivers is None:
        receivers = CONF.MAIL.info_list
    elif isinstance(receivers, (str, unicode)):
        raise TypeError('Receivers should be str type.')
    to_list = receivers.split(';')

    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = Header(sender, 'utf-8')
    msg['To'] = Header(receivers, 'utf-8')
    s = smtplib.SMTP()
    try:
        s.connect(CONF.MAIL.server, CONF.MAIL.port)
        s.sendmail(sender, to_list, msg.as_string())
    except Exception, e:
        log.error("Failed to send email:%s, because: %s" % (msg, e.message))
    finally:
        s.close()


def send_alert_email(content, sender=None):
    receivers = CONF.MAIL.alert_list
    print receivers
    subject = "[DNSDB alarm]"
    send_email(subject, content, sender, receivers)

