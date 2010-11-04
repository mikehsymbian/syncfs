#!/usr/bin/env python
from test import *
import os, sys
from errno import *
from stat import *
import fcntl
# pull in some spaghetti to make this stuff work without fuse-py being installed
try:
    import _find_fuse_parts
except ImportError:
    pass
import fuse
from fuse import Fuse

def log(msg):
    f = open('/tmp/mike.log','a+')
    f.write("%s\n" % msg)
    f.close()

if not hasattr(fuse, '__version__'):
    raise RuntimeError, \
        "your fuse-py doesn't know of fuse.__version__, probably it's too old."

fuse.fuse_python_api = (0, 2)

fuse.feature_assert('stateful_files', 'has_init')



def main():

    usage = """
Userspace nullfs-alike: mirror the filesystem tree from some point on.

""" + Fuse.fusage

    server = NullFS(version="%prog " + fuse.__version__,
                 usage=usage,
                 dash_s_do='setsingle')

    # Disable multithreading: if you want to use it, protect all method of
    # XmlFile class with locks, in order to prevent race conditions
    server.multithreaded = False

    server.parse(values=server, errex=1)
    print dir(server)

    server.main()


if __name__ == '__main__':
    main()
