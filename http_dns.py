# -*- encoding: utf-8 -*-
import gevent.monkey
gevent.monkey.patch_all()
import struct
import logging
import urllib2
import socket

import cache
from cache import unpack_name
from common import AUTHORIZED_DNS_SERVER, TIMEOUT, REMOTE_TCP_DNS_PORT

logger = logging.getLogger('http_dns')


def pack_dns_header(_id, QR, Opcode, AA, TC, RD, RA, Z, RCODE, QDCOUNT,
                    ANCOUNT, NSCOUNT, ARCOUNT):
    QR = QR << 15
    Opcode = Opcode << 11
    AA = AA << 10
    TC = TC << 9
    RD = RD << 8
    RA = RA << 7
    Z = Z << 4
    header_id = struct.pack(">h", _id)
    header_operator_num = QR | Opcode | AA | TC | RD | RA | Z | RCODE
    header_operator = struct.pack(">H", header_operator_num)
    QDCOUNT = struct.pack(">h", QDCOUNT)
    ANCOUNT = struct.pack(">h", ANCOUNT)
    NSCOUNT = struct.pack(">h", NSCOUNT)
    ARCOUNT = struct.pack(">h", ARCOUNT)
    return header_id + header_operator + QDCOUNT + ANCOUNT + NSCOUNT + ARCOUNT


def unpack_dns_header(rawstr):
    ID_SIZE = 2
    HEADER_SIZE = 2
    COUNT_FIELD_SIZE = 2 * 4
    start = 0
    _id = struct.unpack(">h", rawstr[start:start + ID_SIZE])[0]
    start += ID_SIZE
    header_operator = struct.unpack(">h", rawstr[start:start + HEADER_SIZE])[0]
    start += HEADER_SIZE
    QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT = struct.unpack(
        ">hhhh", rawstr[start:start + COUNT_FIELD_SIZE])
    start += COUNT_FIELD_SIZE
    QR = (header_operator & 1 << 15) >> 15
    Opcode = (header_operator & 0b1111 << 11) >> 11
    AA = (header_operator & 1 << 10) >> 10
    TC = (header_operator & 1 << 9) >> 9
    RD = (header_operator & 1 << 8) >> 8
    RA = (header_operator & 1 << 7) >> 7
    Z = (header_operator & 0b111 << 4) >> 4
    RCODE = header_operator & 0b1111
    return {
            "id" : _id,
            "QDCOUNT" : QDCOUNT,
            "ANCOUNT" : ANCOUNT,
            "NSCOUNT" : NSCOUNT,
            "ARCOUNT" : ARCOUNT,
            "header":dict(QR=QR,Opcode = Opcode, AA=AA,TC=TC,RD=RD,RA=RA,Z=Z,RCODE=RCODE),
        }, start  # yapf: disable

def httpdns_request(domain_name):
    resp = urllib2.urlopen("http://119.29.29.29/d?dn=" + domain_name).read()
    resp = resp.split(";")
    return resp


def construct_resp_header(dns_header, resp_len):
    kwparas = dict(
        _id=dns_header["id"],
        QR=1,  #this is response
        Opcode=0,  #standard query
        AA=0,  # not an authority for domain
        TC=0,  # no truncated
        RD=dns_header["header"]["RD"],  # recursion desire
        RA=1,  # server can do recursive look up
        Z=0,  # reserved
        RCODE=0,  #no error 
        QDCOUNT=dns_header["QDCOUNT"],
        ANCOUNT=resp_len,
        ARCOUNT=0,
        NSCOUNT=0, )
    return pack_dns_header(**kwparas)


def pack_a_record(name_offset, ip):
    if len(ip) == 0:
        return ""
    pointer_mark = 0b11 << (2 + 4 * 3)
    pointer = struct.pack("!H", pointer_mark | name_offset)
    record_type = struct.pack("!H", 1)  #type A, host address
    record_class = struct.pack("!H", 1)  #class IN, internet
    ttl = struct.pack("!I", 60)
    data_length = struct.pack("!H", 4)
    packed_ip = socket.inet_aton(ip)
    return pointer + record_type + record_class + ttl + data_length + packed_ip


class HttpDnsHandle(object):
    @cache.memorized_domain
    def http_response(self, dns_req):
        logger.debug("req :%s", dns_req.encode("hex"))
        dns_header, dlen = unpack_dns_header(dns_req)
        name_start = dlen
        labels, name_end = unpack_name(dns_req, name_start)
        domain_name = '.'.join(labels)
        resp = httpdns_request(domain_name)
        logger.debug("ips:%s", str(resp))
        resp_header = construct_resp_header(dns_header, len(resp))
        QTYPE_SIZE = 2
        QCLASS_SIZE = 2
        queries = dns_req[name_start:name_end + QTYPE_SIZE + QCLASS_SIZE]
        records = ''.join([pack_a_record(name_start, r) for r in resp])
        dns_resp = resp_header + queries + records
        logger.debug("resp:%s", dns_resp.encode("hex"))
        return dns_resp


def test_http_dns():
    result = "038b818000010001000000000377777706616d617a6f6e03636f6d00c00c000100010000003c0004b02067cd".decode(
        "hex")
    with open("dns_req", "r") as fin:
        dns_req = fin.read()
        h = HttpDnsHandle()
        dns_resp = h.http_response(dns_req)
    assert (dns_resp == result)


if __name__ == "__main__":
    test_http_dns()
