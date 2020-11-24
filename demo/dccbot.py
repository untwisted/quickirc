"""

"""

# We import the basic modules.
from untwisted.network import SuperSocket
from untwisted.sock_writer import SockWriter
from untwisted.sock_reader import SockReader
from untwisted.client import Client, lose
from untwisted.splits import Terminator, logcon
from untwisted.tools import coroutine
from untwisted.event import CLOSE, ACCEPT_ERR, CONNECT, CONNECT_ERR, DONE, TIMEOUT
from untwisted.iputils import ip_to_long, long_to_ip
from quickirc import Irc, CTCP, send_cmd, DccServer, send_msg, DccClient
from socket import SOCK_STREAM, AF_INET, socket
from os.path import getsize, isfile
from untwisted import core

ADDRESS = 'irc.freenode.org'
PORT = 6667
NICK = 'uxirc'
USER = 'uxirc uxirc uxirc :uxirc'

# The folder where we will be serving files.
FOLDER = '/home/tau/Downloads'

@coroutine
def get_myaddr(con, prefix, nick, msg):
    send_cmd(con, 'userhost %s' % nick)
    args        = yield con, '302'
    _, _, ident = args
    user, myaddr   = ident.split('@')
    con.myaddr  = myaddr

def setup(con):
    SockWriter(con)
    SockReader(con)
    Terminator(con)
    Irc(con)
    CTCP(con)

    con.add_map('PING', lambda con, prefix, servaddr: send_cmd(con, 'PONG :%s' % servaddr))
    con.add_map('376', lambda con, *args: send_cmd(con, 'JOIN #ameliabot'))

    con.add_map('PRIVMSG', send_file)
    con.add_map('DCC SEND', check_file_existence)
    con.add_map('376', get_myaddr)
    con.add_map(CLOSE, lambda con, err: lose(con))

    logcon(con)

    send_cmd(con, 'NICK %s' % NICK)
    send_cmd(con, 'USER %s' % USER)

def main():
    sock = socket(AF_INET, SOCK_STREAM)
    con  = SuperSocket(sock)

    Client(con)
    con.connect_ex((ADDRESS, PORT))
    con.add_map(CONNECT, setup) 

def send_file(con, nick, user, host, target, msg):
    if not msg.startswith('.send'): 
        return
        
    cmd, filename, port = msg.split(' ')
    resource            = '%s/%s' % (FOLDER, filename)
    size                = getsize(resource)
    fd                  = open(resource, 'rb')

    def is_done(msg):
        send_msg(con, nick, msg)
        fd.close()

    try:
        dcc = DccServer(fd, int(port), timeout=50)
    except Exception:
        is_done('Couldnt list on the port!')
        raise

    dcc.add_map(DONE, lambda *args: is_done('Done.'))
    dcc.add_map(CLOSE, lambda *args: is_done('Failed!'))
    dcc.add_map(ACCEPT_ERR, lambda *args: is_done("Accept error!"))
    dcc.add_map(TIMEOUT, lambda *args: is_done('TIMEOUT!'))    

    HEADER  = '\001DCC SEND %s %s %s %s\001' 
    request = HEADER % (filename, ip_to_long(con.myaddr), port, size)
    send_msg(con, nick, request)

def check_file_existence(con, xxx_todo_changeme, 
                                        filename, address, port, size):
    (nick, user, host, target, msg) = xxx_todo_changeme
    resource = '%s/%s' % (FOLDER, filename) 
    if isfile(resource):      
        send_msg(con, nick, 'File already exists.')
    else:
        recv_file(con, nick, resource, address, port, size)

def recv_file(con, nick, resource, address, port, size):
    fd  = open(resource, 'wb')
    dcc = DccClient(long_to_ip(int(address)), 
                     int(port), fd, int(size)) 

    def is_done(msg):
        send_msg(con, nick, msg)
        fd.close()

    dcc.add_map(DONE, lambda *args: is_done('Done!'))
    dcc.add_map(CLOSE, lambda *args: is_done('Failed!'))
    dcc.add_map(CONNECT_ERR, lambda *args: is_done("It couldn't connect!"))

if __name__ == '__main__':
    # import argparser
    # parser = argparser.ArgumentParser()
    main()
    core.gear.mainloop()





