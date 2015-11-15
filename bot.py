import socket
import pickle
import time
import random
import math
        
class Safari_bot:
    def __init__(self):
        self.owner='Iven_Trall'
        self.owner_handle='Iven Trall'
        self.server='irc.swc-irc.com'
        self.channel='#safari-testing'
        self.botnick='safari_guide'
        self.botpass='eaten-b4-li0nes'
        self.botmail='loki@mail.bg'
        self.equipment={'weapons':{},'tools':{},'suits':{}}
        self.destinations={'destination':{0:{'name':'none'}},
                           'game':{0:{'frequency':0,'planet':'','terrains':'','name':'none'}}}
        self.destlist=[]
        self.gamelist=[]
        self.properties=[]
        self.content={}
        self.hunters={}
        self.orders={}
        self.trips={}
        self.data_file="data.dat"
        self.equipment_file="equipment.txt"
        self.destination_file="planets.txt"
        self.content_file="content.txt"
        self.difficulties={'fight':[1,2,4,8,15],
                           'hide':[2,2,3,3,3],
                           'track':[2,2,3,3,4],
                           'survive':[2,2,2,3,3]}
        self.refresh_data()
        self.dest_games={}
        self.game_freqs={}
        self.terr_games={}
        for g in self.destinations['game']:
            for t in self.destinations['game'][g]['terrains'].split('/'):
                self.terr_games[t]=self.terr_games.get(t,[])+[self.destinations['game'][g]['name']]
            self.dest_games[self.destinations['game'][g]['planet']]=self.dest_games.get(self.destinations['game'][g]['planet'],[])+[self.destinations['game'][g]['name']]
            self.game_freqs[self.destinations['game'][g]['name']]=int(self.destinations['game'][g]['frequency'])
        self.load_hunters()
        self.GSChunters={"Gamorrean guide":{'equipment':{'weapons':12,'tools':5,'suits':2}},
                      "Squib tracker":{'equipment':{'weapons':13,'tools':3,'suits':6}},
                      "Sakiyan hunter":{'equipment':{'weapons':11,'tools':2,'suits':5}},
                      "Aleena hunter":{'equipment':{'weapons':6,'tools':7,'suits':5}},
                      "Kubaz hunter":{'equipment':{'weapons':9,'tools':8,'suits':5}},
                      "Weequay hunter":{'equipment':{'weapons':2,'tools':4,'suits':5}}}
        self.hunters.update(self.GSChunters)
        
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
            with open(self.data_file,'rb') as infile:
                self.hunters=pickle.load(infile)
                self.orders=pickle.load(infile)
                self.trips=pickle.load(infile)
        except IOError or EOFError:
            with open(self.data_file,'wb') as outfile:
                print "Database file not found or empty, recreated it."

    def refresh_hunters(self):
        with open(self.data_file,'wb') as outfile:
            pickle.dump(self.hunters,outfile,-1)
            pickle.dump(self.orders,outfile,-1)
            pickle.dump(self.trips,outfile,-1)

    def refresh_data(self):
        ## Load destinations and creatures
        with open(self.destination_file,'r') as infile:
            old_type=''
            for l in infile:
                if l.strip():
                    l=l.strip().split('\t')
                    if l[0]=='Type':
                        dest_properties=l[1:]
                        continue
                    elif l[0]!=old_type:
                        i=1
                        old_type=l[0]
                    if l[0]=='destination':
                        self.destlist.append(l[1].lower())
                    else:
                        self.gamelist.append(l[1].lower())
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
                        self.equipment[t][0]={'name':'(%s)' %(t[:-1]),'properties':[0]*len(self.properties)}
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

    ## List destinations and game
    def list_destinations(self,sender,t):
        if self.hunters[sender]['selected'][t]:
            self.irc.send("PRIVMSG %s :Your current %s is %s.\n" %(sender,t,('the ' if t=='game' else '')+self.destinations[t][self.hunters[sender]['selected'][t]]['name']))
        else:
            self.irc.send("PRIVMSG %s :You haven't selected your %s yet!\n" %(sender,t))
        self.irc.send("PRIVMSG %s :This is the list of available %s%s. Choose one with `!%s %s_number`.\n"
                      %(sender,t,(' for %s' %(self.destinations['destination'][self.hunters[sender]['selected']['destination']]['name'])) if t=='game' else 's',t,t))
        self.irc.send("PRIVMSG %s : === %s%s ===\n" %(sender,t.capitalize(),'' if t=='game' else 's'))
        for w in range(1,len(self.destinations[t])):
            if t=='game' and self.destinations[t][w]['planet']!=self.destinations['destination'][self.hunters[sender]['selected']['destination']]['name']:
                continue
            self.irc.send("PRIVMSG %s : %d) %s: %s  Difficulty: %s%s\n"
                     %(sender,w,'Name' if t=='game' else 'Location',self.destinations[t][w]['name'].capitalize(),self.destinations[t][w]['difficulty'],
                       ('  Frequency: %s%%%s' %(self.destinations[t][w]['frequency'],' (FREE!)' if self.destinations[t][w]['cost']=='0' else '')) if t=='game' else ''))

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

    ## List party stats
    def list_party(self,sender):
        trip=self.trips[self.hunters[sender]['trip']]
        off=4+max([len(member) for member in trip['party']])
        self.irc.send("PRIVMSG %s :PARTY STATS:\n" %(sender))
        self.irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                 %(sender,'Name',''.join(['%-12s' %(x) for x in self.properties])))
        for m in range(int(trip['size'])):
            if m<len(trip['party']):
                self.irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                 %(sender,trip['party'][m],''.join(['%-12d' %(x) for x in trip['properties'][trip['party'][m]]])))
            else:
                self.irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                     %(sender,'(empty)',''.join(['%-12d' %(0) for x in range(len(self.properties))])))
        
    ## List equipped items for status
    def list_personal(self,sender):
        self.irc.send("PRIVMSG %s :EQUIPMENT\n" %(sender))
        off=4+max([len(self.equipment[t][self.hunters[sender]['equipment'][t]]['name']) for t in self.hunters[sender]['equipment']])
        self.irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                 %(sender,'Name',''.join(['%-12s' %(x) for x in self.properties])))
        for t in ['weapons','tools','suits']:
            self.irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                     %(sender,self.equipment[t][self.hunters[sender]['equipment'][t]]['name'],''.join(['%-12s' %(str(p)) for p in self.equipment[t][self.hunters[sender]['equipment'][t]]['properties']])))
        self.irc.send("PRIVMSG %s : %-{offset}s\t%s\n".format(offset=off)
                 %(sender,'TOTAL',''.join(['%-12d' %(sum([self.equipment[t][self.hunters[sender]['equipment'][t]]['properties'][x] for t in ['weapons','tools','suits']])) for x in range(len(self.properties))])))

    ## Create codes for trips
    def gen_code(self,hunter):
        p=random.randint(0,len(hunter)-3)
        code=hunter[p:p+3]+str(random.randint(100000,999999))
        while code in self.trips:
            p=random.randint(0,len(hunter)-3)
            code=hunter[p:p+3]+str(random.randint(100000,999999))
        return code

    def relay_event(self,hunter,event_num,resolve=False,resolve_only=False):
        ## Add game tracking event check here to accomodate all creatures!
        ## (when the direct confrontation check fails)
        pass
        if not resolve_only:
            self.irc.send("PRIVMSG %s :-  Hunting %ss on %s: DAY %d\n"
                          %(hunter,self.destinations['game'][self.hunters[hunter]['selected']['game']]['name'].lower(),
                            self.destinations['destination'][self.hunters[hunter]['selected']['destination']]['name'],
                            event_num))
            self.relay_content(hunter,self.trips[self.hunters[hunter]['trip']]['events'][event_num])
        ## Relay actions/talk since current event here!!!
        pass
        if resolve or resolve_only:
            self.relay_content(hunter,self.trips[self.hunters[hunter]['trip']]['resolves'][event_num])

    ## Give commands for current trip step
    ## Commands are: (h)ide, (f)ight, (t)rack, (s)urvive, heal, forage
    ## Heal/forage are available whenever hide/fight/survive are NOT available
    def list_commands(self,hunter,relay=False):
        coms={'f':'fight','h':'hide','t':'track','s':'survive'}
        com_chars=self.trips[self.hunters[hunter]['trip']]['events'][-1].split('@')[-1]
        if com_chars.replace('t',''):
            commands=[coms[x] for x in com_chars]
        else:
            commands=[coms[x] for x in com_chars]+['heal','forage']
        if relay:
            self.irc.send("PRIVMSG %s : Available commands: !%s\n"
                          %(hunter,', !'.join(commands)))
        else:
            return commands

    ## Take hunter trip commands
    ## The last one automatically receives the event outcome and the next event text
    def trip_step(self,hunter,command=''):
        ## Hunter joins trip
        if command=='arrive':
            self.trips[self.hunters[hunter]['trip']]['party'].append(hunter)
            self.trips[self.hunters[hunter]['trip']]['states'][hunter]=0
            self.trips[self.hunters[hunter]['trip']]['properties'][hunter]=[sum([self.equipment[t][self.hunters[hunter]['equipment'][t]]['properties'][x] for t in ['weapons','tools','suits']]) for x in range(len(self.properties))]
            self.trips[self.hunters[hunter]['trip']]['supplies']+=self.trips[self.hunters[hunter]['trip']]['properties'][hunter][self.properties.index('Supplies')]
        ## Relay events for !trip&!start commands
        if command in ['arrive','']:
            state=self.trips[self.hunters[hunter]['trip']]['states'][hunter]
            if state<len(self.trips[self.hunters[hunter]['trip']]['events'])-1:
                self.relay_event(hunter,state,resolve=True)
                self.trips[self.hunters[hunter]['trip']]['states'][hunter]+=1
                self.relay_event(hunter,state+1)
            else:
                self.relay_event(hunter,state)
        ## Record actions
        if command and hunter not in self.trips[self.hunters[hunter]['trip']]['actions']:
            self.trips[self.hunters[hunter]['trip']]['actions'][hunter]=command
        ## Announce starting conditions after arrival
        if len(self.trips[self.hunters[hunter]['trip']]['events'])==1 and int(self.trips[self.hunters[hunter]['trip']]['size'])-len(self.trips[self.hunters[hunter]['trip']]['actions'])>0:
            self.irc.send("PRIVMSG %s : %d more hunters have to join before the trip can start.\n" %(hunter,int(self.trips[self.hunters[hunter]['trip']]['size'])-len(self.trips[self.hunters[hunter]['trip']]['actions'])))
            if not self.trips[self.hunters[hunter]['trip']]['force']:
                if 24-int((time.time()-self.trips[self.hunters[hunter]['trip']]['started_on'])/3600)<=25:
                    self.back_up(self.hunters[hunter]['trip'])
                    ## Test time delayed trip start!
                    pass
                    if command=='':
                        self.start_random(self.hunters[hunter]['trip'])
                else:
                    self.irc.send("PRIVMSG %s : This trip will also start automatically in %d hours!\n"
                                  %(hunter,24-int((time.time()-self.trips[self.hunters[hunter]['trip']]['started_on'])/3600)))
        ## Initiate event resolution when everyone has acted
        if len(self.trips[self.hunters[hunter]['trip']]['actions'])==int(self.trips[self.hunters[hunter]['trip']]['size']):
            self.resolve_event(self.hunters[hunter]['trip'])
            self.relay_event(hunter,self.trips[self.hunters[hunter]['trip']]['states'][hunter],resolve_only=True)
            self.trips[self.hunters[hunter]['trip']]['states'][hunter]+=1
            self.trips[self.hunters[hunter]['trip']]['actions']={}
            if not self.trips[self.hunters[hunter]['trip']]['events'][-1].startswith('ended'):
                self.select_event(self.hunters[hunter]['trip'])
            self.relay_event(hunter,self.trips[self.hunters[hunter]['trip']]['states'][hunter])
        ## Remove trip if all hunters have seen the ending
        if self.trips[self.hunters[hunter]['trip']]['events'][-1].startswith('ended'):
            code=self.hunters[hunter]['trip']
            self.return_hunter(hunter)
            for state in self.trips[code]['states'].values():
                if state<len(self.trips[code]['events'])-1:
                    break
            else:
                self.trips.pop(code)

    def start_random(self,trip_name):
        new_trip=self.gen_code(trip_name)
        self.trips[new_trip]=self.trips[trip_name].copy()
        self.trips.pop(trip_name)
        for member in self.trips[new_trip]['party']:
            ## Do only players
            if ' ' not in member:
                self.hunters[member]['trip']=new_trip
                self.orders[member]['code']=new_trip

    def resolve_event(self,code):
        ## Begin event chain
        if self.trips[code]['events'][-1].endswith('_arrival'):
            self.trips[code]['resolves'].append(self.trips[code]['events'][-1].replace('_arrival','_start'))
            return 0
        ## Calculate party action stats
        ## fight-sum; hide-average; survive-average
        ## heal-max+helpers;track-max+helpers;forage-%sum
        party_actions={'fight':[],'hide':[],'survive':[],
                     'heal':[],'track':[],'forage':[]}
        action_skills={'fight':'Firepower','hide':'Stealth','survive':'Resilience',
                     'heal':'Resilience','track':'Tracking','forage':'Supplies'}
        for member in self.trips[code]['actions']:
            party_actions[self.trips[code]['actions'][member]].append(self.trips[code]['properties'][member][self.properties.index(action_skills[self.trips[code]['actions'][member]])])
        party_actions['fight']=sum(party_actions['fight'])
        party_actions['hide']=sum(party_actions['hide'])/max([1,float(len(party_actions['hide']))])
        party_actions['survive']=sum(party_actions['survive'])/max([1,float(len(party_actions['survive']))])
        party_actions['heal']=max(party_actions['heal'])+len(party_actions['heal'])-1
        party_actions['track']=max(party_actions['track'])+len(party_actions['track'])-1
        party_actions['forage']=sum(party_actions['forage'])/100.
        ## Determine difficulty
        if event.split('_')[0].lower() in self.gamelist:
            difficulty=self.destinations['game'][self.gamelist.index(event.split('_')[0].lower())+1]['difficulty']
        else:
            difficulty=self.destinations['destination'][self.trips[code]['destination']]['difficulty']
        ## Do checks and determine resolve tag in sequence of danger
        ## Injure groups (last ones are always included if in danger):
        ## fight->survive|hide->track|heal|forage
        injure_group=[]
        resolve_tag=[]
        if party_actions['fight']:
            if random.random()<self.do_check(self.difficulties['fight'][difficulty],party_actions['fight'],'fight'):
                resolve_tag.append(self.trips[code]['events'][-1].replace('_event_','_success_').split('@')[0]+'@f')
            else:
                resolve_tag.append(self.trips[code]['events'][-1].replace('_event_','_fail_').split('@')[0]+'@f')
                injure_group.append('fight')
        else:
            for action in ['survive','hide']:
                if party_actions[action]:
                    if random.random()<self.do_check(self.difficulties[action][difficulty],party_actions[action],action):
                        resolve_tag.append(self.trips[code]['events'][-1].replace('_event_','_success_').split('@')[0]+'@%s' %(action[0]))
                    else:
                        resolve_tag.append(self.trips[code]['events'][-1].replace('_event_','_fail_').split('@')[0]+'@%s' %(action[0]))
                        injure_group.append(action)
        if party_actions['track']:
            if injure_group:
                injure_group.append('track')
            if random.random()<self.do_check(self.difficulties['track'][difficulty],party_actions['track'],'track'):
                resolve_tag.append('track_success')
                self.trips[code]['tracked'][event.split('_')[0]]=self.trips[code]['tracked'].get(event.split('_')[0],0)+1
        if party_actions['heal']:
        ## MULTIPLE RESOLVE TAGS!!!
        ## Register resolve tag
        self.trips[code]['resolves'].append(resolve_tag)
        ## Deal injuries to respective action group that failed
        pass
        ## Give out XP rewards here
        pass
        ## If event fails add injuries in trip
        ## If double injury - add hunter injury and end trip
        pass
        ## Lower supplies
        supply_chance=.2*len(self.trips[code]['party'])-party_actions['forage']
        if random.random()<supply_chance:
            self.trips[code]['supplies']-=1
        ## Check if trip ends here due to injuries/supply shortage/game caught
        ## content tags: ended_supplies/ended_injury/organized_game/random_game
        if self.trips[code]['supplies']<=0:
            self.trips[code]['events'].append('ended_supplies')
        pass

    ## Hunter has reached a trip ending
    def return_hunter(self,hunter):
        ## Check if player has a standing order and reset dest/game
        if hunter in self.orders and self.orders[hunter]['code']!=self.hunters[hunter]['trip']:
            self.hunters[hunter]['selected']['destination']=self.orders[hunter]['destination']
            self.hunters[hunter]['selected']['game']=self.orders[hunter]['game']
        else:
            self.hunters[hunter]['selected']['destination']=0
            self.hunters[hunter]['selected']['game']=0
            try:
                self.orders.pop(hunter)
            except KeyError:
                pass
        ## Clear trip
        self.hunters[hunter]['trip']=0

    ## Events are marked with the planet/game name (for planetary and game events)
    ## or terrain letter (for terrain) +"_event_". Possible actions start
    ## with @ and are listed at the end with a single letter. Actions are:
    ## (h)ide, (f)ight, (t)rack, (s)urvive
    ## (heal and forage are implied whenever h/f/s are not available!)
    def select_event(self,code):
        possible=[]
        games=[]
        for event in self.content:
            ## Take only event starts, not resolves/fails
            if '_event_' not in event:
                continue
            ## Add planet/terrain events
            if event.split('_')[0]==self.destinations['destination'][self.trips[code]['destination']]['name'] or\
               event.split('_')[0]==self.trips[code]['current_terrain']:
                possible+=[event]*5
            ## Add game(+3)/other events based on current terrain (/2 if no match)
            elif event.split('_')[0] in self.dest_games[self.destinations['destination'][self.trips[code]['destination']]['name']]:
                possible+=[event]*((self.game_freqs[event.split('_')[0]]['frequency']+self.trips[code]['tracked'].get(event.split('_')[0],0))/(1 if event.split('_')[0] in self.terr_games[self.trips[code]['current_terrain']] else 2))
                games.append(event)
                if event.split('_')[0]==self.destinations['game'][self.trips[code]['game']]['name']:
                    possible+=[event]*3
        ## Choose event at random. If 50% or more party members are injured reroll until
        ## a non-dangerous event is chosen (group tries to rest)!
        event=random.choice(possible)
        if len(self.trips[code]['injured'])*2>len(self.trips[code]['party']):
            while {'f','h','s'}&set(event.split('@')[-1]):
                event=random.choice(possible)
        ## Check to see if it's the actual creature or just tracks and
        ## make a dummy tracking event that changes the "tracked" trip property
        if event in games:
            if random.randint(1,10)>self.game_freqs[event.split('_')[0]]['frequency']+self.trips[code]['tracked'].get(event.split('_')[0],0):
                event='%s_event_tracking@t' %(event.split('_')[0])
        self.trips[code]['events'].append(event)
        ## Check to see if terrain has changed here, organized trips have a low
        ## chance to go to a non-game terrain and high chance to go back to a
        ## game terrain; random trips have random selection based on terrain
        ## sequence of planet
        terr_index=self.trips[code]['terrains'].index(self.trips[code]['current_terrain'])
        if self.trips[code]['force'] and\
           self.destinations['game'][self.trips[code]['game']]['name'] not in self.terr_games[self.trips[code]['current_terrain']]:
            self.trips[code]['current_terrain']=self.destinations['game'][self.trips[code]['game']]['terrains'][0]
        else:
            self.trips[code]['current_terrain']=random.choice(self.trips[code]['terrains'][max([0,terr_index-1]):terr_index+2])
        ## Automatically update state and select actions for back-up here!
        injured_players=sum([(1 if ' ' not in member else 0) for member in self.trips[code]['injured']])
        available_actions=event.split('@')[-1]
        for member in self.trips[code]['party']:
            ## Check if it's a back-up NPC
            if ' ' in member:
                ## Dangerous events
                if {'f','h','s'}&set(available_actions):
                    if 'f' in available_actions:
                        action='fight'
                    elif 's' in available_actions:
                        action='survive'
                    else:
                        action='hide'
                ## tracking events for uninjured tracker NPCs
                elif 't' in available_actions and 'tracker' in member\
                     and member not in self.trips[code]['injured']:
                    action='track'
                ## Help injured party members
                elif self.trips[code]['injured']:
                    action='heal'
                ## Else try to prolong trip
                else:
                    action='forage'
                self.trips[code]['actions'][member]=action
                self.trips[code]['states'][member]+=1
                

    ## Main skill check formula (Gompertz)
    def do_check(self,difficulty,skill,t):
        if t=='fight':
            p=3
        else:
            p=2
        return math.e**(-1*difficulty*math.e**(-1*0.5**p*skill))*100

    ## Fill party up to preset size with balanced GSC staff
    def back_up(self,code):
        if int(self.trips[code]['size'])==len(self.trips[code]['party']):
            return 0
        self.trips[code]['back-up']=int(self.trips[code]['size'])-len(self.trips[code]['party'])
        for hired in range(self.trips[code]['back-up']):
            party_supplies=self.trips[code]['supplies']
            party_tracking=max([self.trips[code]['properties'][m][self.properties.index('Tracking')] for m in self.trips[code]['properties']])
            ## Determine party supply needs
            if party_supplies<=0 or party_supplies*5./int(self.trips[code]['size'])<5:
                back_up="Gamorrean guide"
            ## Determine party tracking needs for organized trips
            elif self.trips[code]['force'] and self.do_check(code,self.destinations['game'][self.trips[code]['game']]['difficulty'],party_tracking,'Tracking')<33:
                back_up="Squib tracker"
            else:
                back_up_list=['Weequay hunter','Aleena hunter', 'Sakiyan hunter', 'Kubaz hunter']
                random.shuffle(back_up_list)
                for back_up in back_up_list:
                    if back_up not in self.trips[code]['party']:
                        break
            self.trips[code]['party'].append(back_up)
            self.trips[code]['actions'][back_up]='arrive'
            self.trips[code]['states'][back_up]=1
            self.trips[code]['properties'][back_up]=[sum([self.equipment[t][self.hunters[back_up]['equipment'][t]]['properties'][x] for t in ['weapons','tools','suits']]) for x in range(len(self.properties))]
            self.trips[code]['supplies']+=self.trips[code]['properties'][back_up][self.properties.index('Supplies')]

    def parse(self,buff,free_trip=False):
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
            administrative=False
            if sender==self.owner:
                administrative=True
                if '!shut-down' in message:
                    return "!shut-down"
                elif '!clear-my-trips' in message:
                    self.trips={}
                    self.orders={}
                    self.hunters[self.owner]['trip']=0
                    self.irc.send("PRIVMSG %s :Trip and order data cleared!\n" %(sender))
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
                ## Register paid trips for execution
                elif '!ticket ' in message:
                    args=message.split(':!ticket ')[-1].split()
                    if args[0] not in self.hunters:
                        self.irc.send("PRIVMSG %s :Hunter not found!\n" %(sender))
                    elif args[1].lower() not in self.destlist:
                        self.irc.send("PRIVMSG %s :Destination not found!\n" %(sender))
                    elif args[2].lower() not in self.gamelist:
                        self.irc.send("PRIVMSG %s :Game not found!\n" %(sender))
                    elif len(args)>3 and (not args[3].isdigit() or not int(args[3])):
                        self.irc.send("PRIVMSG %s :Party size error!\n" %(sender))
                    elif len(args)==5 and args[4].lower()!='back-up':
                        self.irc.send("PRIVMSG %s :Back-up argument error!\n" %(sender))
                    else:
                        code=self.gen_code(sender)
                        force=self.gen_code(sender)
                        destination=self.destlist.index(args[1].lower())+1
                        destname=self.destinations['destination'][destination]['name']
                        game=self.gamelist.index(args[2].lower())+1
                        self.orders[args[0]]={'destination':destination,'game':game,
                                              'organized':0,'back-up':False,
                                              'code':code,'force':force}
                        if args[3:4]:
                            self.orders[args[0]]['organized']=int(args[3])
                        if args[4:5]:
                            self.orders[args[0]]['back-up']=True
                        ## Generate trip
                        if self.orders[args[0]]['organized']:
                            self.trips[code]={'force':force,'party':[],'events':[destname+'_arrival'],
                                              'resolves':[],'states':{},'injured':{},
                                              'destination':destination,'game':game,
                                              'size':self.orders[args[0]]['organized'],
                                              'back-up':self.orders[args[0]]['back-up'],
                                              'started_on':0,'actions':{},'properties':{},
                                              'supplies':0,'terrains':self.destinations['destination'][destination]['terrains'].split('/'),
                                              'current_terrain':self.destinations['game'][game]['terrains'].split('/')[0],
                                              'tracked':{}}
                        elif 'random%d' %(destination) not in self.trips:
                            self.trips['random%d' %(destination)]={'force':0,'party':[],'events':[destname+'_arrival'],
                                              'resolves':[],'states':{},'injured':{},
                                              'destination':destination,'game':0,
                                              'size':int(self.destinations['destination'][destination]['difficulty']),
                                              'back-up':True,'started_on':0,'actions':{},'properties':{},
                                              'supplies':0,'terrains':self.destinations['destination'][destination]['terrains'].split('/'),
                                              'current_terrain':random.choice(self.destinations['destination'][destination]['terrains'].split('/')),
                                              'tracked':{}}
                        ## Set destination and game for the buyer to remove confusion
                        self.hunters[args[0]]['selected']['destination']=self.destlist.index(args[1].lower())+1
                        self.hunters[args[0]]['selected']['game']=self.gamelist.index(args[2].lower())+1
                        ## For automated ticket issuing on free trips
                        if free_trip:
                            return 0
                        self.irc.send("PRIVMSG %s :Ticket registered!\n" %(sender))
                else:
                    administrative=False
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
                else:
                    self.relay_content(sender,'help2')
            ## Handle hunter commands
            elif sender in self.hunters:
                ## Do trip event commands with event check
                if self.hunters[sender]['trip'] and message.split('!')[-1] in\
                   ['fight','hide','survive','track','heal','forage']:
                    command=message.split('!')[-1]
                    if command in self.list_commands(sender):
                        self.trip_step(sender,command)
                    else:
                        self.list_commands(sender,relay=True)
                ## describe trip step with !trip
                elif self.hunters[sender]['trip'] and message.endswith(':!trip'):
                    ## Random groups are time checked here and filled up with back-up
                    self.trip_step(sender)
                ## Start trip
                elif ':!start ' in message:
                    if 0 in self.hunters[sender]['equipment'].values():
                        self.irc.send("PRIVMSG %s :You cannot start a trip without selecting your equipment! Use !weapons, !tools, and !suits first.\n" %(sender))
                    else:
                        codes=message.split(':!start ')[-1].split()
                        ## organized trips
                        if codes[0] in self.trips:
                            ## Check for force codes and add back-up if requested
                            if self.hunters[sender]['trip']==codes[0]:
                                if codes[1:2] and codes[1]==self.trips[codes[0]]['force']:
                                    self.irc.send("PRIVMSG %s :You use the force code to start the trip ahead of time!\n" %(sender))
                                    if self.trips[codes[0]]['back-up']:
                                        self.back_up(codes[0])
                                    self.select_event(codes[0])
                                elif codes[1:2]:
                                    self.irc.send("PRIVMSG %s :Wrong force code!\n" %(sender))
                                else:
                                    self.irc.send("PRIVMSG %s :You have already started your trip! Use !trip to see your progress.\n" %(sender))
                            elif not self.hunters[sender]['trip']:
                                self.hunters[sender]['trip']=codes[0]
                                self.hunters[sender]['selected']['destination']=self.trips[codes[0]]['destination']
                                self.hunters[sender]['selected']['game']=self.trips[codes[0]]['game']
                                self.trip_step(sender,'arrive')
                            else:
                                self.irc.send("PRIVMSG %s :You have already started a trip! Use !trip to see your progress.\n" %(sender))
                        ## random trips
                        elif sender in self.orders and codes[0]==self.orders[sender]['code']:
                            trip_name='random%d' %(self.orders[sender]['destination'])
                            self.hunters[sender]['trip']=trip_name
                            ## Note trip start to count 24 hours
                            if not self.trips[trip_name]['started_on']:
                                self.trips[trip_name]['started_on']=time.time()
                            self.trip_step(sender,'arrive')
                            ## if party size is reached separate trip, change member trip names&codes
                            if len(self.trips[trip_name]['party'])==self.trips[trip_name]['size']:
                                self.start_random(trip_name)
                            if free_trip:
                                return 0
                        ## Handle free trips
                        elif codes[0].lower() in self.gamelist and self.destinations['game'][self.gamelist.index(codes[0].lower())+1]['cost']=='0':
                            ## Set ticket
                            m=":%s! PRIVMSG %s :!ticket %s %s %s\r\n" %(self.owner,self.botnick,sender,self.destinations['game'][self.gamelist.index(codes[0].lower())+1]['planet'],
                                                                        self.destinations['game'][self.gamelist.index(codes[0].lower())+1]['name'])
                            self.parse(m,free_trip=True)
                            ## Restart with new code
                            self.parse(message.replace(codes[0],self.orders[sender]['code']),free_trip=True)
                        else:
                            self.irc.send("PRIVMSG %s :Wrong trip code!\n" %(sender))
                ## Handle equipment commands
                elif not self.hunters[sender]['trip'] and (':!weapons ' in message or ':!tools ' in message or ':!suits ' in message \
                   or message.split(':!')[-1] in self.equipment.keys()):
                    t=message.split(':!')[-1].split(' ')[0]
                    selected=message.split(':!'+t)[-1].strip()
                    if selected:
                        if selected.isdigit() and int(selected) in self.equipment[t] and int(selected):
                            self.hunters[sender]['equipment'][t]=int(selected)
                            self.irc.send("PRIVMSG %s :You have selected the %s as your %s! You can freely change your %s selection between hunting trips. You can check your hunter stats with the !status command.\n" %(sender,self.equipment[t][int(selected)]['name'],t[:-1],t[:-1]))
                        else:
                            self.irc.send("PRIVMSG %s :This %s identification code is not in our database! Current codes range from 1 to %d.\n" %(sender,t[:-1],len(self.equipment[t])-1))
                    else:
                        self.list_equipment(sender,t)
                ## Handle destination & game commands
                elif not self.hunters[sender]['trip'] and (':!destination ' in message or ':!game ' in message \
                   or message.endswith('!destination') or message.endswith('!game')):
                    t=message.split(':!')[-1].split(' ')[0]
                    if t=='game' and not self.hunters[sender]['selected']['destination']:
                        self.irc.send("PRIVMSG %s : You have not selected a destination! Please use the !destination command first.\n" %(sender))
                    elif sender in self.orders:
                        self.irc.send("PRIVMSG %s : You have already ordered a trip! You cannot change your selection until the trip ends or is cancelled by company management. Contact %s for cancellation requests and a 50%% refund!\n" %(sender,self.owner_handle))
                    else:
                        selected=message.split(':!'+t)[-1].strip()
                        if selected:
                            if selected.isdigit() and int(selected) in self.destinations[t] and int(selected):
                                if  t=='game' and self.destinations[t][int(selected)]['planet']!=self.destinations['destination'][self.hunters[sender]['selected']['destination']]['name']:
                                    self.irc.send("PRIVMSG %s : This game identification code does not match your selected destination!\n" %(sender))
                                    self.list_destinations(sender,'game')
                                else:
                                    self.hunters[sender]['selected'][t]=int(selected)
                                    self.irc.send("PRIVMSG %s : You have selected %s as your %s!\n" %(sender,('the ' if t=='game' else '')+self.destinations[t][int(selected)]['name'],t))
                                    self.irc.send("PRIVMSG %s : %s\n" %(sender,self.destinations[t][int(selected)]['description']))
                                    ## Choosing a destination automatically clears game and lists the game menu
                                    if t=='destination':
                                        self.hunters[sender]['selected']['game']=0
                                        self.list_destinations(sender,'game')
                                    else:
                                        self.irc.send("PRIVMSG %s :Check !status for further instructions!\n" %(sender))
                            else:
                                self.irc.send("PRIVMSG %s :This %s identification code is not in our database! Current codes range from 1 to %d.\n" %(sender,t,len(self.destinations[t])-1))
                        else:
                            self.list_destinations(sender,t)
                ## Handle status requests
                elif message.endswith(':!status'):
                    self.irc.send("PRIVMSG %s :Hunter statistics for %s:\n" %(sender,sender))
                    if self.hunters[sender]['injured_on']:
                        injury_time=int((time.time()-self.hunters[sender]['injured_on'])/3600.)
                        if injury_time>=24:
                            injured='Cleared for participation'
                        else:
                            injured='Under surveilance! (%d hour%s remaining)' %(24-injury_time,'s' if injury_time<23 else '')
                    else:
                        injured='Cleared for participation'
                    self.irc.send("PRIVMSG %s :Hunting experience: %d   Medical status: %s\n" %(sender,self.hunters[sender]['exp'],injured))
                    sels="PRIVMSG %s :"
                    for d in ['destination','game']:
                        sels+="Selected %s: %s" %(d,self.destinations[d][self.hunters[sender]['selected'][d]]['name'] if self.hunters[sender]['selected'][d] else 'None')
                        if d=='destination':
                            sels+='    '
                        else:
                            sels+='\n'
                    self.irc.send(sels %(sender))
                    ## Give hunter or party stats
                    if self.hunters[sender]['trip']:
                        self.list_party(sender)
                    else:
                        self.list_personal(sender)
                    ## Give free code or price with instructions if game is selected
                    ## or codes if it's already paid
                    if self.hunters[sender]['selected']['game']:
                        ## Free trips
                        if self.destinations['game'][self.hunters[sender]['selected']['game']]['cost']=='0' and not self.hunters[sender]['trip']:
                            code=self.destinations['game'][self.hunters[sender]['selected']['game']]['name']
                            self.irc.send("PRIVMSG %s :Free trip confirmed, use `!start %s` to travel to your destination! Depending on the interest in your chosen location there may be a delay of up to 24 hours until the start of the actual trip!\n" %(sender,code))
                        ## Unpaid trips
                        elif sender not in self.orders and not self.hunters[sender]['trip']:
                            # Trip cost is determined by planet and creature
                            dest_cost=int(self.destinations['destination'][self.hunters[sender]['selected']['destination']]['cost'])
                            game_cost=int(self.destinations['game'][self.hunters[sender]['selected']['game']]['cost'])
                            self.irc.send("PRIVMSG %s :Ticket costs for the selected trip:\n" %(sender))
                            self.irc.send("PRIVMSG %s :  %d credits for a single ticket (random groups starting every 24 hours)\n" %(sender,dest_cost+2*game_cost))
                            self.irc.send("PRIVMSG %s :  %d credits PER PARTY SLOT for organized groups WITHOUT back-up.\n" %(sender,dest_cost))
                            self.irc.send("PRIVMSG %s :  %d credits PER PARTY SLOT for organized groups WITH GSC back-up.\n" %(sender,dest_cost+game_cost))
                            self.irc.send("PRIVMSG %s :Please transfer funds and DM trip information (selected destination and game, plus group size and back-up requested (Yes/No) for organized groups) to %s and check !status later for your activation codes!\n"
                                          %(sender,self.owner_handle))
                        ## Paid trips
                        elif not self.hunters[sender]['trip']:
                            self.irc.send("PRIVMSG %s :Congratulations, your order has been processed!\n" %(sender))
                            self.irc.send("PRIVMSG %s :Start code: %s\n" %(sender,self.orders[sender]['code']))
                            if self.orders[sender]['organized']:
                                self.irc.send("PRIVMSG %s :Give the start code to all party members! The trip will start when at least %d hunters have used the `!start start_code` command!\n" %(sender,self.orders[sender]['organized']))
                                self.irc.send("PRIVMSG %s :Force code: %s\n" %(sender,self.orders[sender]['force']))
                                self.irc.send("PRIVMSG %s :Use the `!force force_code` command if some of your party members are not available and you want to begin the trip. Once you do this no one else will be able to join!\n" %(sender))
                                if self.orders[sender]['back-up']:
                                    self.irc.send("PRIVMSG %s :If you use the force code your group will be complemented with hunters from our staff to the size of %d!\n" %(sender,self.orders[sender]['organized']))
                            else:
                                self.irc.send("PRIVMSG %s :You can now use the `!start start_code` command to travel to your destination. Depending on the interest in your chosen location there may be a delay of up to 24 hours until the start of the actual trip!\n" %(sender))
                        ## During trips
                        else:
                            self.irc.send("PRIVMSG %s :Current trip length: %d days\n" %(sender,len(self.trips[self.hunters[sender]['trip']]['events'])))
                            self.irc.send("PRIVMSG %s :Party supplies will last for approximately %d more days!\n"
                                          %(sender,int(self.trips[self.hunters[sender]['trip']]['supplies']*5./int(self.trips[self.hunters[sender]['trip']]['size']))))
                elif not administrative:
                    self.irc.send("PRIVMSG %s :This is not a recognized command, try !help to see available commands.\r\n" %(sender))
                self.refresh_hunters()
            elif not administrative:
                self.irc.send("PRIVMSG %s :You are not registered as a hunter with our company! Please use !sign-up to register or !help to learn more about us.\r\n" %(sender))
        ## handle channel messages?
        elif "PRIVMSG %s" %(self.channel) in message:
            print message
        return buff.split('\r\n',1)[1]

bot=Safari_bot()
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
