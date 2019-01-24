# -*- coding: utf-8 -*-

import re

try:
    basestring
except NameError:
    basestring = (str, )

def _match_pattern(pattern, string):
    ptn = re.search(r'(%s)' % pattern, string)
    if ptn is None:
        return False
    if len(ptn.groups()) == 0:
        return False
    return ptn.group(1) == string


def valid_string(s, min_len=None, max_len=None,
                 allow_blank=False, auto_trim=True, pattern=None):
    """
        @param s str/unicode 要校验的字符串
        @param min_len None/int
        @param max_len None/int
        @param allow_blank boolean
        @param auto_trim boolean
        @:param pattern re.pattern
        @return boolean is_ok
        @return string/int value 若是ok，返回int值，否则返回错误信息
    """
    if s is None:
        return False, u'不能为None'
    if not isinstance(s, basestring):
        return False, u"参数类型需要是字符串"
    if auto_trim:
        s = s.strip()
    str_len = len(s)
    if not allow_blank and str_len < 1:
        return False, u"参数不允许为空"
    if max_len is not None and str_len > max_len:
        return False, u"参数长度需小于%d" % max_len
    if min_len is not None and str_len < min_len:
        return False, u"参数长度需大于 %d" % min_len
    if pattern is not None and s and not _match_pattern(pattern, s):
        return False, u'参数包含的字符: %s' % pattern
    return True, s


def valid_int(s, min_value=None, max_value=None):
    """\
@param s str/unicode 要校验的字符串
@param min_value None/int
@param max_value None/int
@return boolean is_ok
@return string/int value 若是ok，返回int值，否则返回错误信息
    """
    if s is None:
        return False, "cannot is None"
    if not isinstance(s, basestring):
        return False, "must a string value"
    s = int(s)
    if max_value is not None and s > max_value:
        return False, "%d must less than %d" % (s, max_value)
    if min_value is not None and s < min_value:
        return False, "%d must greater than %d" % (s, min_value)
    return True, s
