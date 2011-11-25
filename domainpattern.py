#!/usr/bin/env python
#-*- coding:utf8 -*-
import re

re_program = []
with open('pattern', 'r') as fh:
    lines = fh.readlines()
for line in lines:
    line = line.strip()
    re_program.append(re.compile(line, re.I))

def is_match(url):
    for program in re_program:
        if program.search(line):
            #logger.debug
            return program.pattern
    return None

def match_test():
    global re_program
    with open('testinput', 'r') as fh:
        lines = fh.readlines()
    for line in lines:
        flag = False
        line = line.strip()
        print line,
        if is_match(line):
            print "match:", program.pattern
              flag = True
        if not flag:
            print "doesn't match"

if __name__ == '__main__':
    match_test()
