#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#

import datetime
from icons import *
from callbacks import *
from logger import get_logger

log = get_logger("bot." + __name__)

class Battle():
    check_id = None
    time = {"check": None, "start": None, "end": None}
    is_started = False
    is_postponed = False
    # dicts with lists formatted [name, nick]
    checks = {}
    rages = {}
    fasts = {}
    arsenals = {}
    thinking = {}
    cancels = {}
    lates = {}

    def __init__(self, check, start):
        now = datetime.datetime.now()
        self.time["check"] = now.replace(hour=int(check[:2]), minute=int(check[3:]))
        self.time["start"] = now.replace(hour=int(start[:2]), minute=int(start[3:]))
        self.checks = {}
        self.rages = {}
        self.fasts = {}
        self.arsenals = {}
        self.thinking = {}
        self.cancels = {}
        self.lates = {}
        self.is_started = False
        self.is_postponed = False
        log.info("New battle created (%0.2d:%0.2d / %0.2d:%0.2d)" \
                % (self.time["check"].hour, self.time["check"].minute, self.time["start"].hour, self.time["start"].minute))

    def SetMessageID(self, message_id):
        self.check_id = message_id
        log.debug("Set inline message_id: %s" % self.check_id)

    def DoStartBattle(self):
        now = datetime.datetime.now()
        self.time["start"] = datetime.datetime.now()
        self.is_started = True
        log.warning("Battle started at %0.2d:%0.2d" % (self.time["start"].hour, self.time["start"].minute))

    def DoEndBattle(self):
        now = datetime.datetime.now()
        self.time["end"] = datetime.datetime.now()
        self.is_postponed = True
        log.warning("Battle ended at %0.2d:%0.2d" % (self.time["end"].hour, self.time["end"].minute))

    def GetHeader(self):
        text = "⚔️ *Чек:* %0.2d:%0.2d, *Бой:* %.2d:%.2d\n" \
                % (self.time["check"].hour, self.time["check"].minute, self.time["start"].hour, self.time["start"].minute)
        return text

    def GetText(self):
        text = self.GetHeader()
        text += "❗ Бой начался ❗\n" * (self.is_started and not self.is_postponed)
        if self.is_postponed:
            text += "🛑 Бой"
            if self.is_started:
                text += " завершился "
            else:
                text += " отменен "
            text += "в %0.2d:%0.2d 🛑\n" % (self.time["end"].hour, self.time["end"].minute)

        if len(self.checks) + len(self.rages) + len(self.fasts) > 0:
            text += "\n" + "*%d идут:*\n" % (len(self.checks) + len(self.rages) + len(self.fasts))
        for user in self.checks:
            text += ICON_CHECK + " [%s" % self.checks[user][0]
            if self.checks[user][1] != None:
                text += " (%s)" % self.checks[user][1]
            text += "](tg://user?id=%d)\n" % user
        for user in self.rages:
            text += ICON_RAGE + " [%s" % self.rages[user][0]
            if self.rages[user][1] != None:
                text += " (%s)" % self.rages[user][1]
            text += "](tg://user?id=%d)\n" % user
        for user in self.fasts:
            text += ICON_FAST + " [%s" % self.fasts[user][0]
            if self.fasts[user][1] != None:
                text += " (%s)" % self.fasts[user][1]
            text += "](tg://user?id=%d)\n" % user

        if len(self.arsenals) > 0:
            text += "\n" + "*%d только в арс:*\n" % len(self.arsenals)
        for user in self.arsenals:
            text += ICON_ARS + " [%s" % self.arsenals[user][0]
            if self.arsenals[user][1] != None:
                text += " (%s)" % self.arsenals[user][1]
            text += "](tg://user?id=%d)\n" % user

        if len(self.thinking) > 0:
            text += "\n" + "*%d думают:*\n" % len(self.thinking)
        for user in self.thinking:
            text += ICON_THINK + " [%s" % self.thinking[user][0]
            if self.thinking[user][1] != None:
                text += " (%s)" % self.thinking[user][1]
            text += "](tg://user?id=%d)\n" % user

        if len(self.cancels) > 0:
            text += "\n" + "*%d передумали:*\n" % len(self.cancels)
        for user in self.cancels:
            text += ICON_CANCEL + " [%s" % self.cancels[user][0]
            if self.cancels[user][1] != None:
                text += " (%s)" % self.cancels[user][1]
            text += "](tg://user?id=%d)\n" % user

        if len(self.lates) > 0:
            text += "\n" + "*%d опоздали:*\n" % len(self.lates)
        for user in self.lates:
            text += ICON_LATE + " [%s" % self.lates[user][0]
            if self.lates[user][1] != None:
                text += " (%s)" % self.lates[user][1]
            text += "](tg://user?id=%d)\n" % user
        return text

    def GetVotedText(self, action):
        if action == CHECK_CHECK_CALLBACK:
            return action.replace(CHECK_CALLBACK_PREFIX, "") + " Вы идете. Ожидайте росписи!"
        elif action == CHECK_RAGE_CALLBACK:
            return action.replace(CHECK_CALLBACK_PREFIX, "") + " Вы придете к ярости"
        elif action == CHECK_FAST_CALLBACK:
            return action.replace(CHECK_CALLBACK_PREFIX, "") + " Вы сливаете энку"
        elif action == CHECK_ARS_CALLBACK:
            return action.replace(CHECK_CALLBACK_PREFIX, "") + " Вы идете только в арсенал. Не атакуйте без росписи!"
        elif action == CHECK_THINK_CALLBACK:
            return action.replace(CHECK_CALLBACK_PREFIX, "") + " Вы еще не решили. Постарайтесь определиться к началу боя!"
        elif action == CHECK_CANCEL_CALLBACK:
            return action.replace(CHECK_CALLBACK_PREFIX, "") + " Вы не придете на бой. Жаль"
        elif action == CHECK_LATE_CALLBACK:
            return action.replace(CHECK_CALLBACK_PREFIX, "") + " Вы опоздали к началу. Дождитесь росписи от офицера!"

    def CheckUser(self, user, action):
        ret = True
        log.info("User %d (%s %s) voted for %s" % (*user, action.replace(CHECK_CALLBACK_PREFIX, "")))
        if action == CHECK_CHECK_CALLBACK:
            ret = self.SetCheck(user)
        elif action == CHECK_RAGE_CALLBACK:
            ret = self.SetRageOnly(user)
        elif action == CHECK_FAST_CALLBACK:
            ret = self.SetFast(user)
        elif action == CHECK_ARS_CALLBACK:
            ret = self.SetArsenalOnly(user)
        elif action == CHECK_THINK_CALLBACK:
            ret = self.SetThinking(user)
        elif action == CHECK_CANCEL_CALLBACK:
            ret = self.SetCancel(user)
        elif action == CHECK_LATE_CALLBACK:
            ret = self.SetLate(user)
        if ret: log.info("Vote successful")
        else: log.error("Vote failed")
        return ret

    def SetCheck(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.checks:
            if userid == user: # cannot check more than once
                return False
        # remove user from other lists
        if userid in self.rages: del self.rages[userid]
        if userid in self.arsenals: del self.arsenals[userid]
        if userid in self.fasts: del self.fasts[userid]
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
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
        if userid in self.checks: del self.checks[userid]
        if userid in self.arsenals: del self.arsenals[userid]
        if userid in self.fasts: del self.fasts[userid]
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
        self.rages[userid] = [name, nick]
        return True

    def SetFast(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.fasts:
            if userid == user: # cannot check more than once
                return False
        # remove user from other lists
        if userid in self.checks: del self.checks[userid]
        if userid in self.rages: del self.rages[userid]
        if userid in self.arsenals: del self.arsenals[userid]
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
        self.fasts[userid] = [name, nick]
        return True

    def SetArsenalOnly(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.arsenals:
            if userid == user: # cannot check more than once
                return False
        # remove user from other lists
        if userid in self.checks: del self.checks[userid]
        if userid in self.rages: del self.rages[userid]
        if userid in self.fasts: del self.fasts[userid]
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
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
        if userid in self.checks: del self.checks[userid]
        if userid in self.rages: del self.rages[userid]
        if userid in self.fasts: del self.fasts[userid]
        if userid in self.arsenals: del self.arsenals[userid]
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
        if userid in self.checks: del self.checks[userid]
        if userid in self.rages: del self.rages[userid]
        if userid in self.fasts: del self.fasts[userid]
        if userid in self.arsenals: del self.arsenals[userid]
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.lates: del self.lates[userid]
        self.cancels[userid] = [name, nick]
        return True

    def SetLate(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.lates:
            if userid == user: # cannot check late more than once
                return False
        if  userid in self.checks or \
            userid in self.rages or \
            userid in self.fasts or \
            userid in self.arsenals:
            return False
        if userid in self.cancels: del self.cancels[userid]
        if userid in self.thinking: del self.thinking[userid]
        self.lates[userid] = [name, nick]
        return True
