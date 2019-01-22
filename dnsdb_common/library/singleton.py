# -*- coding: utf-8 -*-

class Singleton(object):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls.__instance, cls):
            cls.__instance = object.__new__(cls, *args, **kwargs)
            cls.__instance.init()
        return cls.__instance

    def init(self):
        pass


class MetaSingleton(type):
    def __init__(self, *args, **kwargs):
        self.__instance = None
        super(MetaSingleton, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super(MetaSingleton, self).__call__(*args, **kwargs)
        return self.__instance



