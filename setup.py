# -*- encoding: utf-8 -*-
from distutils.core import setup
import py2exe

options = {
    'py2exe':
    {'compressed': 1,
     'optimize': 2,
     'bundle_files': 1  #'optimize': 2,
     }
}
setup(
    version='0.0.4',
    description='DNSProxy',
    name='DNSProxy',
    options=options,
    zipfile=None,
    windows=[{'script': 'dns.py'}], )
