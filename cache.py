# -*- encoding: utf-8 -*-
import time
import logging
import functools
from common import DEF_CACHE
from common import DEF_CACHE_TTL

logger = logging.getLogger("cache")

class memorized(object):
    """ 带超时控制的缓存类 """ 
    def __init__(self, func):
        self.func = func
        self.cache_name = "_cache_" + func.func_name
        self.ttl = DEF_CACHE_TTL
        if DEF_CACHE:
          self.__call__ = self.cache_call
        else:
          self.__call__ = self.func

    def __get__(self, obj, cls=None):
        return functools.partial(self.__call__, obj)

    def cache_call(self, *args):
        pass

class memorized_domain(memorized):
    def cache_call(self, obj, raw_data):
        cache = obj.__dict__.setdefault(self.cache_name, {})
        now = time.time()
        url = self.extract_url(raw_data)
        try:
            value, last_update = cache[url]
            if now - last_update > self.ttl:
                raise AttributeError
        except (KeyError, AttributeError):
            value = self.func(obj, raw_data)
            cache[url] = (value, now)
        return value

    def extract_url(self, data):
        logger.debug("raw dns request:%s", data.encode('hex'))
        #pass 12 bytes
        data = data[12:]
        #extract the url
        url = []
        start = 0
        len_of_data = ord(data[start])
        logger.debug("len of data:%s", len_of_data)
        while len_of_data != 0:
            part = str(data[start + 1:start + 1 + len_of_data])
            logger.debug("part:%s", part)
            url.append(part)
            start = start + len_of_data + 1
            len_of_data = ord(data[start])
        url = '.'.join(url)
        logger.debug("requesting url:%s", url)
        return url

