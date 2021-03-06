# -*- encoding: utf-8 -*-
import struct
import socket
import logging
import Queue
import errno

import cache
from common import AUTHORIZED_DNS_SERVER, TIMEOUT, REMOTE_TCP_DNS_PORT, TCP_QUEUE_SIZE

logger = logging.getLogger('tcp_dns')


class TCP_Handle(object):
    @cache.memorized_domain
    def tcp_response(self, data):
        """ tcp request dns data """
        if not hasattr(self, "tcp_pool"):
            self.tcp_pool = Queue.Queue(maxsize=TCP_QUEUE_SIZE)
        resp = None
        sock = self.get_tcp_sock()
        size_data = self.tcp_packet_head(data)
        packet = size_data + data
        while not resp:
            try:
                sock.send(packet)
                resp = sock.recv(1024)
                logger.debug("receive data:[%d]%s",
                             len(resp), resp.encode('hex'))
            except socket.timeout:
                logger.error("tcp socket timeout, throw away")
                self.drop_tcp_sock(sock)
                sock = self.get_tcp_sock()
            except IOError, e:
                if e.errno == errno.EPIPE:
                    logger.error("tcp socket broken pipe, throw away")
                    self.drop_tcp_sock(sock)
                    sock = self.get_tcp_sock()
                else:
                    raise e
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
            logger.debug("tcp pool size:%d", self.tcp_pool.qsize())
            sock = self.tcp_pool.get(block=False)
        except Queue.Empty:
            logger.debug("tcp pool is empty, now create a new socket")
            sock = self.create_tcp_sock()
        return sock

    def drop_tcp_sock(self, sock):
        logger.debug("close timeout sock")
        sock.close()

    def release_tcp_sock(self, sock):
        try:
            self.tcp_pool.put(sock, block=False)
        except Queue.Full:
            logger.debug("tcp pool is full, now throw away the oldest socket")
            old_sock = self.tcp_pool.get(block=False)
            old_sock.close()
            logger.debug("close old sock")
            self.tcp_pool.put(sock, block=False)

    def create_tcp_sock(self):
        logger.debug("create sock")
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((AUTHORIZED_DNS_SERVER, REMOTE_TCP_DNS_PORT))
        tcp_sock.settimeout(TIMEOUT)
        return tcp_sock
