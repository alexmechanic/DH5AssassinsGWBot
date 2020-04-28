#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class representing battle check
#

import datetime
from logger import get_logger
from telebot import types

import common
from common import bot
from icons import *
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
            if (ret):
                markup = kb.KEYBOARD_CHECK
                if common.current_battle.is_rolling:
                    markup = kb.KEYBOARD_CHECK_ROLLED
                elif common.current_battle.is_started:
                    markup = kb.KEYBOARD_LATE
                bot.edit_message_text(common.current_battle.GetText(), inline_message_id=message_id, 
                                    parse_mode="markdown", reply_markup=markup)
                bot.answer_callback_query(call.id, common.current_battle.GetVotedText(userChoice))
                if common.warchat_id:
                    if userChoice == cb.CHECK_LATE_CALLBACK:
                        text = ICON_LATE + " [%s" % user[2]
                        if user[1] != None:
                            text += " (%s)" % user[1]
                        text += "](tg://user?id=%d) пришел на бой!\n" % user[0]
                        bot.send_message(common.warchat_id, text, parse_mode="markdown", disable_notification=True)
                        log.debug("Battle user late notification posted")
                else:
                    log.error("War chat_id is not set, cannot post late notification!")
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
    if not hlp.IsUserAdmin(call):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять боем!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    if common.current_battle:
        notification_text = ""
        if userChoice == kb.CHECK_CONTROL_OPTIONS[0]: # roll
            common.current_battle.DoRollBattle()
            notification_text = ICON_ROLL+" Крутит"
            KEYBOARD_CHECK_CURRENT = kb.KEYBOARD_CHECK_ROLLED
            bot.edit_message_text(common.current_battle.GetText(), inline_message_id=common.current_battle.check_id,
                                  parse_mode="markdown", reply_markup=kb.KEYBOARD_CHECK_ROLLED)
            common.current_battle.BattleRollNotifyActiveUsers()
        elif userChoice == kb.CHECK_CONTROL_OPTIONS[1]: # start
            common.current_battle.DoStartBattle()
            notification_text = ICON_SWORDS+" Бой начался"
            KEYBOARD_CHECK_CURRENT = kb.KEYBOARD_LATE
            bot.edit_message_text(common.current_battle.GetText(), inline_message_id=common.current_battle.check_id,
                                  parse_mode="markdown", reply_markup=kb.KEYBOARD_LATE)
            common.current_battle.BattleStartNotifyActiveUsers()
        elif userChoice == kb.CHECK_CONTROL_OPTIONS[2]: # stop
            reset_control(call)
            notification_text = ICON_FINISH+" Бой завершен"
        if common.warchat_id:
            notification = bot.send_message(common.warchat_id, notification_text, disable_notification=False)
            if userChoice not in [kb.CHECK_CONTROL_OPTIONS[0], kb.CHECK_CONTROL_OPTIONS[2]]: # roll / stop
                bot.pin_chat_message(notification.chat.id, notification.message_id, disable_notification=False)
            else:
                bot.unpin_chat_message(common.warchat_id)
            log.debug("Battle status notification posted: %s" % notification_text)
        else:
            log.error("War chat_id is not set, cannot post battle status notification!")
        bot.answer_callback_query(call.id, notification_text)
        return
    log.error("Battle not found!")
    bot.answer_callback_query(call.id, "Неверный чек боя! Пожалуйста, создайте новый")

#
# Battle check creation
# (war chat inline query)
#
@bot.inline_handler(lambda query: hlp.IsCheckTimeQuery(query)[0])
def battle_query_inline(q):
    # print("battle_query_inline")
    # print(q)
    user = [q.from_user.id, q.from_user.username, q.from_user.first_name]
    log.debug("User %d (%s %s) is trying to create battle check" % (*user,))
    if not hlp.IsUserAdmin(q): # non-admins cannot post votes
        log.error("Failed (not an admin)")
        hlp.SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    times = hlp.IsCheckTimeQuery(q)[1]
    if hlp.CanStartNewBattle():
        res = types.InlineQueryResultArticle('battle',
                                            title='[%s/%s] Создать чек на бой' % (times[0], times[1]),
                                            description=ICON_CHECK+ICON_RAGE+ICON_FAST+ICON_ARS+ICON_THINK+ICON_CANCEL,
                                            input_message_content=types.InputTextMessageContent("BATTLE PLACEHOLDER", parse_mode="markdown"),
                                            thumb_url="https://i.ibb.co/jb9nVCm/battle.png",
                                            reply_markup=kb.KEYBOARD_CHECK)
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=2)
    else:
        log.error("Trying to setup another battle while current is not finished")
        error_text = "Уже имеется активный бой в %0.2d:%0.2d" \
                     % (common.current_battle.time["start"].hour, common.current_battle.time["start"].minute)
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")

