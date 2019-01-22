# -*- coding: utf-8 -*-

import sqlite3
from oslo.config import cfg

from ..library import exception as err
from ..library.log import log

CONF = cfg.CONF


class SqliteDatabase(object):
    def __init__(self):
        self.data = CONF.database.data

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.data)
            self.cur = self.conn.cursor()
            return True
        except Exception as e:
            log.error("Unable to connect to db: %s" % (e))
            return False

    def execute_sql(self, sql):
        try:
            self.cur.execute(sql)
            return True
        except Exception as e:
            log.error("Failed to execute sql: %s" % (e))
            return False

    def fetchall(self):
        try:
            result = self.cur.fetchall()
            return True, result
        except Exception as e:
            log.error("Failed to fetchall: %s" % (e))
            return False, None

    def insert(self, sql):
        try:
            self.cur.execute(sql)
            return err.ENONE
        except sqlite3.IntegrityError as e:
            log.error("Failed to execute sql: %s" % e)
            return err.ECONFLICT
        except Exception as e:
            log.error("Failed to execute sql: %s" % e)
            return err.EDBGONE

    def execute_and_fetch(self, sql, *args, **kargs):
        try:
            self.cur.execute(sql, *args, **kargs)
            result = self.cur.fetchall()
            return True, result
        except Exception as e:
            log.error("Failed to execute_and_fetch sql: %s" % e)
            return False, None

    def execute_and_get_count(self, sql, *args, **kargs):
        try:
            self.cur.execute(sql, *args, **kargs)
            result = self.cur.rowcount
            return True, result
        except Exception as e:
            log.error("Failed to execute_and_get_count sql: %s" % (e))
            return False, None

    def commit(self):
        self.conn.commit()

    def commit_and_close(self):
        self.conn.commit()
        self.conn.close()

    def rollback(self):
        self.conn.rollback()

    def rollback_and_close(self):
        self.conn.rollback()
        self.conn.close()

    def get_rowcount(self):
        return self.cur.rowcount

    def close(self):
        self.conn.close()


def get_db_connection():
    db = SqliteDatabase()
    if not db.connect():
        return None
    return db
