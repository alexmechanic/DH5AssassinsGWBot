#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
#

import datetime

class Battle():
    check_id = None
    time = {"check": None, "start": None, "end": None}
    is_started = False
    is_postponed = False
    checks = {}
    rages = {}
    cancels = {}
    thinking = {}
    arsenals = {}
    lates = {}

    def __init__(self, check, start):
        now = datetime.datetime.now()
        self.time["check"] = now.replace(hour=int(check[:2]), minute=int(check[3:]))
        self.time["start"] = now.replace(hour=int(start[:2]), minute=int(start[3:]))
        self.checks = {}
        self.rages = {}
        self.cancels = {}
        self.thinking = {}
        self.arsenals = {}
        self.lates = {}

    def SetMessageID(self, message_id):
        print("Set ID: " + str(message_id))
        self.check_id = message_id

    def DoStartBattle(self):
        now = datetime.datetime.now()
        self.time["start"] = datetime.datetime.now()
        self.is_started = True

    def DoEndBattle(self):
        now = datetime.datetime.now()
        self.time["end"] = datetime.datetime.now()
        self.is_postponed = True

    def GetText(self):
        text = "*Чек:* %0.2d:%0.2d, *Бой:* %.2d:%.2d" \
                % (self.time["check"].hour, self.time["check"].minute, self.time["start"].hour, self.time["start"].minute)
        text += "\n❗ Бой начался ❗" * (self.is_started and not self.is_postponed)
        if self.is_postponed:
            text += "\n🛑 Бой завершился в %0.2d:%0.2d 🛑" % (self.time["end"].hour, self.time["end"].minute)

        text += ("\n\n" + "*%d идут:*\n" % (len(self.checks) + len(self.rages))) * (len(self.checks) + len(self.rages))
        for user in self.checks:
            text += "✅ [%s (%s)](tg://user?id=%d)\n" % (self.checks[user][0], self.checks[user][1], user)
        for user in self.rages:
            text += "🔥 [%s (%s)](tg://user?id=%d)\n" % (self.rages[user][0], self.rages[user][1], user)

        text += ("\n\n" + "* %d только в арс:*\n" % len(self.arsenals)) * len(self.arsenals)
        for user in self.arsenals:
            text += "📦 [%s (%s)](tg://user?id=%d)\n" % (self.arsenals[user][0], self.arsenals[user][1], user)

        text += ("\n\n" + "*%d думают:*\n" % len(self.thinking)) * len(self.thinking)
        for user in self.thinking:
            text += "💤 [%s (%s)](tg://user?id=%d)\n" % (self.thinking[user][0], self.thinking[user][1], user)

        text += ("\n\n" + "* %d передумали:*\n" % len(self.cancels)) * len(self.cancels)
        for user in self.cancels:
            text += "❌ [%s (%s)](tg://user?id=%d)\n" % (self.cancels[user][0], self.cancels[user][1], user)

        text += ("\n\n" + "* %d опоздали:*\n" % len(self.lates)) * len(self.lates)
        for user in self.lates:
            text += "⏰ [%s (%s)](tg://user?id=%d)\n" % (self.lates[user][0], self.lates[user][1], user)
        return text

    def CheckUser(self, user, action):
        ret = True
        if action == "✅":
            ret = self.SetCheck(user)
        if action == "🔥":
            ret = self.SetRageOnly(user)
        elif action == "📦":
            ret = self.SetArsenalOnly(user)
        elif action == "💤":
            ret = self.SetThinking(user)
        elif action == "❌":
            ret = self.SetCancel(user)
        elif action == "⏰":
            ret = self.SetLate(user)
        return ret

    def SetCheck(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.checks:
            if userid == user: # cannot check more than once
                return False
        # remove user from other lists
        if (userid in self.rages): del self.rages[userid]
        if (userid in self.arsenals): del self.arsenals[userid]
        if (userid in self.thinking): del self.thinking[userid]
        if (userid in self.cancels): del self.cancels[userid]
        self.checks[userid] = [name, nick]
        return True

    def SetRageOnly(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.rages:
            if userid == user: # cannot check more than once
                return False
        # remove user from other lists
        if (userid in self.checks): del self.checks[userid]
        if (userid in self.arsenals): del self.arsenals[userid]
        if (userid in self.thinking): del self.thinking[userid]
        if (userid in self.cancels): del self.cancels[userid]
        self.rages[userid] = [name, nick]
        return True

    def SetArsenalOnly(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.arsenals:
            if userid == user: # cannot check more than once
                return False
        # remove user from other lists
        if (userid in self.checks): del self.checks[userid]
        if (userid in self.rages): del self.rages[userid]
        if (userid in self.thinking): del self.thinking[userid]
        if (userid in self.cancels): del self.cancels[userid]
        self.arsenals[userid] = [name, nick]
        return True

    def SetThinking(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.thinking:
            if userid == user: # cannot think more than once
                return False
        # remove user from other lists
        if (userid in self.checks): del self.checks[userid]
        if (userid in self.rages): del self.rages[userid]
        if (userid in self.arsenals): del self.arsenals[userid]
        if (userid in self.cancels): del self.cancels[userid]
        self.thinking[userid] = [name, nick]
        return True

    def SetCancel(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.cancels:
            if userid == user: # cannot cancel more than once
                return False
        # remove user from other lists
        if (userid in self.checks): del self.checks[userid]
        if (userid in self.rages): del self.rages[userid]
        if (userid in self.arsenals): del self.arsenals[userid]
        if (userid in self.thinking): del self.thinking[userid]
        self.cancels[userid] = [name, nick]
        return True

    def SetLate(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.lates:
            if userid == user: # cannot check late more than once
                return False
        if  userid in [self.checks, self.rages, self.arsenals, self.thinking]:
            return False
        self.lates[userid] = [name, nick]
        return True
