#!/usr/bin/env python
from comms import *
import hashlib
import socket
import threading
import SocketServer
import os
import time 
from fs import SyncFS
import sys
import time
from util import log

from fuse import FUSE
argv = sys.argv


if len(argv) < 4:
    print 'usage: %s <root> <mountpoint> <servers>' % argv[0]
    exit(1)

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        directive = self.request.recv(1024).strip()
        type = directive.split(" ")[0]
        filename = " ".join(directive.split(" ")[1:])
        self.request.send('OK\n')
        if type == "file":
            manager.process_incoming_file(self.request, filename)
        if type == "symlink":
            manager.process_incoming_symlink(self.request, filename)
        if type == "delete":
            manager.process_incoming_delete(self.request, filename)
        if type == "directory":
            manager.process_incoming_directory(self.request, filename)
        if type == "announce":
            manager.process_incoming_announce(self.request)
        if type == "rename":
            manager.process_incoming_rename(self.request, filename)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass



this_host = os.uname()[1]

while 1:
    try:
        HOST, PORT = '', 11899
        server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)

        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.setDaemon(True)
        server_thread.start()
        servers = argv[3:]
        if this_host in servers:
            servers.remove(os.uname()[1])
        manager = Manager(11899, servers)
        manager.process_outgoing_announce()
        fuse = FUSE(SyncFS(argv[1], manager), argv[2], foreground=True)
        server.shutdown()
        break
    except:
        type = sys.exc_info()[1]
        message = sys.exc_info()[0]
        print "%s %s" % (type, message)
        log("FATAL ERROR: %s %s" % (type, message))
        log("Restarting...")
        server.shutdown()
        time.sleep(2)

