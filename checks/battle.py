#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class and methods representing battle check
#

import datetime, re
from logger import get_logger
from telebot import types

import common
from common import bot
from icons import *
from statistics import *
from commands import COMMANDS
import keyboards as kb
import callbacks as cb
import helpers as hlp

log = get_logger("bot." + __name__)

#
# Battle check
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.CHECK_OPTIONS)
def battle_check_user(call):
    # print("battle_check_user")
    # print(call)
    message_id = call.inline_message_id
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    userChoice = call.data
    log.debug("User %d (%s %s) is trying to vote for battle (%s)" % (*user, userChoice.replace(cb.CHECK_CALLBACK_PREFIX, "")))
    if common.current_battle:
        if message_id == common.current_battle.check_id:
            ret = common.current_battle.CheckUser(user, userChoice)
            if ret or userChoice == cb.CHECK_LATE_CALLBACK:
                markup = kb.KEYBOARD_CHECK
                if common.current_battle.is_rolling:
                    markup = kb.KEYBOARD_CHECK_ROLLED
                elif common.current_battle.is_started:
                    markup = kb.KEYBOARD_LATE
                bot.edit_message_text(common.current_battle.GetText(), inline_message_id=message_id, 
                                    parse_mode="markdown", reply_markup=markup)
                bot.answer_callback_query(call.id, common.current_battle.GetVotedText(userChoice))
                if userChoice == cb.CHECK_LATE_CALLBACK and ret:
                    text = ICON_LATE + " [%s" % user[2]
                    if user[1] != None:
                        text += " (%s)" % user[1]
                    text += "](tg://user?id=%d) пришел на бой!\n" % user[0]
                    bot.send_message(common.warchat_id, text, parse_mode="markdown", disable_notification=True)
                    log.debug("Battle user late notification posted")
            else:
                log.error("Failed")
                bot.answer_callback_query(call.id, "Вы уже проголосовали (%s)" % userChoice.replace(cb.CHECK_CALLBACK_PREFIX, ""))
            return
    log.error("Battle not found!")
    bot.answer_callback_query(call.id, "Неверный чек боя! Пожалуйста, создайте новый")

#
# Battle control
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.CHECK_CONTROL_OPTIONS)
def battle_control(call):
    # print("battle_control")
    # print(call)
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    log.debug("User %d (%s %s) is trying to control battle" % (*user,))
    if not hlp.IsUserAdmin(user[0]):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять боем!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    need_send_notification = True
    if common.current_battle:
        notification_text = ""
        user_addend = " ([%s](tg://user?id=%d))" % (user[2], user[0])
        if userChoice == kb.CHECK_CONTROL_OPTIONS[0]: # roll
            common.current_battle.DoRollBattle()
            notification_text = ICON_ROLL+" Крутит"
            KEYBOARD_CHECK_CURRENT = kb.KEYBOARD_CHECK_ROLLED
            bot.edit_message_text(common.current_battle.GetText(), inline_message_id=common.current_battle.check_id,
                                  parse_mode="markdown", reply_markup=kb.KEYBOARD_CHECK_ROLLED)
            common.current_battle.BattleRollNotifyActiveUsers(except_user=user)
        elif userChoice == kb.CHECK_CONTROL_OPTIONS[1]: # start
            common.current_battle.DoStartBattle()
            notification_text = ICON_SWORDS+" Бой начался"
            KEYBOARD_CHECK_CURRENT = kb.KEYBOARD_LATE
            bot.edit_message_text(common.current_battle.GetText(), inline_message_id=common.current_battle.check_id,
                                  parse_mode="markdown", reply_markup=kb.KEYBOARD_LATE)
            common.current_battle.BattleStartNotifyActiveUsers(except_user=user)
        elif userChoice == kb.CHECK_CONTROL_OPTIONS[2]: # stop
            if not common.current_battle.is_started: # if battle was cancelled - do not send notification
                need_send_notification = False
            else: # unpin other battle messages
                bot.unpin_chat_message(common.warchat_id)
            reset_battlechecks(call)
            notification_text = ICON_FINISH+" Бой завершен"
            # do not notify about roll / stop
        if need_send_notification:
            bot.send_message(common.warchat_id,
                             notification_text + user_addend,
                             parse_mode="markdown")
            log.debug("Battle status notification posted: %s" % notification_text)
        bot.answer_callback_query(call.id, notification_text)
        return
    log.error("Battle not found!")
    bot.answer_callback_query(call.id, "Неверный чек боя! Пожалуйста, создайте новый")

