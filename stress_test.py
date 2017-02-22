#encoding:utf8
from multiprocessing import Pool
import subprocess
import os
FNULL = open(os.devnull, 'w')

def call_dig(addr):
    subprocess.call(["dig", "@127.0.0.1", "-p", "5300", addr], stdout=FNULL)

with open("website_addr", "r") as fin:
    all_address = fin.readlines()
    pool = Pool(4)
    pool.map(call_dig, all_address)
    pool.close()
    pool.join()
