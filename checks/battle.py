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
    user = User(call.from_user.id, call.from_user.first_name, call.from_user.username)
    userChoice = call.data
    log.debug("%s is trying to vote for battle (%s)" % (user, userChoice.replace(cb.CHECK_CALLBACK_PREFIX, "")))
    if common.current_battle and message_id == common.current_battle.check_id:
        is_guide_training = False
        battle_object = common.current_battle
    elif user._id in common.user_guiding.keys(): # guide battle example workaround
        is_guide_training = True
        if common.user_guiding[user._id].IsTrainingStage(): # using check is allowed only at several steps of guide
            battle_object = common.user_guiding[user._id].demonstration
        else:
            log.error("Not at training stage, aborting")
            bot.answer_callback_query(call.id, "На данный момент использование чека недоступно")
            return
    else:
        battle_object = None
    if battle_object:
        ret = battle_object.CheckUser(user, userChoice)
        if ret or userChoice == cb.CHECK_LATE_CALLBACK:
            markup = kb.KEYBOARD_CHECK
            if battle_object.is_rolling:
                markup = kb.KEYBOARD_CHECK_ROLLED
            elif battle_object.is_started:
                markup = kb.KEYBOARD_LATE
            if is_guide_training:
                bot.edit_message_text(battle_object.GetText(), user._id, battle_object.check_id,
                                      parse_mode="markdown", reply_markup=markup)
            else:
                bot.edit_message_text(battle_object.GetText(), inline_message_id=message_id, 
                                      parse_mode="markdown", reply_markup=markup)
            bot.answer_callback_query(call.id, battle_object.GetVotedText(userChoice))
            if userChoice == cb.CHECK_LATE_CALLBACK and ret and not is_guide_training:
                text = ICON_LATE + " %s пришел на бой!\n" % user.GetString()
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
    message_id = call.inline_message_id
    user = User(call.from_user.id, call.from_user.first_name, call.from_user.username)
    log.debug("%s is trying to control battle" % user)
    if not hlp.IsUserAdmin(user):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять боем!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    need_send_notification = True
    if common.current_battle and message_id == common.current_battle.check_id:
        notification_text = ""
        if userChoice == kb.CHECK_CONTROL_OPTIONS[0]: # roll
            common.current_battle.DoRollBattle()
            notification_text = ICON_ROLL+" Крутит"
            bot.edit_message_text(common.current_battle.GetText(), inline_message_id=common.current_battle.check_id,
                                  parse_mode="markdown", reply_markup=common.current_battle.keyboard)
            common.current_battle.BattleRollNotifyActiveUsers(except_user=user)
        elif userChoice == kb.CHECK_CONTROL_OPTIONS[1]: # start
            common.current_battle.DoStartBattle()
            notification_text = ICON_SWORDS+" Бой начался"
            bot.edit_message_text(common.current_battle.GetText(), inline_message_id=common.current_battle.check_id,
                                  parse_mode="markdown", reply_markup=common.current_battle.keyboard)
            common.current_battle.BattleStartNotifyActiveUsers(except_user=user)
        elif userChoice == kb.CHECK_CONTROL_OPTIONS[2]: # stop
            if not common.current_battle.is_started: # if battle was cancelled - do not send notification
                need_send_notification = False
                notification_text = ICON_CANCEL+" Бой отменен"
            else: # unpin other battle messages
                bot.unpin_chat_message(common.warchat_id)
                notification_text = ICON_FINISH+" Бой завершен"
            reset_battlechecks(call)
            # do not notify about roll / stop
        if need_send_notification:
            bot.send_message(common.warchat_id,
                             notification_text + " (%s)" % user.GetString(),
                             parse_mode="markdown")
            log.debug("Battle status notification posted: %s" % notification_text)
        hlp.LogEvent(notification_text + " (%s)" % user.GetString(with_link=False))
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
    user = User(q.from_user.id, q.from_user.first_name, q.from_user.username)
    log.debug("%s is trying to create battle check" % user)
    if not hlp.IsUserAdmin(user): # non-admins cannot post votes
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
                q.inline_message_id = common.current_battle.check_id
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
    if not common.DEBUG_MODE:
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
        bot.unpin_chat_message(common.warchat_id)
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
    last_backup = None
    is_rolling = False
    is_started = False
    is_postponed = False
    keyboard = None
    checks = {}   # { User: twink_count }
    rages = {}    # { User: twink_count }
    fasts = {}    # { User: twink_count }
    arsenals = {} # { User: twink_count }
    thinking = {} # { User: 0 }
    cancels = {}  # { User: 0 }
    lates = {}    # { User: 0 }

    def __init__(self, start):
        now = datetime.datetime.now()
        times = re.findall(r'\d+', start)
        self.time = {"start": None, "end": None}
        self.time["start"] = now.replace(hour=int(times[0]), minute=int(times[1]))
        self.last_backup = None
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
        self.keyboard = kb.KEYBOARD_CHECK
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
    def BattleRollNotifyActiveUsers(self, except_user=None):
        activeUsers = self.GetActiveUsers()
        for user in activeUsers:
            # do not notify user if checked for rage or is one preseed the button
            if user not in self.rages and user != except_user:
                bot.send_message(user._id, ICON_ROLL+" Крутит!")

    # Notify participated users if battle has been started
    def BattleStartNotifyActiveUsers(self, except_user=None):
        activeUsers = self.GetActiveUsers()
        for user in activeUsers:
            # do not notify user if checked for rage or is one preseed the button
            if user not in self.rages and user != except_user:
                bot.send_message(user._id, ICON_SWORDS+" Бой начинается!")

    def GetActiveUsers(self):
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
            for user, count in group.items():
                username = user.GetString(with_link=False)
                username += self.GetPlusNumericSuffix(count)
                users.add(username)
        return users

    def DoRollBattle(self):
        self.time["roll"] = datetime.datetime.now()
        self.is_rolling = True
        self.keyboard = kb.KEYBOARD_CHECK_ROLLED
        log.warning("Battle rolled at %0.2d:%0.2d" % (self.time["roll"].hour, self.time["roll"].minute))
        # force backup
        common.current_battle.last_backup = self.time["roll"]
        hlp.AWSCheckBackup(common.current_battle)

    def DoStartBattle(self):
        self.time["start"] = datetime.datetime.now()
        self.is_started = True
        self.is_rolling = False
        self.keyboard = kb.KEYBOARD_LATE
        log.warning("Battle started at %0.2d:%0.2d" % (self.time["start"].hour, self.time["start"].minute))
        # force backup
        common.current_battle.last_backup = self.time["start"]
        hlp.AWSCheckBackup(common.current_battle)

    def DoEndBattle(self):
        self.time["end"] = datetime.datetime.now()
        self.is_postponed = True
        self.is_rolling = False
        self.keyboard = None
        if self.is_started and not common.DEBUG_MODE:
            common.statistics.Update(self.CollectStatistic())
        log.warning("Battle ended at %0.2d:%0.2d" % (self.time["end"].hour, self.time["end"].minute))
        # force backup
        common.current_battle.last_backup = self.time["end"]
        hlp.AWSCheckBackup(common.current_battle)

    def CollectStatistic(self):
        statistic = {}
        for user in self.checks:
            statistic[user] = Score(battle=1)
        for user in self.rages:
            statistic[user] = Score(battle=1)
        for user in self.fasts:
            statistic[user] = Score(battle=1)
        for user in self.arsenals:
            statistic[user] = Score(battle=1)
        for user in self.lates:
            statistic[user] = Score(battle=1)
        return statistic

    def GetNominatedPrefix(self, user):
        return common.statistics.GetNominatedPrefix(user)

    def GetPlusNumericSuffix(self, count):
        nums = "0¹²³⁴⁵⁶⁷⁸⁹"
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
        for user, count in self.checks.items():
            text += ICON_CHECK + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user)
            text += user.GetString()
            text += self.GetPlusNumericSuffix(count) + "\n"

        for user, count in self.rages.items():
            text += ICON_RAGE + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user)
            text += user.GetString()
            text += self.GetPlusNumericSuffix(count) + "\n"

        for user, count in self.fasts.items():
            text += ICON_FAST + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user)
            text += user.GetString()
            text += self.GetPlusNumericSuffix(count) + "\n"

        if len(self.arsenals) > 0:
            text += "\n" + "*%d только в арс:*\n" % len(self.arsenals)
        for user, count in self.arsenals.items():
            text += ICON_ARS + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user)
            text += user.GetString()
            text += self.GetPlusNumericSuffix(count) + "\n"

        if len(self.thinking) > 0:
            text += "\n" + "*%d думают:*\n" % len(self.thinking)
        for user, _ in self.thinking.items():
            text += ICON_THINK + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user)
            text += user.GetString() + "\n"

        if len(self.cancels) > 0:
            text += "\n" + "*%d передумали:*\n" % len(self.cancels)
        for user, _ in self.cancels.items():
            text += ICON_CANCEL + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user)
            text += user.GetString() + "\n"

        if len(self.lates) > 0:
            text += "\n" + "*%d опоздали:*\n" % len(self.lates)
        for user, count in self.lates.items():
            text += ICON_LATE + " "
            text += (ICON_OFFICER + " ")*hlp.IsUserAdmin(user)
            text += self.GetNominatedPrefix(user)
            text += user.GetString()
            text += self.GetPlusNumericSuffix(count) + "\n"

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
        log.info("%s voted for %s" % (user, action.replace(cb.CHECK_CALLBACK_PREFIX, "")))
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
        if hlp.NeedCheckBackup(common.current_battle):
            common.current_battle.last_backup = datetime.datetime.now()
            hlp.AWSCheckBackup(common.current_battle)
        return ret

    def SetCheck(self, user):
        for _user in self.checks:
            if user == _user: # check +1 (twink case)
                oldrecord = self.checks[user]
                self.checks[user] = oldrecord+1
                return
        # remove user from other lists
        if user in self.rages: del self.rages[user]
        if user in self.arsenals: del self.arsenals[user]
        if user in self.fasts: del self.fasts[user]
        if user in self.thinking: del self.thinking[user]
        if user in self.cancels: del self.cancels[user]
        # create record
        self.checks[user] = 0

    def SetRageOnly(self, user):
        for _user in self.rages:
            if user == _user: # check +1 (twink case)
                oldrecord = self.rages[user]
                self.rages[user] = oldrecord+1
                return
        # remove user from other lists
        if user in self.checks: del self.checks[user]
        if user in self.arsenals: del self.arsenals[user]
        if user in self.fasts: del self.fasts[user]
        if user in self.thinking: del self.thinking[user]
        if user in self.cancels: del self.cancels[user]
        # create record
        self.rages[user] = 0

    def SetFast(self, user):
        for _user in self.fasts:
            if user == _user: # check +1 (twink case)
                oldrecord = self.fasts[user]
                self.fasts[user] = oldrecord+1
                return
        # remove user from other lists
        if user in self.checks: del self.checks[user]
        if user in self.rages: del self.rages[user]
        if user in self.arsenals: del self.arsenals[user]
        if user in self.thinking: del self.thinking[user]
        if user in self.cancels: del self.cancels[user]
        # create record
        self.fasts[user] = 0

    def SetArsenalOnly(self, user):
        for _user in self.arsenals:
            if user == _user: # check +1 (twink case)
                oldrecord = self.arsenals[user]
                self.arsenals[user] = oldrecord+1
                return
        # remove user from other lists
        if user in self.checks: del self.checks[user]
        if user in self.rages: del self.rages[user]
        if user in self.fasts: del self.fasts[user]
        if user in self.thinking: del self.thinking[user]
        if user in self.cancels: del self.cancels[user]
        # create record
        self.arsenals[user] = 0

    def SetThinking(self, user):
        for _user in self.thinking:
            if user == _user: # cannot think more than once
                return False
        # remove user from other lists
        if user in self.checks: del self.checks[user]
        if user in self.rages: del self.rages[user]
        if user in self.fasts: del self.fasts[user]
        if user in self.arsenals: del self.arsenals[user]
        if user in self.cancels: del self.cancels[user]
        # create record
        self.thinking[user] = 0
        return True

    def SetCancel(self, user):
        for _user in self.cancels:
            if user == _user: # cannot cancel more than once
                return False
        # remove user from other lists
        if user in self.checks: del self.checks[user]
        if user in self.rages: del self.rages[user]
        if user in self.fasts: del self.fasts[user]
        if user in self.arsenals: del self.arsenals[user]
        if user in self.thinking: del self.thinking[user]
        if user in self.lates: del self.lates[user]
        # create record
        self.cancels[user] = 0
        return True

    def SetLate(self, user):
        # now we use twinks so support late +1s
        if user in self.checks:
            self.SetCheck(user)
            return False
        elif user in self.rages:
            self.SetRageOnly(user)
            return False
        elif user in self.fasts:
            self.SetFast(user)
            return False
        elif user in self.arsenals:
            self.SetArsenalOnly(user)
            return False
        for _user in self.lates:
            if user == _user: # check +1 (twink case)
                oldrecord = self.lates[user]
                self.lates[user] = oldrecord+1
                return False
        if user in self.cancels: del self.cancels[user]
        if user in self.thinking: del self.thinking[user]
        self.lates[user] = 0
        return True
