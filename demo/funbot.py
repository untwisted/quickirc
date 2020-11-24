from untwisted.network import SuperSocket
from untwisted.sock_writer import SockWriter
from untwisted.sock_reader import SockReader
from untwisted.client import Client, lose
from untwisted.event import CLOSE, CONNECT, CONNECT_ERR
from untwisted.splits import Terminator
from quickirc import Irc, send_cmd, send_msg
from untwisted import core
from socket import socket, AF_INET, SOCK_STREAM

class FunBot(object):
    """ Bot class """
    def __init__(self, ip, port, nick, user, password, *chan_list):
        """ It sets up the bot instance. """
        sock = socket(AF_INET, SOCK_STREAM)

        # We have to wrap our socket with a SuperSocket instance
        # in order to have our events issued when data comes
        # from the socket.
        con = SuperSocket(sock)
        
        # This protocol is required by uxirc.irc protocol.
        # It spawns CONNECT.
        Client(con)

        # We use connect_ex since we do not want an exception.
        # Untwisted uses non blocking sockets.
        con.connect_ex((ip, port))

        # We save whatever we might need.
        self.nick      = nick
        self.user      = user
        self.password  = password
        self.chan_list = chan_list
        self.ip        = ip
        self.port      = port

        # It maps CONNECT to self.send_auth so
        # when our socket connects it sends NICK and USER info.
        con.add_map(CONNECT, self.send_auth)
        con.add_map(CONNECT_ERR, lambda con, err: lose(con))

    def send_auth(self, con):
        # It is what we use to send data. send_msg function uses
        # ssock.dump function to dump commands.
        SockWriter(con)
        SockReader(con)

        # This protocol spawns FOUND whenever it finds \r\n.
        Terminator(con)

        Irc(con)
        
        con.add_map(CLOSE, lambda con, err: lose(con))

        # Now, it basically means: when it '376' irc command is
        # issued by the server then calls self.auto_join.
        # We use auto_join to send the sequence of JOIN
        # commands in order to join channels.
        con.add_map('376', self.auto_join)

        # Below the remaining stuff follows the same pattern.
        con.add_map('JOIN', self.on_join)
        con.add_map('PING', self.on_ping)
        con.add_map('PART', self.on_part)
        con.add_map('376', self.on_376)
        con.add_map('NOTICE', self.on_notice)
        con.add_map('PRIVMSG', self.on_privmsg)
        con.add_map('332', self.on_332)
        con.add_map('001', self.on_001)
        con.add_map('001', self.on_002)
        con.add_map('003', self.on_003)
        con.add_map('004', self.on_004)
        con.add_map('333', self.on_333)
        con.add_map('353', self.on_353)
        con.add_map('366', self.on_366)
        con.add_map('474', self.on_474)
        con.add_map('302', self.on_302)


        send_cmd(con, 'NICK %s' % self.nick)
        send_cmd(con, 'USER %s' % self.user)
        send_msg(con, 'nickserv', 'identify %s' % self.password)

    def auto_join(self, con, *args):
        for ind in self.chan_list:
            send_cmd(con, 'JOIN %s' % ind)

    def on_ping(self, con, prefix, servaddr):
        # If we do not need pong we are disconnected.
        print('on_ping', (prefix, servaddr))
        reply = 'PONG :%s\r\n' % servaddr
        send_cmd(con, reply)
        
    def on_join(self, con, nick, user, host, chan):
        print('on_join\n', (nick, user, host, chan))

    def on_part(self, con, nick, user, host, chan):
        print('on_part\n', (nick, user, host, chan))

    def on_privmsg(self, con, nick, user, host, target, msg):
        print('on_privmsg\n', (nick, user, host, target, msg))

    def on_332(self, con, prefix, nick, chan, topic):
        print('on_332\n', (prefix, nick, chan, topic))

    def on_302(self, con, prefix, nick, info):
        print('on_302\n', (prefix, nick, info))

    def on_333(self, con, prefix, nick_a, chan,  nick_b, ident):
        print('on_333\n', (prefix, nick_a, chan, nick_b, ident))

    def on_353(self, con, prefix, nick, mode, chan, peers):
        print('on_353\n', (prefix, nick, mode, chan, peers))

    def on_366(self, con, prefix, nick, chan, msg):
        print('on_366\n', (prefix, nick, chan, msg))

    def on_474(self, con, prefix, nick, chan, msg):
        print('on_474\n', (prefix, nick, chan, msg))

    def on_376(self, con, prefix, nick, msg):
        print('on_376\n', (prefix, nick, msg))

    def on_notice(self, con, prefix, nick, msg, *args):
        print('on_notice\n', (prefix, nick, msg), args)

    def on_001(self, con, prefix, nick, msg):
        print('on_001\n', (prefix, nick, msg))

    def on_002(self, con, prefix, nick, msg):
        print('on_002\n', (prefix, nick, msg))

    def on_003(self, con, prefix, nick, msg):
        print('on_004\n', (prefix, nick, msg))

    def on_004(self, con, prefix, nick, *args):
        print('on_004\n', (prefix, nick, args))
    
    def on_005(self, con, prefix, nick, *args):
        print('on_005', (prefix, nick, args))

bot = FunBot('irc.freenode.com', 6667, 'Fourier1', 'kaus keus kius :kous', '', '##calculus')
core.gear.mainloop()







