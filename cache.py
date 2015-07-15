# -*- encoding: utf-8 -*-
import time
import logging
import functools
from common import DEF_CACHE
from common import DEF_CACHE_TTL
import struct

logger = logging.getLogger("cache")

class memorized(object):
    """ 带超时控制的缓存类 """ 
    def __init__(self, func):
        self.func = func
        self.cache_name = "_cache_" + func.func_name
        self.cache = {}
        self.ttl = DEF_CACHE_TTL
        if DEF_CACHE:
          self.__call__ = self.cache_call
        else:
          self.__call__ = self.func

    def __get__(self, obj, cls=None):
        return functools.partial(self.__call__, obj)

    def cache_call(self, *args):
        pass

def unpack_name(rawstring, offset):
    labels = []
    i = offset
    while True:
        label_length = struct.unpack(">B", rawstring[i])[0]
        if label_length >= 192: #this is pointer
            label_length = struct.unpack(">H", rawstring[i:i+2])[0]
            pointer_offset = label_length & 0x3fff
            labels, _ = unpack_name(rawstring, pointer_offset)
            return labels, i + 2
        else:
            i = i + 1
        label = struct.unpack("%ds" %label_length, rawstring[i:i+label_length])[0]
        labels.append(label)
        i = i + label_length
        if rawstring[i] == chr(0):
            break
    i += 1
    return labels, i

class memorized_domain(memorized):
    def cache_call(self, obj, raw_data):
        cache = self.cache.get(self.cache_name, {})
        logger.debug(cache)
        now = time.time()
        url = self.extract_url(raw_data)
        try:
            value, last_update = cache[url]
            value = raw_data[0:2] + value[2:]
            logger.debug("hit cache")
            if now - last_update > self.ttl:
                raise AttributeError
        except (KeyError, AttributeError):
            logger.debug("miss cache")
            value = self.func(obj, raw_data)
            cache[url] = (value, now)
            self.cache[self.cache_name] = cache
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
        labels, offset = unpack_name(data, 0)
        url = ".".join(labels)
        logger.debug("requesting url:%s", url)
        return url

