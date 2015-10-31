import socket
from time import sleep

owner='Iven_Trall'
server='irc.swc-irc.com'
channel='#safari-testing'
botnick='safari_guide'
botpass='eaten-b4-li0nes'
botmail='loki@mail.bg'
quitmessage='Expedition requests are suspended at this time!'

def parse(buff):
    message=buff.split('\r\n',1)[0]
    ## parse messages by sender
    if message.startswith(':irc.swc-irc.com'):
        if ' instead.' in message:
            ## register connection
            irc.send("USER {bn} {bn} {bn} :This is a test bot.\n".format(bn=botnick))
            irc.send("NICK %s\n" %(botnick))
        else:
            print message
    elif message.startswith(':NickServ!'):
        ## register nick and join channel
        if '/msg NickServ help' in message:
            irc.send("PRIVMSG nickserv :register %s %s\r\n" %(botpass,botmail))
            irc.send("JOIN %s\n" %(channel))
        ## identify nick and join channel
        elif '/msg NickServ identify' in message:
            irc.send("PRIVMSG nickserv :identify %s\r\n" %(botpass))
            irc.send("JOIN %s\n" %(channel))
        else:
            print message
    elif message.startswith('PING'):
        irc.send("PONG :%s\n" %(message.split(':')[1]))
        print message,'\nPONG'
    ## handle private messages to the bot
    elif "PRIVMSG %s" %(botnick) in message:
        if message.startswith(':'+owner):
            if '!shut_down' in message:
                irc.send("QUIT :%s" %(quitmessage))
                return "!shut_down"
            else:
                print message
    ## handle channel messages?
    elif "PRIVMSG %s" %(channel) in message:
        print message
    return buff.split('\r\n',1)[1]

irc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.setblocking(True)
print "connecting to:"+server
irc.connect((server,6667))
buff=''
while True:
    sleep(.3)
    buff+=irc.recv(1024)
    while '\r\n' in buff:
        buff=parse(buff)
    if buff=='!shut_down':
        break
irc.close()
