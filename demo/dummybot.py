from untwisted.network import SuperSocket
from untwisted.sock_writer import SockWriter
from untwisted.sock_reader import SockReader
from untwisted.client import Client, lose
from quickirc import Irc, send_cmd
from untwisted.splits import Terminator, logcon
from socket import socket, AF_INET, SOCK_STREAM
from untwisted.event import CLOSE, CONNECT, CONNECT_ERR
from untwisted import core

def send_auth(con, nick, user):
    SockWriter(con)
    SockReader(con)
    Terminator(con)
    Irc(con)
    logcon(con)

    con.add_map(CLOSE, lambda con, err: lose(con))
    send_cmd(con, 'NICK %s' % nick)
    send_cmd(con, 'USER %s' % user)

def send_pong(con, prefix, servaddr):
    reply = 'PONG :%s\r\n' % servaddr
    send_cmd(con, reply)

def connect(addr, port, nick, user, *chans):
    sock = socket(AF_INET, SOCK_STREAM)
    con  = SuperSocket(sock)
    Client(con)
    con.connect_ex((addr, port))

    def auto_join(con, *args):
        for ind in chans:
            send_cmd(con, 'JOIN %s' % ind)

    con.add_map(CONNECT, send_auth, nick, user)
    con.add_map(CONNECT_ERR, lambda con, err: lose(con))
    con.add_map('PING', send_pong)
    con.add_map('376', auto_join)
    return con

NICK_LIST = ('alphaaaa','cooool', 'blablalb')

for ind in NICK_LIST:
    connect('irc.freenode.org', 6667, ind, 'ae eu de :uxirc', '#vy')

core.gear.mainloop()





