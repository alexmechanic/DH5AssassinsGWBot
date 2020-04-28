#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class representing arsenal check
#

import datetime
from logger import get_logger
from telebot import types

import common
from common import bot
from icons import *
from commands import COMMANDS
import keyboards as kb
import callbacks as cb
import helpers as hlp

log = get_logger("bot." + __name__)

#
# Arsenal progress for battle
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.ARS_OPTIONS)
def arsenal_check_user(call):
    # print("arsenal_check_user")
    # print(call)
    message_id = call.inline_message_id
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    userChoice = call.data
    log.debug("User %d (%s %s) is trying to vote for arsenal (%s)" % (*user, userChoice.replace(cb.ARS_CALLBACK_PREFIX, "")))
    if common.current_arscheck:
        if message_id == common.current_arscheck.check_id:
            ret = common.current_arscheck.Increment(user, userChoice)
            if (ret):
                bot.edit_message_text(common.current_arscheck.GetText(), inline_message_id=message_id,
                                    parse_mode="markdown", reply_markup=kb.KEYBOARD_ARS)
                common.current_arscheck.CheckNotifyIfFired(common.current_battle, bot, common.warchat_id)
            else:
                log.error("Failed")
            bot.answer_callback_query(call.id)
            return
    log.error("Ars check not found!")
    bot.answer_callback_query(call.id, "Неверный чек арсенала! Пожалуйста, создайте новый")

#
# Arsenal control
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.ARS_CONTROL_OPTIONS)
def arsenal_control(call):
    # print("arsenal_control")
    # print(call)
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    log.debug("User %d (%s %s) is trying to control arsenal check" % (*user,))
    if not hlp.IsUserAdmin(call):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять чеком арсенала!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    if userChoice == kb.ARS_CONTROL_OPTIONS[0]: # stop
        if (common.current_arscheck):
            common.current_arscheck.DoEndArsenal()
            bot.edit_message_text(common.current_arscheck.GetText(),
                                  inline_message_id=common.current_arscheck.check_id,
                                  parse_mode="markdown")
            bot.answer_callback_query(call.id, "🏁 Чек арсенала завершен")
            return
    log.error("Ars check not found!")
    bot.answer_callback_query(call.id, "Неверный чек арсенала! Пожалуйста, создайте новый")

#
# Arsenal creation
# (war chat inline query)
#
@bot.inline_handler(lambda query: query.query[:len(COMMANDS["arsenal"])] == COMMANDS["arsenal"])
def arsenal_query_inline(q):
    # print("arsenal_query_inline")
    # print(q)
    user = [q.from_user.id, q.from_user.username, q.from_user.first_name]
    log.debug("User %d (%s %s) is trying to create arsenal check" % (*user,))
    if not hlp.IsUserAdmin(q): # non-admins cannot post votes
        log.error("Failed (not an admin)")
        hlp.SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    if hlp.CanStartNewBattle():
        log.error("Trying to setup arsenal check with no current battle")
        error_text = "Отсутствует активный бой"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")
        return
    rage = hlp.IsArsQuery(q)
    if rage[0]:
        if hlp.CanStartNewArs():
            common.rage_time_workaround = rage[1][0]
            res = types.InlineQueryResultArticle('arsenal',
                                                 title='Добавить прогресс арса',
                                                 description='📦 |████--| Х/120\nЯрость в %s' % common.rage_time_workaround,
                                                 input_message_content=types.InputTextMessageContent("ARS PLACEHOLDER", parse_mode="markdown"),
                                                 thumb_url="https://i.ibb.co/WfxPRks/arsenal.png",
                                                 reply_markup=kb.KEYBOARD_ARS)
            bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=2)
        else:
            log.error("Trying to setup another arsenal check while current has not been fired")
            error_text = "Уже имеется активный чек арсенала"
            bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                    switch_pm_text=error_text, switch_pm_parameter="existing_arsenal")
    else:
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text="Неверный формат запроса", switch_pm_parameter="existing_arsenal")


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
        arsValue = value.replace(cb.ARS_CALLBACK_PREFIX, "")
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