#
# Emergency reset control
# (private bot chat)
#
@bot.message_handler(func=lambda message: message.text in kb.RESET_CONTROL_OPTIONS)
def reset_control(m):
    try:
        if not hlp.IsInPrivateChat(m): return
    except: # issue when resetting checks via battle stop. could be ignored
        pass
    if not hlp.IsUserAdmin(m):
        hlp.SendHelpNonAdmin(m)
        return
    markup = types.ReplyKeyboardRemove(selective=False)
    try:
        if m.text == kb.RESET_CONTROL_OPTIONS[1]: # cancel
            bot.send_message(m.from_user.id, "⛔️ Действие отменено", reply_markup=markup)
            log.debug("Reset calcelled")
            return
        else:
            raise Exception()
    except:
        
        if not hlp.CanStartNewPrecheck():
            common.current_precheck.DoEndPrecheck()
            bot.edit_message_text(common.current_precheck.GetText(), inline_message_id=common.current_precheck.check_id,
                                  parse_mode="markdown")
            common.current_precheck = None
        if not hlp.CanStartNewBattle():
            common.current_battle.DoEndBattle()
            bot.edit_message_text(common.current_battle.GetText(), inline_message_id=common.current_battle.check_id,
                                  parse_mode="markdown")
            common.current_battle = None
        if common.current_arscheck:
            common.current_arscheck.DoEndArsenal()
            bot.edit_message_text(common.current_arscheck.GetText(), inline_message_id=common.current_arscheck.check_id,
                                  parse_mode="markdown")
            common.current_arscheck = None
        if not hlp.CanStartNewNumbers():
            common.current_numcheck.DoEndCheck()
            bot.edit_message_text(common.current_numcheck.GetText(), inline_message_id=common.current_numcheck.check_id,
                                  parse_mode="markdown")
            common.current_numcheck = None
    try:
        bot.send_message(m.from_user.id, ICON_CHECK+" Бот успешно сброшен", reply_markup=markup)
    except: # no need to send private message if checks have been reset via battle control
        pass
    log.debug("Reset successful")

class Battle():
    check_id = None
    time = {"check": None, "start": None, "end": None}
    is_rolling = False
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
        self.is_rolling = False
        self.is_started = False
        self.is_postponed = False
        log.info("New battle created (%0.2d:%0.2d / %0.2d:%0.2d)" \
                % (self.time["check"].hour, self.time["check"].minute, self.time["start"].hour, self.time["start"].minute))

    def SetMessageID(self, message_id):
        self.check_id = message_id
        log.debug("Set inline message_id: %s" % self.check_id)

    # Notify participated users if battle has been rolled
    def BattleRollNotifyActiveUsers(self):
        activeUsers = self.GetActiveUsersID()
        print("BattleRollNotifyActiveUsers:")
        print(activeUsers)
        for user in activeUsers:
            if user not in self.rages: # do not notify user if checked for rage
                print("Notify user: ", user)
                bot.send_message(user, ICON_ROLL+" Крутит!")

    # Notify participated users if battle has been started
    def BattleStartNotifyActiveUsers(self):
        activeUsers = self.GetActiveUsersID()
        print("BattleStartNotifyActiveUsers:")
        print(activeUsers)
        for user in activeUsers:
            if user not in self.rages: # do not notify user if checked for rage
                print("Notify user: ", user)
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
        print("GetActiveUsersID:")
        print(users)
        return users

    def GetActiveUsersNames(self):
        users = set()
        for user in self.checks:
            username = self.checks[user][0]
            if self.checks[user][1] != None:
                username += " (%s)" % self.checks[user][1]
            users.add(username)
        for user in self.rages:
            username = self.rages[user][0]
            if self.rages[user][1] != None:
                username += " (%s)" % self.rages[user][1]
            users.add(username)
        for user in self.fasts:
            username = self.fasts[user][0]
            if self.fasts[user][1] != None:
                username += " (%s)" % self.fasts[user][1]
            users.add(username)
        for user in self.arsenals:
            username = self.arsenals[user][0]
            if self.arsenals[user][1] != None:
                username += " (%s)" % self.arsenals[user][1]
            users.add(username)
        for user in self.lates:
            username = self.lates[user][0]
            if self.lates[user][1] != None:
                username += " (%s)" % self.lates[user][1]
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
        log.warning("Battle ended at %0.2d:%0.2d" % (self.time["end"].hour, self.time["end"].minute))

    def GetHeader(self):
        text = ICON_SWORDS+" *Чек:* %0.2d:%0.2d, *Бой:* %.2d:%.2d\n" \
                % (self.time["check"].hour, self.time["check"].minute, self.time["start"].hour, self.time["start"].minute)
        return text

    def GetText(self):
        text = self.GetHeader()
        if self.is_rolling:
            text += "Поиск запущен в %0.2d:%0.2d\n" % (self.time["roll"].hour, self.time["roll"].minute)
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
            ret = self.SetCheck(user)
        elif action == cb.CHECK_RAGE_CALLBACK:
            ret = self.SetRageOnly(user)
        elif action == cb.CHECK_FAST_CALLBACK:
            ret = self.SetFast(user)
        elif action == cb.CHECK_ARS_CALLBACK:
            ret = self.SetArsenalOnly(user)
        elif action == cb.CHECK_THINK_CALLBACK:
            ret = self.SetThinking(user)
        elif action == cb.CHECK_CANCEL_CALLBACK:
            ret = self.SetCancel(user)
        elif action == cb.CHECK_LATE_CALLBACK:
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
            userid in self.rages or  \
            userid in self.fasts or  \
            userid in self.arsenals:
            return False
        if userid in self.cancels: del self.cancels[userid]
        if userid in self.thinking: del self.thinking[userid]
        self.lates[userid] = [name, nick]
        return True