#
# Battle check creation
# (war chat inline query)
#
@bot.inline_handler(lambda query: query.query[:len(COMMANDS["battle"])] == COMMANDS["battle"])
def battle_query_inline(q):
    # print("battle_query_inline")
    # print(q)
    user = [q.from_user.id, q.from_user.username, q.from_user.first_name]
    log.debug("User %d (%s %s) is trying to create battle check" % (*user,))
    if not hlp.IsUserAdmin(user[0]): # non-admins cannot post votes
        log.error("Failed (not an admin)")
        hlp.SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    res, time = hlp.IsCheckTimeQuery(q)
    if res:
        if hlp.CanStartNewBattle() or hlp.CanStopCurrentBattle():
            res = types.InlineQueryResultArticle('battle',
                                                title='[%s] Создать чек на бой' % time,
                                                description=ICON_CHECK+ICON_RAGE+ICON_FAST+ICON_ARS+ICON_THINK+ICON_CANCEL,
                                                input_message_content=types.InputTextMessageContent(ICON_SWORDS+" *Бой*: %s" % time, parse_mode="markdown"),
                                                thumb_url="https://i.ibb.co/jb9nVCm/battle.png",
                                                reply_markup=kb.KEYBOARD_CHECK)
            bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=2)
            # stop current battle as the time is passed anyway
            # to help admin not doing exact battle stop but start another with auto-stopping the previous
            if hlp.CanStopCurrentBattle():
                q.data = kb.CHECK_CONTROL_OPTIONS[2]
                battle_control(q)
        else:
            log.error("Trying to setup another battle while current is not finished")
            error_text = "Уже имеется активный бой в %0.2d:%0.2d" % (*common.current_battle.GetTime(start=True),)
            bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                    switch_pm_text=error_text, switch_pm_parameter="existing_battle")
    else:
        log.error("Failed (invalid query)")
        error_text = "Неверный формат запроса"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")

#
# Battle checks reset control
# (private bot chat)
#
def reset_battlechecks(m):
    common.statistics.CycleIfNeed()
    if not hlp.CanStartNewBattle(): # should hit 'end' to start another
        common.current_battle.DoEndBattle()
        bot.edit_message_text(common.current_battle.GetText(), inline_message_id=common.current_battle.check_id,
                              parse_mode="markdown")
        common.current_battle = None
    if common.current_arscheck: # postponed is not a condition that check ended
        common.current_arscheck.DoEndArsenal()
        bot.edit_message_text(common.current_arscheck.GetText(), inline_message_id=common.current_arscheck.check_id,
                              parse_mode="markdown")
        # unpin rage time message if can
        try:
            bot.unpin_chat_message(common.warchat_id)
        except:
            pass
        common.current_arscheck = None
    if common.current_numcheck: # postponed is not a condition that check ended
        common.current_numcheck.DoEndCheck()
        bot.edit_message_text(common.current_numcheck.GetText(), inline_message_id=common.current_numcheck.check_id,
                              parse_mode="markdown")
        common.current_numcheck = None
    common.statistics.BackupIfNeed(m)

