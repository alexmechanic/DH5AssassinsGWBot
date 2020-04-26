#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class representing arsenal check
#

import datetime
from icons import *
from callbacks import ARS_CALLBACK_PREFIX
from logger import get_logger

log = get_logger("bot." + __name__)

class Arsenal():
    check_id = None
    progress = 0
    is_fired = False
    rage_time = None
    # dict with lists formatted [name, nick, value, count, is_fired]
    done_users = {}
    is_postponed = False

    def __init__(self):
        self.progress = 0
        self.is_fired = False
        self.done_users = {}
        self.rage_time = None
        self.is_postponed = False
        log.info("New arsenal check created")

    def SetMessageID(self, message_id):
        self.check_id = message_id
        log.debug("Set inline message_id: %s" % self.check_id)

    def SetRage(self, time):
        self.rage_time = time

    def GetProgress(self):
        return self.progress

    def DoEndArsenal(self):
        self.is_postponed = True
        log.info("Arsenal check stopped")

    # Notify participated users if arsenal has been fired
    def CheckNotifyIfFired(self, battle, bot, warchat_id):
        if self.is_fired:
            # get active users from battle check
            activeUsers = battle.GetActiveUsersID()
            for user in self.done_users:
                activeUsers.add(user)
            log.debug(activeUsers)
            now = datetime.datetime.now()
            text = ICON_RAGE+" %0.2d:%0.2d ГОРИТ!" % (now.hour, now.minute)
            for user in activeUsers:
                now = datetime.datetime.now()
                bot.send_message(user, text)
            if warchat_id:
                notification = bot.send_message(warchat_id, text)
                bot.pin_chat_message(notification.chat.id, notification.message_id, disable_notification=False)
                log.debug("Arsenal status notification posted")
            else:
                log.error("War chat_id is not set, cannot post arsenal status notification!")


    def GetHeader(self):
        iteration = self.progress
        total = 120
        length = 17
        # form progress bar
        percent = iteration if iteration <= 120 else 120
        filledLength = int(length * percent // total)
        bar = '█' * filledLength + '--' * (length - filledLength)
        text =  ICON_ARS+" Прогресс арсенала: *%s/120*\n" % percent
        if self.rage_time:
            text += "*Ярость в %s*\n" % self.rage_time
        text += "|%s|\n" % bar
        return text

    def GetText(self):
        text = self.GetHeader()
        # list done users
        if self.progress >= 120:
            now = datetime.datetime.now()
            text += ICON_RAGE+" %0.2d:%0.2d ГОРИТ! " % (now.hour, now.minute) +ICON_RAGE+"\n"
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
        log.info("User %d (%s %s) voted for %s" % (*user, arsValue))
        if arsValue == "Cancel":
            if userid in self.done_users:
                self.UndoIncrement(user)
                return True
            log.error("Vote failed - user already reverted his votes")
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
            self.is_postponed = True
        else:
            self.progress += inc
        if self.progress >= 120:
            user_fired = True
            self.is_fired = True
            self.is_postponed = True
        user_oldvalue = 0
        user_oldcount = 0
        if userid in self.done_users:
            user_oldvalue = self.done_users[userid][2]
            user_oldcount = self.done_users[userid][3]
        user_record = [name, nick, user_oldvalue+inc, user_oldcount+user_newcount, user_fired]
        log.debug("User %d (%s %s) total impact: %s" % (*user, str(user_record[2:])))
        self.done_users[userid] = user_record
        log.info("Vote successful")
        return True

    # undo arsenal result for user if user made mistake
    def UndoIncrement(self, user):
        userid = user[0]
        dec = self.done_users[userid][2]
        log.debug("User %d (%s %s) reverting all his votes" % (user[0], user[1], user[2]))
        del self.done_users[userid]
        self.progress -= dec
        if self.progress < 120:
            log.warning("Rage might've been reverted!")
            self.is_fired = False
            self.is_postponed = False
            for user in self.done_users:
                self.done_users[user][4] = False
        log.info("Revert successful")
