#!/usr/bin/env python
#-*- coding:utf8 -*-
import re
import logging

logger = logging.getLogger("pattern")
re_program = []
with open('pattern', 'r') as fh:
    lines = fh.readlines()
for line in lines:
    line = line.strip()
    re_program.append(re.compile(line, re.I))

def is_match(url):
    global re_program
    for program in re_program:
        if program.search(url):
            logger.debug("match pattern:%s", program.pattern)
            return program.pattern
    return None

def match_test():
    global re_program
    with open('testinput.txt', 'r') as fh:
        lines = fh.readlines()
    for line in lines:
        flag = False
        line = line.strip()
        print line,
        result = is_match(line)
        if result:
            print "match:", result
            flag = True
        if not flag:
            print "doesn't match"

if __name__ == '__main__':
    match_test()
