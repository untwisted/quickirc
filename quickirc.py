""" 
"""

from untwisted.event import TIMEOUT, DONE, ACCEPT, CLOSE, \
CONNECT, CONNECT_ERR, LOAD, DUMPED
from untwisted.splits import Terminator, Fixed
from untwisted.network import SuperSocket
from untwisted.client import Client, lose
from untwisted.dispatcher import Dispatcher
from untwisted.sock_writer import SockWriter
from untwisted.sock_reader import SockReader
from untwisted.server import Server
from untwisted.timer import Timer
from struct import pack, unpack
from textwrap import wrap
from socket import socket, AF_INET, SOCK_STREAM

import re

RFC_STR        = "^(:(?P<prefix>[^ ]+) +)?(?P<command>[^ ]+)( *(?P<arguments> .+))?"
RFC_REG        = re.compile(RFC_STR)
PREFIX_STR     = "(?P<nick>.+)!(?P<user>.+)@(?P<host>.+)"
PREFIX_REG     = re.compile(PREFIX_STR)
PRIVMSG_HEADER = b'PRIVMSG %s :%s\r\n'
CMD_HEADER     = b'%s\r\n'

class DccServer(Dispatcher):
    """ 
    This class is used to send files. It is called DccServer cause the one sending 
    a file is the one who sets up a server.
    """

    def __init__(self, fd, port, timeout=20):
        """
        fd      -> The file to be sent.
        port    -> The port which will be used.
        timeout -> How long the server must be up.
        """

        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind(('', port))
        sock.listen(1)
        self.local = SuperSocket(sock)
        Server(self.local)

        Dispatcher.__init__(self)
        self.fd      = fd
        self.timeout = timeout
        self.port    = port
       
        self.local.add_map(ACCEPT, self.on_accept) 
        self.timer = Timer(self.timeout, self.on_timeout)
        
    def on_timeout(self):
        self.drive(TIMEOUT)
        lose(self.local)

    def on_accept(self, local, ssock):
        """
        """

        SockReader(ssock)
        SockWriter(ssock)
        Fixed(ssock)

        ssock.dumpfile(self.fd)

        ssock.add_map(CLOSE, lambda con, err: lose(con)) 
        ssock.add_map(Fixed.FOUND, self.on_ack) 
        ssock.add_handle(lambda ssock, event, args: self.drive(event, ssock, *args))
        self.timer.cancel()

    def on_ack(self, ssock, ack):
        """
        """
        pos = unpack("!I", ack)[0]

        if pos >= self.fd.tell(): 
            self.run_done(ssock)

    def run_done(self, ssock):
        lose(ssock)
        lose(self.local)
        ssock.drive(DONE)

class DccClient(Dispatcher):
    def __init__(self, host, port, fd, size):
        """
        """
        Dispatcher.__init__(self)

        sock      = socket(AF_INET, SOCK_STREAM)
        ssock      = SuperSocket(sock)
        self.port = port
        self.fd   = fd
        self.size = size
        
        Client(ssock)
        ssock.connect_ex((host, port))
   
        ssock.add_map(CONNECT, self.on_connect) 
        ssock.add_map(CONNECT_ERR, lambda con, err: lose(con)) 

        ssock.add_handle(lambda ssock, event, args: self.drive(event, ssock, *args))

    def on_connect(self, ssock):
        """
        """

        SockReader(ssock)
        SockWriter(ssock)
        ssock.add_map(LOAD, self.on_load) 
        ssock.add_map(CLOSE, lambda con, err: lose(con)) 

    def on_load(self, ssock, data):
        """
        """

        self.fd.write(data)
        ssock.dump(pack('!I', self.fd.tell()))

        if self.fd.tell() >= self.size:
            ssock.add_map(DUMPED, self.run_done)

    def run_done(self, ssock):
        lose(ssock)
        self.sdrive(DONE)

