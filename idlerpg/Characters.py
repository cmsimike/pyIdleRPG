# -*- coding: utf-8 -*-
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=80:
"""
TEST check on __init__ if the player is already connected.
TODO load when needed some character ifno
TODO load important info such as: identify chains

schema of the code:
Character:
    equipment
    body

    __init__(cname, chost, cequipment, cbody)
    updateBodyPart(bodyPartId, +/-Float, Collection)
    updateEquipment(equipmentKey, +/-Int, Name=None, Collection)
"""

from hashlib import sha1
from types import *
from time import time

def validateEmail(email):
    import re
    if len(email) > 6:
        if (re.match('^[a-zA-Z0-9._%-+]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$',
            email) != None):
            return 1
    return 0

class Character:
    _equipmentKeys = ['leggings', 'tunic', 'weapon', 'ring', 'shield',
                     'amulet', 'helm', 'charm', 'boots', 'gloves']
    #Not used yet
    _bodyPartKeys = ['hips', 'vagina', 'cock', 'breasts', 'tallness', 'hair',
                     'face', 'ear', 'antennae', 'horns', 'wings', 'lowerbody']


    def __init__(self, nickname, hostname, username, myCollection,
                 password=None, cname=None):
        self.empty = True
        self.nickname = nickname
        self.hostname = hostname
        self.equipment = {}
        self._myCollection = myCollection

        if cname is None:
            cdata = self._myCollection.find_one({'nickname': self.nickname,
                                                 'hostname': self.hostname,
                                                 'username': self.username,
                                                 'loggedin': True})
            if len(cdata) > 0:
                self.empty = False
                self.load(cdata,'autoload')
        else:
            self.loggin_in(cname, password)


    def loggin_in(self, character_name, password):
        cdata = self._myCollection.find_one({
            'character_name': character_name,
            'password': sha1(password)
            })

        if len(cdata) > 0:
            self.empty = False
            self.load(cdata, 'loggin')
            return 1
        return -1

    def load(self, characterData, method):
        """
        Load userdata in memory
        """
        if method == 'loggin':
            toUpdate = {}
            if characterData['nickname'] is not self.nickname:
                toUpdate.update({'nickname': self.nickname})
                characterData['nickname'] = self.nickname
            if characterData['hostname'] is not self.hostname:
                toUpdate.update({'hostname': self.hostname})
                characterData['hostname'] = self.hostname
            if len(toUpdate) > 0:
                self._myCollection.update({'_id': characterData['_id']},
                                    {'$set': toUpdate})

        self._myId = characterData['_id']
        # TODO verify if loading the equipment in memory is really needed
        for key in self._equipmentKeys:
            if not characterData['equipment'].has_key(key):
                pass
            val = characterData['equipment'][key]
            self.equipment.update({key: val})

        self.characterName = characterData['character_name']
        self.registeredat = characterData['registeredat']
        self.idle_time = characterData['idle_time']
        self.total_idle = characterData['total_idle']
        self.level = characterData['level']
        self.empty = False
        return 1

    def unload(self):
        """
        Commit everything into the database
        """
        data = {'total_idle': self.total_idle,
                'level': self.level,
                'idle_time': self.idle_time}

        self._myCollection.update({'_id': self._myId},
                {'$set': data})
        return 1

    def createNew(self, myCollection, character_name, character_class,
                        nickname, hostname password, email, gender=0,
                        align=0):
        if self.empty is not True:
            return -1

        # Do not use email if
        if validateEmail(email) < 1:
            email=None

        # find twins
        haveTwin = myCollection.find_one({'character_name': character_name})
        if haveTwin is not None:
            return 0

        from os.path import exists
        from hashlib import sha1
        import yaml
        import random
        import time

        if len(int(gender))>1 or (gender is 0 or gender is not in [1,2]):
            gender = random.randrange(1,2)

        password = sha1(password).hexdigest()

        with file('character.yaml','r') as stream:
            myCharacter = yaml.load(stream)

        myCharacter.save({'character_name': character_name,
                            'nickname': nickname,
                            'hostname': hostname,
                            'password': password,
                            'email': email,
                            'gender': gender,
                            'class': chararcter_class,
                            'level': 1,
                            'registeredat': time.time(),
                            'ttl': self._ttl(1),
                            'alignment': 0 if align not in [-1,0,1] else align
                            })
        self._myId = myCollection.insert(myCharacter)
        return 1

    def increaseIdleTime(self, ittl):
        cttl = self.getTTL()
        if cttl['ttl'] >= self.idle_time+5:
            # LEVEL UP
            self.levelUp()
        else:
            self._myCollection.update('_id': self._myId,
                    {$inc: {'idle_time': ittl}})
            self.idle_time+=ittl

    def getTTL(self, level=None):
        """
        return the Time To Level for a specified level or return the
        current ttl from the database.
        """
        if level is None:
            return self._myCollection.findone({'_id': self._myId}, {'ttl': 1})
        else:
            return int(600*(1.16**level))

    def getEquipmentSum(self):
        data = self._myCollection().find(
                {'_id': self._myId},
                {'_id': 0, 'equipment': 1})
        esum = sum([item['power'] for item in data['equipment'].itervalues()])
        return esum

    def levelUp(self):
        self.level+= 1
        self._myCollection.update({'_id': self.myId},
                                   {'$inc': {'level': 1
                                             'total_idle': self.idle_time},
                                    '$set': {'idle_time': 0,
                                             'ttl': self.getTTL(self.level)}}
                                  )
        self.idle_time = 0
        return 1

    def rename(self, newName):
        if self.empty:
            return 0
        self._myCollection.update({'_id': self.myId},
                                   {'$set': {'character_name': newName}})
        self.characterName = newName

    def penalty(self, penalty=0, messagelenght=None):
        """
        increment the time to idle to next level by M*(1.4**LEVEL)
        """
        if self.empty:
            return 0
        if messagelenght is not None and int(messagelenght) > 0:
            penalty = int(messagelenght)

        increase = int(penalty) * (1.14**int(self.level))
        self._myCollection.update({'character_name': self.characterName},
                                   {'$inc': {'ttl': increase})
        return penalty

    def P(self, modifier):
        """
        alias for self.penalty
        """
        return self.penalty(penalty=modifier)

    def updateBodypart(self, bodypID, value):
        mname = '__update_' + bodypID
        if hasattr(self, mname):
            o = getattr(self, mname)(value)
        else:
            pass

    def updateEquipment(self, equipKey, value, name=None):
        updateValue = {'equipment.'+equipKey: {'power': value, 'name': name}}
        self._myCollection.update({'character_name': self.characterName,
                                   'equipment.'+equipKey+'.power': {'$lt': value}},
                                  updateValue,
                                  false)
        # TODO: Checking the Outcome of an Update Request
        # http://www.mongodb.org/display/DOCS/Updating#Updating-CheckingtheOutcomeofanUpdateRequest
        self.equipment[equipKey] = (value, name)


    def get_characterName(self):
        return self.characterName

    def get_nickname(self):
        return self.nickname

    def get_hostname(self):
        return self.user_host

    def get_level(self):
        return self.level

    def get_ttl(self):
        """
        return the time to level. Alias of getTTL
        """
        return self.getTTL()

    def get_alignment(self):
        pass

    def get_equipment(self, key=None):
        if key is not None:
            return self.equipment.get(key, 0)
        else:
            return self.equipment.items()

    def set_alignment(self, align):
        self._myCollection.update({'_id': self.myId}, {'align': align})
