#!/usr/bin/env python

from __future__ import with_statement

from errno import EACCES
from os.path import realpath
from sys import argv, exit
from threading import Lock
from util import log
import os

from fuse import FUSE, FuseOSError, Operations


class SyncFS(Operations):    
    def __init__(self, root, manager):
        self.root = realpath(root)
        self.rwlock = Lock()
        self.fd_info = {}
        self.manager = manager

    def __call__(self, op, path, *args):
        return super(SyncFS, self).__call__(op, self.root + path, *args)
    
    def access(self, path, mode):
        #log("access %s %d" % (path, mode))
        if not os.access(path, mode):
            raise FuseOSError(EACCES)

    chmod = os.chmod
    chown = os.chown
    
    def create(self, path, mode):
        #log("create %s %d" % (path, mode))
        file = os.open(path, os.O_WRONLY | os.O_CREAT, mode)
        self.fd_info[file] = True
        return file
    
    def flush(self, path, fh):
        #log("flush %s %d" % (path, fh))
        return os.fsync(fh)

    def fsync(self, path, datasync, fh):
        #log("fsync %s %d" % (path, fh))
        return os.fsync(fh)
                
    def getattr(self, path, fh=None):
        st = os.lstat(path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
            'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
    
    getxattr = None
    
    def link(self, target, source):
        return os.link(source, target)
    
    listxattr = None
    def mkdir(self, path, mode=0777):
        self.manager.process_outgoing_directory(path, mode)
        return os.mkdir(path, mode)

    mknod = os.mknod

    def open(self, path, mode):
        #log("open %s %d" % (path, mode))
        return os.open(path, mode)

    def read(self, path, size, offset, fh):
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.read(fh, size)
    
    def readdir(self, path, fh):
        return ['.', '..'] + os.listdir(path)

    readlink = os.readlink
    
    def release(self, path, fh):
        #log("release %s %d" % (path, fh))
        if self.fd_info.has_key(fh) and self.fd_info[fh]:
            #log("%s was written to" % path)
            written_to = True
            del(self.fd_info[fh])
        else:
            #log("%s was not written to" % path)
            written_to = False
        res = os.close(fh)
        if written_to:
            self.manager.process_outgoing_file(path)
        return res

    def rename(self, old, new):
        self.manager.process_outgoing_rename(old, self.root + new)
        return os.rename(old, self.root + new)
    
    def rmdir(self, path):
        self.manager.process_outgoing_delete(path)
        return os.rmdir(path)
    
    def statfs(self, path):
        stv = os.statvfs(path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))
    
    def symlink(self, link_name, target):
        #print "symlink %s %s" % (link_name, target)
        self.manager.process_outgoing_symlink(target, link_name)
        return os.symlink(target, link_name)
    
    def truncate(self, path, length, fh=None):
        #log("truncate %s" % path)
        with open(path, 'r+') as f:
            f.truncate(length)
            if length > 0:
                self.manager.process_outgoing_file(path)

    def unlink(self, path):
        os.unlink(path)
        self.manager.process_outgoing_delete(path)

    utimens = os.utime
    
    def write(self, path, data, offset, fh):
        #log("write %s %s" % (path, data))
        if data:
            self.fd_info[fh] = True
        with self.rwlock:
            os.lseek(fh, offset, 0)
            return os.write(fh, data)
    