class Irc(object):
    def __init__(self, ssock, encoding='utf8'):
        """ 
        Install the protocol inside a SuperSocket instance. 
        """
        self.encoding = encoding
        ssock.add_map(Terminator.FOUND, self.main)

    def main(self, ssock, data):
        """ 
        The function which uses irc rfc regex to extract
        the basic arguments from the msg.
        """
        data  = data.decode(self.encoding)
        field = re.match(RFC_REG, data)
        
        if not field:
            return
    
        prefix  = self.extract_prefix(field.group('prefix'))
        command = field.group('command').upper()
        args    = self.extract_args(field.group('arguments'))
        ssock.drive(command, *(prefix + args))
    
    def extract_prefix(self, prefix):
        """ 
        It extracts an irc msg prefix chunk 
        """

        field = re.match(PREFIX_REG, prefix if prefix else '')
        
        return (prefix,) if not field else field.group(1, 2, 3)
    
    def extract_args(self, data):
        """ 
        It extracts irc msg arguments. 
        """
        args = []
        data = data.strip(' ')
        if ':' in data:
            lhs, rhs = data.split(':', 1)
            if lhs: args.extend(lhs.rstrip(' ').split(' '))
            args.append(rhs)
        else:
           args.extend(data.split(' '))
        return tuple(args)    
    
class CTCP(object):
    def __init__(self, ssock):
        """ 
        It installs the subprotocol inside a SuperSocket
        instance.
        """
        ssock.add_map('PRIVMSG', self.extract_ctcp)
    
        ssock.add_map('DCC', self.patch)
    
    def extract_ctcp(self, ssock, nick, user, host, target, msg):
        """ 
        it is used to extract ctcp requests into pieces.
        """
    
        # The ctcp delimiter token.
        DELIM = '\001'
    
        if not msg.startswith(DELIM) or not msg.endswith(DELIM):
            return
    
        ctcp_args = msg.strip(DELIM).split(' ') 
        
        ssock.drive(ctcp_args[0], (nick, user, host,  target, msg), *ctcp_args[1:])
    
    def patch(self, ssock, header, *args):
        """ 
        It spawns DCC TYPE as event. 
        """

        ssock.drive('DCC %s' % args[0], header, *args[1:])
    

class Misc(object):
    def __init__(self, ssock):
        ssock.add_map('001', self.on_001)
        ssock.add_map('PRIVMSG', self.on_privmsg)
        ssock.add_map('JOIN', self.on_join)
        ssock.add_map('PART', self.on_part)
        ssock.add_map('353', self.on_353)
        ssock.add_map('332', self.on_332)
        ssock.add_map('NICK', self.on_nick)
        ssock.add_map('KICK', self.on_kick)
        ssock.add_map('MODE', self.on_mode)

        self.nick = ''

    def on_privmsg(self, ssock, nick, user, host, target, msg):
        ssock.drive('PRIVMSG->%s' % target.lower(), nick, user, host, msg)
        ssock.drive('PRIVMSG->%s' % nick.lower(), target, user, host, msg)

        if target.startswith('#'):
            ssock.drive('CMSG', nick, user, host, target, msg)
        elif self.nick.lower() == target.lower():
            ssock.drive('PMSG', nick, user, host, target, msg)
        
    def on_join(self, ssock, nick, user, host, chan):
        if self.nick == nick: 
            ssock.drive('*JOIN', chan)
        else:
            ssock.drive('JOIN->%s' % chan, nick, 
                  user, host)
    
    def on_353(self, ssock, prefix, nick, mode, chan, peers):
        ssock.drive('353->%s' % chan, prefix, 
              nick, mode, peers)
    
    def on_332(self, ssock, addr, nick, channel, msg):
        ssock.drive('332->%s' % channel, addr, nick, msg)
    
    def on_part(self, ssock, nick, user, host, chan, msg=''):
        ssock.drive('PART->%s' % chan, nick, 
              user, host, msg)
    
        if self.nick == nick: 
            ssock.drive('*PART->%s' % chan, user, host, msg)
    
    def on_001(self, ssock, address, nick, *args):
        self.nick = nick
    
    def on_nick(self, ssock, nicka, user, host, nickb):
        if not self.nick == nicka: 
            return
    
        self.nick = nickb;
        ssock.drive('*NICK', nicka, user, host, nickb)

    def on_kick(self, ssock, nick, user, host, chan, target, msg=''):
        ssock.drive('KICK->%s' % chan, nick, user, host, target, msg)

        if self.nick == target:
            ssock.drive('*KICK->%s' % chan, nick, user, host, target, msg)

    def on_mode(self, ssock, nick, user, host, chan='', mode='', target=''):
        ssock.drive('MODE->%s' % chan, nick, user, host, mode, target)

def send_msg(server, target, msg, encoding='utf8'):
    for ind in wrap(msg, width=512):
        server.dump(PRIVMSG_HEADER % (target.encode(
            encoding), ind.encode(encoding)))

def send_cmd(server, cmd, encoding='utf8'):
    server.dump(CMD_HEADER % cmd.encode(encoding))



