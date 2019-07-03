#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#

from icons import *

class WarPreCheck():
    check_id = None
    is_postponed = False
    friday = {}
    saturday = {}
    sunday = {}
    thinking = {}
    cancels = {}

    def __init__(self):
        self.friday = {}
        self.saturday = {}
        self.sunday = {}
        self.thinking = {}
        self.cancels = {}

    def SetMessageID(self, message_id):
        # print("Set ID: " + str(message_id))
        self.check_id = message_id

    def DoEndPrecheck(self):
        self.is_postponed = True

    def GetHeader(self):
        return "📝 *Чек перед ВГ:*\n"

    def GetText(self):
        text = self.GetHeader()
        text += "🛑 Голование завершено 🛑\n" * self.is_postponed

        if len(self.friday) > 0:
            text += "\n" + "🗓 *Пятница (%d):*\n" % len(self.friday)
        for user in self.friday:
            text += "👤 [%s" % self.friday[user][0]
            if self.friday[user][1] != None:
                text += " (%s)" % self.friday[user][1]
            text += "](tg://user?id=%d)\n" % user

        if len(self.saturday) > 0:
            text += "\n" + "🗓 *Суббота (%d):*\n" % len(self.saturday)
        for user in self.saturday:
            text += "👤 [%s" % self.saturday[user][0]
            if self.saturday[user][1] != None:
                text += " (%s)" % self.saturday[user][1]
            text += "](tg://user?id=%d)\n" % user

        if len(self.sunday) > 0:
            text += "\n" + "🗓 *Воскресенье (%d):*\n" % len(self.sunday)
        for user in self.sunday:
            text += "👤 [%s" % self.sunday[user][0]
            if self.sunday[user][1] != None:
                text += " (%s)" % self.sunday[user][1]
            text += "](tg://user?id=%d)\n" % user

        if len(self.thinking) > 0:
            text += "\n" + "*Думают (%d):*\n" % len(self.thinking)
        for user in self.thinking:
            text += ICON_THINK + " [%s" % self.thinking[user][0]
            if self.thinking[user][1] != None:
                text += " (%s)" % self.thinking[user][1]
            text += "](tg://user?id=%d)\n" % user

        if len(self.cancels) > 0:
            text += "\n" + "*Не идут (%d):*\n" % len(self.cancels)
        for user in self.cancels:
            text += ICON_CANCEL + " [%s" % self.cancels[user][0]
            if self.cancels[user][1] != None:
                text += " (%s)" % self.cancels[user][1]
            text += "](tg://user?id=%d)\n" % user

        return text

    def GetVotedText(self, user, action):
        text = "Вы "
        if action == PRECHECK_FR_CALLBACK:
            if user[0] not in self.friday:
                text += "не "
            return text + "участвуете в пятницу"
        if action == PRECHECK_SAT_CALLBACK:
            if user[0] not in self.saturday:
                text += "не "
            return text + "участвуете в субботу"
        if action == PRECHECK_SUN_CALLBACK:
            if user[0] not in self.sunday:
                text += "не "
            return text + "участвуете в воскресенье"
        elif action == PRECHECK_FULL_CALLBACK:
            return text + "участвуете все дни"
        elif action == PRECHECK_THINK_CALLBACK:
            return text + "еще не решили. Постарайтесь определиться к началу ВГ!"
        elif action == PRECHECK_CANCEL_CALLBACK:
            return text + "не будете участвовать в этой ВГ. Жаль"

    def CheckUser(self, user, action):
        ret = True
        if action == PRECHECK_FR_CALLBACK:
            ret = self.SetFriday(user)
        if action == PRECHECK_SAT_CALLBACK:
            ret = self.SetSaturday(user)
        if action == PRECHECK_SUN_CALLBACK:
            ret = self.SetSunday(user)
        elif action == PRECHECK_FULL_CALLBACK:
            ret = self.SetFull(user)
        elif action == PRECHECK_THINK_CALLBACK:
            ret = self.SetThinking(user)
        elif action == PRECHECK_CANCEL_CALLBACK:
            ret = self.SetCancel(user)
        return ret

    def SetFriday(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        if userid in self.friday: # if already checked - uncheck
            del self.friday[userid]
        else: # if not - check
            self.friday[userid] = [name, nick]
        # remove user from other lists
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
        return True

    def SetSaturday(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        if userid in self.saturday: # if already checked - uncheck
            del self.saturday[userid]
        else: # if not - check
            self.saturday[userid] = [name, nick]
        # remove user from other lists
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
        return True

    def SetSunday(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        if userid in self.sunday: # if already checked - uncheck
            del self.sunday[userid]
        else: # if not - check
            self.sunday[userid] = [name, nick]
        # remove user from other lists
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
        return True

    def SetFull(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        if userid not in self.friday:
            self.friday[userid] = [name, nick]
        if userid not in self.saturday:
            self.saturday[userid] = [name, nick]
        if userid not in self.sunday:
            self.sunday[userid] = [name, nick]
        # remove user from other lists
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
        return True

    def SetThinking(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.thinking:
            if userid == user: # cannot think more than once
                return False
        # remove user from other lists
        if userid in self.friday: del self.friday[userid]
        if userid in self.saturday: del self.saturday[userid]
        if userid in self.sunday: del self.sunday[userid]
        if userid in self.cancels: del self.cancels[userid]
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
        if userid in self.friday: del self.friday[userid]
        if userid in self.saturday: del self.saturday[userid]
        if userid in self.sunday: del self.sunday[userid]
        if userid in self.thinking: del self.thinking[userid]
        self.cancels[userid] = [name, nick]
        return True
