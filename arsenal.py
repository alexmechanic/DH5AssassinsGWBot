#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#

import datetime
from icons import *

class Arsenal():
    check_id = None
    progress = 0
    is_fired = False
    # dict with lists formatted [name, nick, value, count, is_fired]
    done_users = {}

    def __init__(self):
        self.progress = 0
        self.is_fired = False
        self.done_users = {}

    def SetMessageID(self, message_id):
        # print("Set Arsenal ID: " + str(message_id))
        self.check_id = message_id

    def GetProgress(self):
        return self.progress

    def GetHeader(self):
        iteration = self.progress
        total = 120
        length = 17
        # form progress bar
        percent = iteration if iteration <= 120 else 120
        filledLength = int(length * percent // total)
        bar = '█' * filledLength + '--' * (length - filledLength)
        text =  "📦 Прогресс арсенала: *%s/120*\n" % percent
        text += "|%s|\n" % bar
        return text

    def GetProgressText(self):
        text = self.GetHeader()
        # list done users
        if self.progress >= 120:
            now = datetime.datetime.now()
            text += "🔥 %0.2d:%0.2d ГОРИТ! 🔥\n" % (now.hour, now.minute)
        text += "\n"*(len(self.done_users) != 0)
        for user in self.done_users:
            name = self.done_users[user][0]
            nick = self.done_users[user][1]
            inc = self.done_users[user][2]
            count = self.done_users[user][3]
            is_fired = self.done_users[user][4]
            text += ICON_RAGE*is_fired
            text += (" *+%d*" % inc)
            text += " [%s" % name
            if nick != None:
                text += " (%s)" % nick
            text += "](tg://user?id=%d) (x%d)\n" % (user, count)
        return text

    def Increment(self, user, value):
        userid = user[0]
        nick = user[1]
        name = user[2]
        arsValue = value.replace(ARS_CALLBACK_PREFIX, "")
        inc = 0
        user_fired = False # this variable is needed in order to count ars value for user even if ars is already fired now
        user_newcount = 1
        if arsValue == "Cancel":
            if userid in self.done_users:
                self.UndoIncrement(user)
                return True
            return False
        if arsValue == "Full":
            if not self.is_fired:
                user_fired = True
                inc = 120 - self.progress
            else:
                user_newcount = 0
        else:
            inc = int(arsValue)
            if inc > 14:
                user_newcount = 3
        if user_fired:
            self.progress = 120
        else:
            self.progress += inc
        if self.progress >= 120:
            user_fired = True
            self.is_fired = True
        user_oldvalue = 0
        user_oldcount = 0
        if userid in self.done_users:
            user_oldvalue = self.done_users[userid][2]
            user_oldcount = self.done_users[userid][3]
        user_record = [name, nick, user_oldvalue+inc, user_oldcount+user_newcount, user_fired]
        self.done_users[userid] = user_record
        return True

    # undo arsenal result for user if user made mistake
    def UndoIncrement(self, user):
        userid = user[0]
        dec = self.done_users[userid][2]
        del self.done_users[userid]
        self.progress -= dec
        if self.progress < 120:
            self.is_fired = False
