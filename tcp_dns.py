# -*- encoding: utf-8 -*-
import struct
import socket
import logging
import Queue

import cache
from common import DEF_REMOTE_SERVER, DEF_PORT, DEF_TIMEOUT

logger = logging.getLogger('tcp_dns')

tcp_pool = Queue.Queue()
class TCP_Handle(object):
    def extract_url(self, data):
        logger.debug("raw dns request:%s", data.encode('hex'))
        #pass 12 bytes
        data = data[12:]
        #extract the url
        url = []
        start = 0
        len = ord(data[start])
        print "len:", len
        while len != 0:
            part = str(data[start + 1:start + 1 + len])
            print part
            url.append(part)
            start = start + len + 1
            len = ord(data[start])
        url = '.'.join(url)
        logger.debug("requesting url:%s", url)
        return url

    @cache.memorized_domain
    def tcp_response(self, data):
        """ tcp request dns data """        
        resp = None
        while not resp:
          sock = self.get_tcp_sock()
          size_data = self.tcp_packet_head(data)
          sock.send(size_data + data)
          try:
            resp = sock.recv(1024)
            logger.debug("receive data:%s", resp.encode('hex'))
          except socket.timeout:
            logger.debug("tcp socket timeout, throw away")
            sock = self.create_tcp_sock()
        self.release_tcp_sock(sock)
        return self.packet_body(resp)

    def tcp_packet_head(self, data):
        size = len(data)
        size_data = struct.pack('!H', size)
        logger.debug("head data len: %d", size)
        logger.debug("head data: %s", size_data.encode('hex'))
        return size_data

    def packet_body(self, data):
        size = struct.unpack('!H', data[0:2])[0]
        logger.debug("response package size: %d", size)
        logger.debug("len of response: %d", len(data))
        return data[2:2 + size]

    def get_tcp_sock(self):
        try:
          sock = tcp_pool.get(block=True, timeout=DEF_TIMEOUT)
        except Queue.Empty:
          logger.debug("tcp pool is empty, now create a new socket")
          sock = self.create_tcp_sock()
        return sock
    
    def release_tcp_sock(self, sock):
        try:
          tcp_pool.put(sock, block=False)
        except Queue.Full:
          logger.debug("tcp pool is full, now throw away the oldest socket")
          old_sock = tcp_pool.get(block=False)
          old_sock.close()
          tcp_pool.put(sock, block=False)

    def create_tcp_sock(self):
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((self.tcp_dns_server, DEF_PORT))
        tcp_sock.settimeout(5)
        return tcp_sock

