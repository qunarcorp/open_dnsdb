# -*- coding: utf-8 -*-

BADREQUEST = 400
UNAUTHORIZED = 401
FORBIDDEN = 403
GONE = 410
TOOMANYREQUESTS = 412


class DnsdbException(Exception):
    def __init__(self, message, errcode=500, detail=None, msg_ch=u''):
        self.message = message
        self.errcode = errcode
        self.detail = detail
        self.msg_ch = msg_ch
        super(DnsdbException, self).__init__()

    def __str__(self):
        return self.message

    def json(self):
        return dict(code=self.errcode, why=self.message)


class Unauthorized(DnsdbException):
    def __init__(self, message='Unauthorized', errcode=UNAUTHORIZED, detail=None, msg_ch=u''):
        super(Unauthorized, self).__init__(message, errcode, detail, msg_ch)

class Forbidden(DnsdbException):
    def __init__(self, message='Forbidden', errcode=FORBIDDEN, detail=None, msg_ch=u''):
        super(Forbidden, self).__init__(message, errcode, detail, msg_ch)


class OperationLogErr(DnsdbException):
    def __init__(self, message, errcode=500, detail=None, msg_ch=u''):
        super(OperationLogErr, self).__init__(message, errcode, detail, msg_ch)


class BadParam(DnsdbException):
    def __init__(self, message='Bad params', errcode=BADREQUEST, detail=None, msg_ch=u''):
        super(BadParam, self).__init__(message, errcode, detail, msg_ch)


class UpdaterErr(DnsdbException):
    pass


class ConfigErr(UpdaterErr):
    def __init__(self, message):
        super(ConfigErr, self).__init__(message=message, errcode=501)
