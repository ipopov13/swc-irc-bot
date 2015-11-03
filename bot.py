import socket
import pickle
from time import sleep

owner='Iven_Trall'
server='irc.swc-irc.com'
channel='#safari-testing'
botnick='safari_guide'
botpass='eaten-b4-li0nes'
botmail='loki@mail.bg'

equipment={}

def list_equipment(sender,t):
    if hunters[sender]['equipment'][t]:
        irc.send("PRIVMSG %s :You are currently using a %s.\n" %(sender,equipment[t][hunters[sender]['equipment'][t]]['name']))
    else:
        irc.send("PRIVMSG %s :You haven't selected a %s yet!\n" %(sender,t[:-1]))
    irc.send("PRIVMSG %s :This is the list of available %s. Choose one with `!%s %s_number`.\n" %(sender,t,t,t[:-1]))
    irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=4+max([len(equipment[t][x]['name']) for x in equipment[t]]))
             %(sender,t.capitalize(),''.join(['%-12s' %(x) for x in properties])))
    for w in equipment[t]:
        irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=4+max([len(equipment[t][x]['name']) for x in equipment[t]]))
                 %(sender,'%d) ' %(w)+equipment[t][w]['name'],''.join(['%-12s' %(str(p)) for p in equipment[t][w]['properties']])))

def refresh_hunters():
    with open("registered_hunters.txt",'w') as outfile:
        pickle.dump(hunters,outfile)

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
        message=message.strip()
        sender=message.split("!")[0][1:]
        ## Handle owner-only functions
        if sender==owner:
            if '!shut-down' in message:
                return "!shut-down"
            elif '!clear-me' in message:
                hunters.pop(sender)
                irc.send("PRIVMSG %s :Data on %s cleared!\n" %(sender,sender))
            else:
                print message
        ## Commands open to all users
        if message.endswith(':!sign-up'):
            if sender in hunters:
                irc.send("PRIVMSG %s :You are already registered as a hunter!\n" %(sender))
            else:
                hunters[sender]={'equipment':{'weapons':0,'tools':0,'suits':0},'trip':-1,
                                 'selected':{'planet':'','quarry':''},'injured_on':0,
                                 'exp':0}
                ## Save new hunters immediately to preserve information in case of bugs
                refresh_hunters()
                irc.send("PRIVMSG %s :Congratulations! You are now registered as a hunter and can use our guide service to explore the various worlds of the Galaxy. Use !help to see available commands at any time!\n" %(sender))
                irc.send("PRIVMSG %s :You should now select your starting equipment. Equipped items can be changed freely between trips, but once you start the hunt you have to finish with what you have selected. When exploring dangerous planets or tracking lethal prey it is good to bring along friends with equipment that complements your own.\n" %(sender))
                irc.send("PRIVMSG %s :Use !weapons, !tools, and !suits to check out the available equipment and make a selection.\n" %(sender))
                irc.send("PRIVMSG %s :YOU WILL NOT BE ALLOWED TO PARTICIPATE IN A HUNT BEFORE EQUIPPING AN ITEM IN EVERY SLOT!\n" %(sender))
        elif message.endswith(':!help'):
            ## !help can be used by non-hunters too! They get an adverticement!
            pass
        ## Handle hunter commands
        ## TO DO: !status, !tools, !suits, code and trip commands!
        elif sender in hunters:
            if ':!weapons ' in message or ':!tools ' in message or ':!suits ' in message \
               or message.split(':!')[-1] in equipment.keys():
                t=message.split(':!')[-1].split(' ')[0]
                selected=message.split(':!'+t)[-1].strip()
                if selected:
                    if selected.isdigit() and int(selected) in equipment[t]:
                        hunters[sender]['equipment'][t]=int(selected)
                        irc.send("PRIVMSG %s :You have selected the %s as your %s! You can freely change your %s selection between hunting trips. You can check your hunter stats with the !status command.\n" %(sender,equipment[t][int(selected)]['name'],t[:-1],t[:-1]))
                    else:
                        irc.send("PRIVMSG %s :This %s identification code is not in our database! Current codes range from 1 to %d.\n" %(sender,t[:-1],len(equipment[t])))
                else:
                    list_equipment(sender,t)
            else:
                irc.send("PRIVMSG %s :This is not a recognized command, try !help to see available commands.\r\n" %(sender))
            refresh_hunters()
        else:
            irc.send("PRIVMSG %s :You are not registered as a hunter with our company! Please use !sign-up to register or !help to learn more about us.\r\n" %(sender))
    ## handle channel messages?
    elif "PRIVMSG %s" %(channel) in message:
        print message
    return buff.split('\r\n',1)[1]

## Load known characters or create empty file
try:
    with open("registered_hunters.txt",'r') as infile:
        try:
            hunters=pickle.load(infile)
        except:
            hunters={}
except IOError:
    with open('registered_hunters.txt','w') as outfile:
        hunters={}
## Load equipment
equipment={'weapons':{},'tools':{},'suits':{}}
with open('equipment.txt','r') as infile:
    old_type=''
    for l in infile:
        l=l.strip().split('\t')
        if l[0]=='Type':
            properties=l[2:]
            continue
        elif l[0]!=old_type:
            i=1
            old_type=l[0]
        equipment[l[0]][i]={'name':l[1],'properties':[int(x) for x in l[2:]]}
        i+=1
#### Load creatures
##creatures={}
##with open('creatures.txt','r') as infile:
    
## Connect to server
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
    if buff=='!shut-down':
        break
irc.close()
refresh_hunters()