class Battle():
    check_id = None
    time = {"start": None, "end": None}
    is_rolling = False
    is_started = False
    is_postponed = False
    # { userid: [name, nick, twink_count] }
    checks = {}
    rages = {}
    fasts = {}
    arsenals = {}
    thinking = {}
    cancels = {}
    lates = {}

    def __init__(self, start):
        now = datetime.datetime.now()
        times = re.findall(r'\d+', start)
        self.time["start"] = now.replace(hour=int(times[0]), minute=int(times[1]))
        self.checks = {}
        self.rages = {}
        self.fasts = {}
        self.arsenals = {}
        self.thinking = {}
        self.cancels = {}
        self.lates = {}
        self.is_rolling = False
        self.is_started = False
        self.is_postponed = False
        log.info("New battle created (%0.2d:%0.2d)" % (self.time["start"].hour, self.time["start"].minute))

    def SetMessageID(self, message_id):
        self.check_id = message_id
        log.debug("Set inline message_id: %s" % self.check_id)

    def GetTime(self, start=False, end=False):
        if start:
            return [self.time["start"].hour, self.time["start"].minute]
        elif end:
            return [self.time["end"].hour, self.time["end"].minute]
        return []

    # Notify participated users if battle has been rolled
    def BattleRollNotifyActiveUsers(self, except_user=[None]):
        activeUsers = self.GetActiveUsersID()
        for user in activeUsers:
            # do not notify user if checked for rage or is one preseed the button
            if user not in self.rages and \
               user != except_user[0]:
                bot.send_message(user, ICON_ROLL+" Крутит!")

    # Notify participated users if battle has been started
    def BattleStartNotifyActiveUsers(self, except_user=[None]):
        activeUsers = self.GetActiveUsersID()
        for user in activeUsers:
            # do not notify user if checked for rage or is one preseed the button
            if user not in self.rages and \
               user != except_user[0]:
                bot.send_message(user, ICON_SWORDS+" Бой начинается!")

    def GetActiveUsersID(self):
        users = set()
        for user in self.checks:
            users.add(user)
        for user in self.rages:
            users.add(user)
        for user in self.fasts:
            users.add(user)
        for user in self.arsenals:
            users.add(user)
        for user in self.thinking:
            users.add(user)
        for user in self.lates:
            users.add(user)
        return users

    def GetActiveUsersNames(self):
        users = set()
        for group in [self.checks, self.rages, self.fasts, self.arsenals, self.lates]:
            for user in group:
                username = self.GetUserString(user, group)
                username += self.GetPlusNumericSuffix(user, group)
                users.add(username)
        return users

    def DoRollBattle(self):
        self.time["roll"] = datetime.datetime.now()
        self.is_rolling = True
        log.warning("Battle rolled at %0.2d:%0.2d" % (self.time["roll"].hour, self.time["roll"].minute))

    def DoStartBattle(self):
        self.time["start"] = datetime.datetime.now()
        self.is_started = True
        self.is_rolling = False
        log.warning("Battle started at %0.2d:%0.2d" % (self.time["start"].hour, self.time["start"].minute))

    def DoEndBattle(self):
        self.time["end"] = datetime.datetime.now()
        self.is_postponed = True
        self.is_rolling = False
        if self.is_started:
            common.statistics.Update(self.CollectStatistic())
        log.warning("Battle ended at %0.2d:%0.2d" % (self.time["end"].hour, self.time["end"].minute))

    def CollectStatistic(self):
        statistic = {}
        for k, v in self.checks.items():
            statistic[User(k, v[0], v[1])] = Score(battle=1)
        for k, v in self.rages.items():
            statistic[User(k, v[0], v[1])] = Score(battle=1)
        for k, v in self.fasts.items():
            statistic[User(k, v[0], v[1])] = Score(battle=1)
        for k, v in self.arsenals.items():
            statistic[User(k, v[0], v[1])] = Score(battle=1)
        for k, v in self.lates.items():
            statistic[User(k, v[0], v[1])] = Score(battle=1)
        return statistic

    def GetUserString(self, user, group, with_link=False):
        text = ""
        if with_link:
            text += "["
        text += "%s" % group[user][0]
        if group[user][1] != None:
            text += " (%s)" % group[user][1]
        if with_link:
            text += "](tg://user?id=%d)" % user
        return text

    def GetNominatedPrefix(self, user, group):
        user = User(user, group[user][0], group[user][1])
        return common.statistics.GetNominatedPrefix(user)

    def GetPlusNumericSuffix(self, user, group):
        nums = "0¹²³⁴⁵⁶⁷⁸⁹"
        count = group[user][2]
        return "⁺" + nums[count] if count > 0 else ""

    def GetHeader(self):
        text = ICON_SWORDS+" *Бой:* %.2d:%.2d\n" % (self.time["start"].hour, self.time["start"].minute)
        return text

    def GetText(self):
        text = self.GetHeader()
        if self.is_rolling:
            text += "⏳ *Поиск:* %0.2d:%0.2d\n" % (self.time["roll"].hour, self.time["roll"].minute)
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
            text += ICON_CHECK + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user, self.checks)
            text += self.GetUserString(user, self.checks, with_link=True)
            text += self.GetPlusNumericSuffix(user, self.checks) + "\n"

        for user in self.rages:
            text += ICON_RAGE + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user, self.rages)
            text += self.GetUserString(user, self.rages, with_link=True)
            text += self.GetPlusNumericSuffix(user, self.rages) + "\n"

        for user in self.fasts:
            text += ICON_FAST + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user, self.fasts)
            text += self.GetUserString(user, self.fasts, with_link=True)
            text += self.GetPlusNumericSuffix(user, self.fasts) + "\n"

        if len(self.arsenals) > 0:
            text += "\n" + "*%d только в арс:*\n" % len(self.arsenals)
        for user in self.arsenals:
            text += ICON_ARS + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user, self.arsenals)
            text += self.GetUserString(user, self.arsenals, with_link=True)
            text += self.GetPlusNumericSuffix(user, self.arsenals) + "\n"

        if len(self.thinking) > 0:
            text += "\n" + "*%d думают:*\n" % len(self.thinking)
        for user in self.thinking:
            text += ICON_THINK + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user, self.thinking)
            text += self.GetUserString(user, self.thinking, with_link=True)  + "\n"

        if len(self.cancels) > 0:
            text += "\n" + "*%d передумали:*\n" % len(self.cancels)
        for user in self.cancels:
            text += ICON_CANCEL + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user, self.cancels)
            text += self.GetUserString(user, self.cancels, with_link=True) + "\n"

        if len(self.lates) > 0:
            text += "\n" + "*%d опоздали:*\n" % len(self.lates)
        for user in self.lates:
            text += ICON_LATE + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user, self.lates)
            text += self.GetUserString(user, self.lates, with_link=True)
            text += self.GetPlusNumericSuffix(user, self.lates) + "\n"

        return text

    def GetVotedText(self, action):
        if action == cb.CHECK_CHECK_CALLBACK:
            return action.replace(cb.CHECK_CALLBACK_PREFIX, "") + " Вы идете. Ожидайте росписи!"
        elif action == cb.CHECK_RAGE_CALLBACK:
            return action.replace(cb.CHECK_CALLBACK_PREFIX, "") + " Вы придете к ярости"
        elif action == cb.CHECK_FAST_CALLBACK:
            return action.replace(cb.CHECK_CALLBACK_PREFIX, "") + " Вы сливаете энку"
        elif action == cb.CHECK_ARS_CALLBACK:
            return action.replace(cb.CHECK_CALLBACK_PREFIX, "") + " Вы идете только в арсенал. Не атакуйте без росписи!"
        elif action == cb.CHECK_THINK_CALLBACK:
            return action.replace(cb.CHECK_CALLBACK_PREFIX, "") + " Вы еще не решили. Постарайтесь определиться к началу боя!"
        elif action == cb.CHECK_CANCEL_CALLBACK:
            return action.replace(cb.CHECK_CALLBACK_PREFIX, "") + " Вы не придете на бой. Жаль"
        elif action == cb.CHECK_LATE_CALLBACK:
            return action.replace(cb.CHECK_CALLBACK_PREFIX, "") + " Вы опоздали к началу. Дождитесь росписи от офицера!"

    def CheckUser(self, user, action):
        ret = True
        log.info("User %d (%s %s) voted for %s" % (*user, action.replace(cb.CHECK_CALLBACK_PREFIX, "")))
        if action == cb.CHECK_CHECK_CALLBACK:
            self.SetCheck(user)
        elif action == cb.CHECK_RAGE_CALLBACK:
            self.SetRageOnly(user)
        elif action == cb.CHECK_FAST_CALLBACK:
            self.SetFast(user)
        elif action == cb.CHECK_ARS_CALLBACK:
            self.SetArsenalOnly(user)
        elif action == cb.CHECK_THINK_CALLBACK:
            ret = self.SetThinking(user)
        elif action == cb.CHECK_CANCEL_CALLBACK:
            ret = self.SetCancel(user)
        elif action == cb.CHECK_LATE_CALLBACK:
            ret = self.SetLate(user)
        # SetLate() always successful, return value indicates
        # that user has corrected his previous vote with +1 (not actually late)
        if ret:
            log.info("Vote successful")
        elif action != cb.CHECK_LATE_CALLBACK:
            log.error("Vote failed")
        return ret

    def SetCheck(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.checks:
            if userid == user: # check +1 (twink case)
                oldrecord = self.checks[userid]
                oldrecord[2] = oldrecord[2]+1
                self.checks[userid] = oldrecord
                return
        # remove user from other lists
        if userid in self.rages: del self.rages[userid]
        if userid in self.arsenals: del self.arsenals[userid]
        if userid in self.fasts: del self.fasts[userid]
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
        # create record
        self.checks[userid] = [name, nick, 0]

    def SetRageOnly(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.rages:
            if userid == user: # check +1 (twink case)
                oldrecord = self.rages[userid]
                oldrecord[2] = oldrecord[2]+1
                self.rages[userid] = oldrecord
                return
        # remove user from other lists
        if userid in self.checks: del self.checks[userid]
        if userid in self.arsenals: del self.arsenals[userid]
        if userid in self.fasts: del self.fasts[userid]
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
        # create record
        self.rages[userid] = [name, nick, 0]

    def SetFast(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.fasts:
            if userid == user: # check +1 (twink case)
                oldrecord = self.fasts[userid]
                oldrecord[2] = oldrecord[2]+1
                self.fasts[userid] = oldrecord
                return
        # remove user from other lists
        if userid in self.checks: del self.checks[userid]
        if userid in self.rages: del self.rages[userid]
        if userid in self.arsenals: del self.arsenals[userid]
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
        # create record
        self.fasts[userid] = [name, nick, 0]

    def SetArsenalOnly(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        for user in self.arsenals:
            if userid == user: # check +1 (twink case)
                oldrecord = self.arsenals[userid]
                oldrecord[2] = oldrecord[2]+1
                self.arsenals[userid] = oldrecord
                return
        # remove user from other lists
        if userid in self.checks: del self.checks[userid]
        if userid in self.rages: del self.rages[userid]
        if userid in self.fasts: del self.fasts[userid]
        if userid in self.thinking: del self.thinking[userid]
        if userid in self.cancels: del self.cancels[userid]
        # create record
        self.arsenals[userid] = [name, nick, 0]

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
        # create record
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
        # create record
        self.cancels[userid] = [name, nick]
        return True

    def SetLate(self, user):
        userid = user[0]
        nick = user[1]
        name = user[2]
        # now we use twinks so support late +1s
        if userid in self.checks:
            self.SetCheck(user)
            return False
        elif userid in self.rages:
            self.SetRageOnly(user)
            return False
        elif userid in self.fasts:
            self.SetFast(user)
            return False
        elif userid in self.arsenals:
            self.SetArsenalOnly(user)
            return False
        for user in self.lates:
            if userid == user: # check +1 (twink case)
                oldrecord = self.lates[userid]
                oldrecord[2] = oldrecord[2]+1
                self.lates[userid] = oldrecord
                return False
        if userid in self.cancels: del self.cancels[userid]
        if userid in self.thinking: del self.thinking[userid]
        self.lates[userid] = [name, nick, 0]
        return True
