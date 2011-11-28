# -*- encoding: utf-8 -*-
import time
from common import DEF_CACHE
from common import DEF_CACHE_TTL

class memorized(object):
    """ 带超时控制的缓存类 """ 
    def __init__(self, func):
        self.func = func
        self.cache_name = "_cache_" + func.func_name
        self.ttl = DEF_CACHE_TTL
        if DEF_CACHE:
            self.call = self.cache_call
        else:
            self.call = self.func

    def __get__(self, instance, cls=None):
        self.instance = instance
        return self
    
    def __call__(self, *args):
        self.call(*args)

    def cache_call(self, *args):
        pass

class memorized_domain(memorized):
    def cache_call(self, raw_data, url):
        cache = self.instance.__dict__.setdefault(self.cache_name, {})
        now = time.time()
        try:
            value, last_update = cache[url]
            if now - last_update > self.ttl:
                raise AttributeError
        except (KeyError, AttributeError):
            value = self.func(self.instance, raw_data, url)
            cache[url] = (value, now)
        return value
