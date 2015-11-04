import socket
import pickle
import time

class Safari_bot:
    def __init__(self):
        self.owner='Iven_Trall'
        self.server='irc.swc-irc.com'
        self.channel='#safari-testing'
        self.botnick='safari_guide'
        self.botpass='eaten-b4-li0nes'
        self.botmail='loki@mail.bg'
        self.equipment={'weapons':{},'tools':{},'suits':{}}
        self.destinations={'destination':{},'game':{}}
        self.properties=[]
        self.content={}
        self.hunters={}
        self.hunter_file="registered_hunters.txt"
        self.equipment_file="equipment.txt"
        self.destination_file="planets.txt"
        self.content_file="content.txt"

    def connect(self):
        ## Connect to server
        self.irc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.irc.setblocking(True)
        print "connecting to:"+self.server
        self.irc.connect((self.server,6667))

    def relay_content(self,sender,code):
        code=str(code)
        for l in self.content[code]:
            self.irc.send("PRIVMSG %s :%s" %(sender,l))

    def load_hunters(self):
        ## Load known characters or create empty file
        try:
            with open(self.hunter_file,'r') as infile:
                try:
                    self.hunters=pickle.load(infile)
                except:
                    self.hunters={}
        except IOError:
            with open(self.hunter_file,'w') as outfile:
                print "Database file not found, recreated it."

    def refresh_hunters(self):
        with open(self.hunter_file,'w') as outfile:
            pickle.dump(self.hunters,outfile)

    def refresh_data(self):
        ## Load destinations
        with open(self.destination_file,'r') as infile:
            old_type=''
            for l in infile:
                l=l.strip().split('\t')
                if l[0]=='Type':
                    dest_properties=l[1:]
                    continue
                elif l[0]!=old_type:
                    i=1
                    old_type=l[0]
                self.destinations[l[0]][i]=dict(zip(dest_properties,l[1:]))
                i+=1
        ## Load equipment
        with open(self.equipment_file,'r') as infile:
            old_type=''
            for l in infile:
                l=l.strip().split('\t')
                if l[0]=='Type':
                    self.properties=l[2:]
                    for t in self.equipment:
                        self.equipment[t][0]={'name':'None','properties':[0]*len(self.properties)}
                    continue
                elif l[0]!=old_type:
                    i=1
                    old_type=l[0]
                self.equipment[l[0]][i]={'name':l[1],'properties':[int(x) for x in l[2:]]}
                i+=1
        ## Load text content by tags
        with open(self.content_file,'r') as infile:
            for l in infile:
                if l.strip():
                    l=l.split(':',1)
                    if l[0] not in self.content:
                        self.content[l[0]]=[l[1]]
                    else:
                        self.content[l[0]].append(l[1])
        #### Load creatures
        ##creatures={}
        ##with open('creatures.txt','r') as infile:

    def list_destinations(self,sender,t):
        if self.hunters[sender]['selected'][t]:
            self.irc.send("PRIVMSG %s :Your current %s is %s.\n" %(sender,t,('the ' if t=='game' else '')+self.destinations[t][self.hunters[sender]['selected'][t]]['name']))
        else:
            self.irc.send("PRIVMSG %s :You haven't selected your %s yet!\n" %(sender,t))
        self.irc.send("PRIVMSG %s :This is the list of available %s%s. Choose one with `!%s %s_number`.\n" %(sender,t,'' if t=='game' else 's',t,t))
        self.irc.send("PRIVMSG %s : ===%s%s===\n" %(sender,t.capitalize(),'' if t=='game' else 's'))
        for w in range(1,len(self.destinations[t])+1):
            self.irc.send("PRIVMSG %s : %d) %s: %s  Difficulty: %s%s\n"
                     %(sender,w,'Name' if t=='game' else 'Location',self.destinations[t][w]['name'].capitalize(),self.destinations[t][w]['difficulty'],
                       ('  Frequency: %s%%' %(self.destinations[t][w]['frequency'])) if t=='game' else ''))

    def list_equipment(self,sender,t):
        off=4+max([len(self.equipment[t][x]['name']) for x in self.equipment[t]])
        if self.hunters[sender]['equipment'][t]:
            self.irc.send("PRIVMSG %s :You are currently using a %s.\n" %(sender,self.equipment[t][self.hunters[sender]['equipment'][t]]['name']))
        else:
            self.irc.send("PRIVMSG %s :You haven't selected a %s yet!\n" %(sender,t[:-1]))
        self.irc.send("PRIVMSG %s :This is the list of available %s. Choose one with `!%s %s_number`.\n" %(sender,t,t,t[:-1]))
        self.irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                 %(sender,t.capitalize(),''.join(['%-12s' %(x) for x in self.properties])))
        for w in range(1,len(self.equipment[t])):
            self.irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                     %(sender,'%d) ' %(w)+self.equipment[t][w]['name'],''.join(['%-12d' %(p) for p in self.equipment[t][w]['properties']])))

    def list_personal(self,sender):
        off=4+max([len(self.equipment[t][self.hunters[sender]['equipment'][t]]['name']) for t in self.hunters[sender]['equipment']])
        self.irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                 %(sender,'Name',''.join(['%-12s' %(x) for x in self.properties])))
        for t in ['weapons','tools','suits']:
            self.irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                     %(sender,self.equipment[t][self.hunters[sender]['equipment'][t]]['name'],''.join(['%-12s' %(str(p)) for p in self.equipment[t][self.hunters[sender]['equipment'][t]]['properties']])))
        self.irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                 %(sender,'TOTAL',''.join(['%-12d' %(sum([self.equipment[t][self.hunters[sender]['equipment'][t]]['properties'][x] for t in ['weapons','tools','suits']])) for x in range(len(self.properties))])))

    def parse(self,buff):
        message=buff.split('\r\n',1)[0]
        ## parse messages by sender
        ## System messages
        if message.startswith(':irc.swc-irc.com'):
            if ' instead.' in message:
                ## register connection
                self.irc.send("USER {bn} {bn} {bn} :This is a test bot.\n".format(bn=self.botnick))
                self.irc.send("NICK %s\n" %(self.botnick))
            else:
                print message
        elif message.startswith(':NickServ!'):
            ## register nick and join channel
            if '/msg NickServ help' in message:
                self.irc.send("PRIVMSG nickserv :register %s %s\r\n" %(self.botpass,self.botmail))
                self.irc.send("JOIN %s\n" %(self.channel))
            ## identify nick and join channel
            elif '/msg NickServ identify' in message:
                self.irc.send("PRIVMSG nickserv :identify %s\r\n" %(self.botpass))
                self.irc.send("JOIN %s\n" %(self.channel))
            else:
                print message
        elif message.startswith('PING'):
            self.irc.send("PONG :%s\n" %(message.split(':')[1]))
        ## handle private messages to the bot
        elif "PRIVMSG %s" %(self.botnick) in message:
            message=message.strip()
            sender=message.split("!")[0][1:]
            ## Handle owner-only functions
            if sender==self.owner:
                if '!shut-down' in message:
                    return "!shut-down"
                elif '!clear-me' in message:
                    try:
                        self.hunters.pop(sender)
                    except KeyError:
                        pass
                    self.irc.send("PRIVMSG %s :Data on %s cleared!\n" %(sender,sender))
                elif '!injure-me' in message:
                    self.hunters[sender]['injured_on']=time.time()-3600*int(message.split()[-1])
                    self.irc.send("PRIVMSG %s :Injury added!\n" %(sender,sender))
                elif '!refresh' in message:
                    self.refresh_data()
                    self.irc.send("PRIVMSG %s :Data refreshed!\n" %(sender))
                else:
                    print message
            ## Commands open to all users
            if message.endswith(':!sign-up'):
                if sender in self.hunters:
                    self.irc.send("PRIVMSG %s :You are already registered as a hunter!\n" %(sender))
                else:
                    self.hunters[sender]={'equipment':{'weapons':0,'tools':0,'suits':0},'trip':0,
                                     'selected':{'destination':0,'game':0},'injured_on':0,
                                     'exp':0}
                    ## Save new hunters immediately to preserve information in case of bugs
                    self.refresh_hunters()
                    self.relay_content(sender,'registered')
            elif message.endswith(':!help'):
                if sender not in self.hunters:
                    self.relay_content(sender,'help0')
                elif not self.hunters[sender]['trip']:
                    self.relay_content(sender,'help1')
            ## Handle hunter commands
            elif sender in self.hunters:
                ## Handle equipment commands
                if ':!weapons ' in message or ':!tools ' in message or ':!suits ' in message \
                   or message.split(':!')[-1] in self.equipment.keys():
                    t=message.split(':!')[-1].split(' ')[0]
                    selected=message.split(':!'+t)[-1].strip()
                    if selected:
                        if selected.isdigit() and int(selected) in self.equipment[t] and int(selected):
                            self.hunters[sender]['equipment'][t]=int(selected)
                            irc.send("PRIVMSG %s :You have selected the %s as your %s! You can freely change your %s selection between hunting trips. You can check your hunter stats with the !status command.\n" %(sender,self.equipment[t][int(selected)]['name'],t[:-1],t[:-1]))
                        else:
                            irc.send("PRIVMSG %s :This %s identification code is not in our database! Current codes range from 1 to %d.\n" %(sender,t[:-1],len(self.equipment[t])-1))
                    else:
                        self.list_equipment(sender,t)
                ## Handle planet & game commands
                elif ':!destination ' in message or ':!game ' in message \
                   or message.endswith('!destination') or message.endswith('!game'):
                    t=message.split(':!')[-1].split(' ')[0]
                    selected=message.split(':!'+t)[-1].strip()
                    if selected:
                        if selected.isdigit() and int(selected) in self.destinations[t] and int(selected):
                            self.hunters[sender]['selected'][t]=int(selected)
                            self.irc.send("PRIVMSG %s : You have selected %s as your %s!\n" %(sender,('the ' if t=='game' else '')+self.destinations[t][int(selected)]['name'],t))
                            self.irc.send("PRIVMSG %s : %s\n" %(sender,self.destinations[t][int(selected)]['description']))
                        else:
                            self.irc.send("PRIVMSG %s :This %s identification code is not in our database! Current codes range from 1 to %d.\n" %(sender,t,len(self.destinations[t])))
                    else:
                        self.list_destinations(sender,t)
                ## Handle status requests
                elif message.endswith(':!status'):
                    self.irc.send("PRIVMSG %s :Hunter statistics for %s:\n" %(sender,sender))
                    self.irc.send("PRIVMSG %s :EQUIPMENT\n" %(sender))
                    self.list_personal(sender)
                    self.irc.send("PRIVMSG %s :Hunting experience: %d\n" %(sender,self.hunters[sender]['exp']))
                    if self.hunters[sender]['injured_on']:
                        injury_time=int((time.time()-self.hunters[sender]['injured_on'])/3600.)
                        if injury_time>=24:
                            injured='Cleared for participation'
                        else:
                            injured='Under surveilance! (%d hour%s remaining)' %(24-injury_time,'s' if injury_time<23 else '')
                    else:
                        injured='Cleared for participation'
                    self.irc.send("PRIVMSG %s :Medical status: %s\n" %(sender,injured))
                else:
                    self.irc.send("PRIVMSG %s :This is not a recognized command, try !help to see available commands.\r\n" %(sender))
                self.refresh_hunters()
            else:
                self.irc.send("PRIVMSG %s :You are not registered as a hunter with our company! Please use !sign-up to register or !help to learn more about us.\r\n" %(sender))
        ## handle channel messages?
        elif "PRIVMSG %s" %(self.channel) in message:
            print message
        return buff.split('\r\n',1)[1]

bot=Safari_bot()
bot.load_hunters()
bot.refresh_data()
bot.connect()
buff=''
while True:
    time.sleep(.3)
    buff+=bot.irc.recv(1024)
    while '\r\n' in buff:
        buff=bot.parse(buff)
    if buff=='!shut-down':
        break
bot.irc.close()
bot.refresh_hunters()
