from util import log
import socket
import os
import errno

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise

class Delivery(object):
    # This works, and is very bad in the sense that there's a lot of repeated code. I know, I know!
    def deliver_file(self, filename, destinations, port):
        for destination in destinations:
            log('Delivering %s to %s' % (filename, destination))
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((destination, port))
                sock.send("file %s" % filename)
                sock.recv(3)
                sock.send('%s' % os.path.getsize(filename))
                sock.recv(3)
                f = open(filename)
                sock.send(f.read())
                f.close()
                sock.close()
            except socket.error:
                log('Bad news, everyone! There was an error connecting to %s' % destination)

    def deliver_symlink(self, target, link_name, destinations, port):
        for destination in destinations:
            log('Delivering %s to %s' % (target, destination))
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((destination, port))
                sock.send("symlink %s" % target)
                sock.recv(3)
                sock.send('%s' % link_name)
                sock.recv(3)
                sock.close()
            except socket.error:
                log('Bad news, everyone! There was an error connecting to %s' % destination)

    def deliver_rename(self, target, new_name, destinations, port):
        for destination in destinations:
            log('Delivering %s to %s' % (target, destination))
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((destination, port))
                sock.send("rename %s" % target)
                sock.recv(3)
                sock.send('%s' % new_name)
                sock.recv(3)
                sock.close()
            except socket.error:
                log('Bad news, everyone! There was an error connecting to %s' % destination)

    def deliver_directory(self, path, mode, destinations, port):
        for destination in destinations:
            log('Delivering %s to %s' % (path, destination))
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((destination, port))
                sock.send("directory %s" % path)
                sock.recv(3)
                sock.send(oct(mode))
                sock.recv(3)
                sock.close()
            except socket.error:
                log('Bad news, everyone! There was an error connecting to %s' % destination)

    def deliver_delete(self, filename, destinations, port):
        for destination in destinations:
            log('Deleting %s at %s' % (filename, destination))
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((destination, port))
                sock.send("delete %s" % filename)
                sock.recv(3)
                sock.send('confirming delete')
                sock.recv(3)
                sock.close()
            except socket.error:
                log('Bad news, everyone! There was an error connecting to %s' % destination)

    def deliver_announce(self, destinations, port):
        for destination in destinations:
            log('Announcing to %s' % destination)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((destination, port))
                sock.send("announce %s" % os.uname()[1])
                sock.recv(3)
                sock.close()
            except socket.error:
                log('Bad news, everyone! There was an error connecting to %s' % destination)


class Manager(object):

    def __init__(self, port, destinations):
        self.port = port
        self.destinations = destinations

    def process_outgoing_file(self, package):
        log('Sending out %s' % package)
        d = Delivery()
        d.deliver_file(package, self.destinations, self.port)

    def process_outgoing_symlink(self, target, link_name):
        log('Sending out symlunk %s' % target)
        d = Delivery()
        d.deliver_symlink(target, link_name, self.destinations, self.port)

    def process_outgoing_rename(self, target, new_name):
        log('Sending out rename %s to %s' % (target, new_name))
        d = Delivery()
        d.deliver_rename(target, new_name, self.destinations, self.port)

    def process_outgoing_announce(self):
        log('Sending out announcement')
        d = Delivery()
        d.deliver_announce(self.destinations, self.port)

    def process_outgoing_directory(self, path, mode):
        log('Sending out directory %s' % path)
        d = Delivery()
        d.deliver_directory(path, mode, self.destinations, self.port)

    def process_outgoing_delete(self, filename):
        log('Sending out delete %s' % filename)
        d = Delivery()
        d.deliver_delete(filename, self.destinations, self.port)

    def process_incoming_file(self, request, filename):
        log('Incoming file : %s' % filename)
        if not os.path.exists(os.path.dirname(filename)):
          mkdir_p(os.path.dirname(filename))
        size = int(request.recv(1024))
        request.send("OK\n")
        f = open(filename,'w')
        while 1:
            data = request.recv(1024*4)
            if not data:
                break
            f.write(data)
        f.close()
        request.send("OK\n")


    def process_incoming_directory(self, request, path):
        log('Incoming directory : %s' % path)
        if not os.path.exists(path):
          mkdir_p(path)
        mode = request.recv(1024)
        request.send("OK\n")


    def process_incoming_symlink(self, request, target):
        log('Incoming symlink : %s' % target)
        link_name = request.recv(1024).strip()
        request.send("OK\n")
        os.symlink(target, link_name)

    def process_incoming_rename(self, request, target):
        log('Incoming rename : %s' % target)
        new_name = request.recv(1024).strip()
        request.send("OK\n")
        log('Renaming %s to %s' % (target, new_name))
        os.rename(target, new_name)

    def process_incoming_announce(self, request):
        log('Incoming host announce')
        os.system("sudo /usr/sbin/csync2 -xA &")
        request.send("OK\n")

    def process_incoming_delete(self, request, filename):
        log('Incoming delete : %s' % filename)
        confirm = request.recv(1024).strip()
        request.send("OK\n")
        if os.path.isdir(filename):
            os.rmdir(filename)
        else:
            os.unlink(filename)

