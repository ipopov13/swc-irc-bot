import socket
import pickle
import time

owner='Iven_Trall'
server='irc.swc-irc.com'
channel='#safari-testing'
botnick='safari_guide'
botpass='eaten-b4-li0nes'
botmail='loki@mail.bg'

equipment={}

def list_equipment(sender,t):
    off=4+max([len(equipment[t][x]['name']) for x in equipment[t]])
    if hunters[sender]['equipment'][t]:
        irc.send("PRIVMSG %s :You are currently using a %s.\n" %(sender,equipment[t][hunters[sender]['equipment'][t]]['name']))
    else:
        irc.send("PRIVMSG %s :You haven't selected a %s yet!\n" %(sender,t[:-1]))
    irc.send("PRIVMSG %s :This is the list of available %s. Choose one with `!%s %s_number`.\n" %(sender,t,t,t[:-1]))
    irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
             %(sender,t.capitalize(),''.join(['%-12s' %(x) for x in properties])))
    for w in range(1,len(equipment[t])):
        irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                 %(sender,'%d) ' %(w)+equipment[t][w]['name'],''.join(['%-12d' %(p) for p in equipment[t][w]['properties']])))

def list_personal(sender):
    off=4+max([len(equipment[t][hunters[sender]['equipment'][t]]['name']) for t in hunters[sender]['equipment']])
    irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
             %(sender,'Name',''.join(['%-12s' %(x) for x in properties])))
    for t in ['weapons','tools','suits']:
        irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                 %(sender,equipment[t][hunters[sender]['equipment'][t]]['name'],''.join(['%-12s' %(str(p)) for p in equipment[t][hunters[sender]['equipment'][t]]['properties']])))
    irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
             %(sender,'TOTAL',''.join(['%-12d' %(sum([equipment[t][hunters[sender]['equipment'][t]]['properties'][x] for t in ['weapons','tools','suits']])) for x in range(len(properties))])))

def refresh_hunters():
    with open("registered_hunters.txt",'w') as outfile:
        pickle.dump(hunters,outfile)

def relay_file(sender,f,code):
    code=str(code)
    with open(f,'r') as infile:
        for l in infile:
            if l.startswith(code+':'):
                irc.send("PRIVMSG %s :%s" %(sender,l.strip(code+':')))

def parse(buff):
    message=buff.split('\r\n',1)[0]
    ## parse messages by sender
    ## System messages
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
                try:
                    hunters.pop(sender)
                except KeyError:
                    pass
                irc.send("PRIVMSG %s :Data on %s cleared!\n" %(sender,sender))
            elif '!injure-me' in message:
                hunters[sender]['injured_on']=time.time()-3600*int(message.split()[-1])
                irc.send("PRIVMSG %s :Injury added!\n" %(sender,sender))
            else:
                print message
        ## Commands open to all users
        if message.endswith(':!sign-up'):
            if sender in hunters:
                irc.send("PRIVMSG %s :You are already registered as a hunter!\n" %(sender))
            else:
                hunters[sender]={'equipment':{'weapons':0,'tools':0,'suits':0},'trip':0,
                                 'selected':{'planets':'','game':''},'injured_on':0,
                                 'exp':0}
                ## Save new hunters immediately to preserve information in case of bugs
                refresh_hunters()
                irc.send("PRIVMSG %s :Congratulations! You are now registered as a hunter and can use our guide service to explore the various worlds of the Galaxy. Use !help to see available commands at any time!\n" %(sender))
                irc.send("PRIVMSG %s :You should now select your starting equipment. Equipped items can be changed freely between trips, but once you start the hunt you have to finish with what you have selected. When exploring dangerous planets or tracking lethal prey it is good to bring along friends with equipment that complements your own.\n" %(sender))
                irc.send("PRIVMSG %s :Use !weapons, !tools, and !suits to check out the available equipment and make a selection.\n" %(sender))
                irc.send("PRIVMSG %s :After that you can try our free tours that are always located on the top of the game list! (use !help or !game for details)\n" %(sender))
                irc.send("PRIVMSG %s :YOU WILL NOT BE ALLOWED TO PARTICIPATE IN A HUNT BEFORE EQUIPPING AN ITEM IN EVERY SLOT!\n" %(sender))
        elif message.endswith(':!help'):
            if sender not in hunters:
                relay_file(sender,'help.txt',0)
            elif not hunters[sender]['trip']:
                relay_file(sender,'help.txt',1)
        ## Handle hunter commands
        ## TO DO: code and trip commands!
        elif sender in hunters:
            ## Handle equipment commands
            if ':!weapons ' in message or ':!tools ' in message or ':!suits ' in message \
               or message.split(':!')[-1] in equipment.keys():
                t=message.split(':!')[-1].split(' ')[0]
                selected=message.split(':!'+t)[-1].strip()
                if selected:
                    if selected.isdigit() and int(selected) in equipment[t] and int(selected):
                        hunters[sender]['equipment'][t]=int(selected)
                        irc.send("PRIVMSG %s :You have selected the %s as your %s! You can freely change your %s selection between hunting trips. You can check your hunter stats with the !status command.\n" %(sender,equipment[t][int(selected)]['name'],t[:-1],t[:-1]))
                    else:
                        irc.send("PRIVMSG %s :This %s identification code is not in our database! Current codes range from 1 to %d.\n" %(sender,t[:-1],len(equipment[t])-1))
                else:
                    list_equipment(sender,t)
            ## Handle planet & game commands
            if ':!destination ' in message or ':!game ' in message \
               or message.endswith('!destination') or message.endswith('!game'):
                t=message.split(':!')[-1].split(' ')[0]
                selected=message.split(':!'+t)[-1].strip()
                if selected:
                    if selected.isdigit() and int(selected) in destinations[t] and int(selected):
                        hunters[sender]['selected'][t]=int(selected)
                        irc.send("PRIVMSG %s :You have selected %s as your %s!\n" %(sender,destinations[t][int(selected)]['name'],t))
                    else:
                        irc.send("PRIVMSG %s :This %s identification code is not in our database! Current codes range from 1 to %d.\n" %(sender,t,len(destinations[t])))
                else:
                    list_destinations(sender,t)
            ## Handle status requests
            elif message.endswith(':!status'):
                irc.send("PRIVMSG %s :Hunter statistics for %s:\n" %(sender,sender))
                irc.send("PRIVMSG %s :EQUIPMENT\n" %(sender))
                list_personal(sender)
                irc.send("PRIVMSG %s :Hunting experience: %d\n" %(sender,hunters[sender]['exp']))
                if hunters[sender]['injured_on']:
                    injury_time=int((time.time()-hunters[sender]['injured_on'])/3600.)
                    if injury_time>=24:
                        injured='Cleared for participation'
                    else:
                        injured='Under surveilance! (%d hour%s remaining)' %(24-injury_time,'s' if injury_time<23 else '')
                else:
                    injured='Cleared for participation'
                irc.send("PRIVMSG %s :Medical status: %s\n" %(sender,injured))
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
            for t in equipment:
                equipment[t][0]={'name':'None','properties':[0]*len(properties)}
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
    time.sleep(.3)
    buff+=irc.recv(1024)
    while '\r\n' in buff:
        buff=parse(buff)
    if buff=='!shut-down':
        break
irc.close()
refresh_hunters()
