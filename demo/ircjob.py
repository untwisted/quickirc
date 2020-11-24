from untwisted.network import SuperSocket
from untwisted.sock_writer import SockWriter
from untwisted.sock_reader import SockReader
from untwisted.client import Client, lose
from untwisted.timer import Sched
from quickirc import Irc, send_cmd
from untwisted.splits import Terminator, logcon
from socket import socket, AF_INET, SOCK_STREAM
from untwisted.event import CLOSE, CONNECT, CONNECT_ERR
from untwisted import core
from time import sleep


def send_auth(con, nick, user, cmd, delay):
    SockWriter(con)
    SockReader(con)
    Terminator(con)
    Irc(con)
    logcon(con)

    def do_job(ssock, *args):
        for ind in cmd:
            send_cmd(ssock, ind)
            sleep(delay)
    
    con.add_map('376', do_job)
    con.add_map('PING', lambda con, prefix, 
            servaddr: send_cmd(con, 'PONG :%s' % servaddr))

    con.add_map(CLOSE, lambda con, err: lose(con))
    send_cmd(con, 'NICK %s' % nick)
    send_cmd(con, 'USER %s' % user)

def main(address, port, nick, user, cmd, delay=1):
    sock = socket(AF_INET, SOCK_STREAM)
    con  = SuperSocket(sock)
    
    Client(con)
    con.connect_ex((address, port))
    con.add_map(CONNECT, send_auth, nick, user, cmd, delay)
    return con

if __name__ == '__main__':
    USER     = 'uxirc beta gama :uxirc'
    NICK     = 'alphaaa'
    CMD      = ('JOIN #vy','PRIVMSG #vy :Uriel', 'quit')
    INTERVAL = 20
    cbck     = lambda :main('irc.freenode.com', 6667, NICK, USER, CMD)
    Sched(INTERVAL, cbck)

    core.gear.mainloop()







