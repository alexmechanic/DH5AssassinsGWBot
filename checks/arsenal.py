#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class and methods representing arsenal check
#

import datetime, re
from logger import get_logger
from telebot import types

import common
from common import bot
from icons import *
from statistics import User, Score
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
    user = User(call.from_user.id, call.from_user.first_name, call.from_user.username)
    userChoice = call.data
    log.debug("%s is trying to vote for arsenal (%s)" % (user, userChoice.replace(cb.ARS_CALLBACK_PREFIX, "")))
    if common.current_arscheck and message_id == common.current_arscheck.check_id:
        is_guide_training = False
        battle_object = common.current_arscheck
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
        if battle_object.Increment(user, userChoice, notify=not is_guide_training):
            if is_guide_training:
                bot.edit_message_text(battle_object.GetText(), user._id, battle_object.check_id,
                                      parse_mode="markdown", reply_markup=kb.KEYBOARD_ARS)
            else:
                bot.edit_message_text(battle_object.GetText(), inline_message_id=message_id,
                                      parse_mode="markdown", reply_markup=kb.KEYBOARD_ARS)
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
    message_id = call.inline_message_id
    user = User(call.from_user.id, call.from_user.first_name, call.from_user.username)
    log.debug("%s is trying to control arsenal check" % user)
    if not hlp.IsUserAdmin(user):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять чеком арсенала!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    if userChoice == kb.ARS_CONTROL_OPTIONS[0]: # stop
        if common.current_arscheck and message_id == common.current_arscheck.check_id:
            common.current_arscheck.DoEndArsenal()
            bot.edit_message_text(common.current_arscheck.GetText(),
                                  inline_message_id=common.current_arscheck.check_id,
                                  parse_mode="markdown")
            # unpin rage time message
            bot.unpin_chat_message(common.warchat_id)
            bot.answer_callback_query(call.id, "🏁 Чек арсенала завершен")
            hlp.LogEvent("🏁 %s завершил чек арсенала" % user.GetString(with_link=False))
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
    user = User(q.from_user.id, q.from_user.first_name, q.from_user.username)
    log.debug("%s is trying to create arsenal check" % user)
    if not hlp.IsUserAdmin(user): # non-admins cannot post votes
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
    res, time = hlp.IsArsQuery(q)
    if res:
        if hlp.CanStartNewArs():
            res = types.InlineQueryResultArticle('arsenal',
                                                 title='Добавить прогресс арсенала',
                                                 description=ICON_ARS+' |████--| Х/120\nЯрость в %s' % time,
                                                 input_message_content=types.InputTextMessageContent(ICON_ARS+" *Прогресс арсенала:* 0/120", parse_mode="markdown"),
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
    crit_notification = None
    progress = 0
    is_fired = False
    is_fire_notified = False
    rage_time = None
    rage_msg_id = None
    done_users = {} # {User: [value, count, is_fired]}
    is_postponed = False
    last_backup = None

    def __init__(self, rage):
        self.progress = 0
        self.is_fired = False
        self.done_users = {}
        times = re.findall(r'\d+', rage)
        now = datetime.datetime.now()
        self.rage_time = now.replace(hour=int(times[0]), minute=int(times[1]))
        self.rage_msg_id = None
        self.crit_notification = None
        self.is_postponed = False
        self.last_backup = None
        log.info("New arsenal check created")

    def SetMessageID(self, message_id):
        self.check_id = message_id
        log.debug("Set inline message_id: %s" % self.check_id)

    def SetRageMessageID(self, message_id):
        self.rage_msg_id = message_id
        log.debug("Set rage message_id: %s" % self.rage_msg_id)

    def GetProgress(self):
        return self.progress

    def DoEndArsenal(self):
        self.is_postponed = True
        if not common.DEBUG_MODE:
            common.statistics.Update(self.CollectStatistic())
        log.info("Arsenal check stopped")
        # force backup
        common.current_arscheck.last_backup = datetime.datetime.now()
        hlp.AWSCheckBackup(common.current_arscheck)

    def CollectStatistic(self):
        statistic = {}
        for user in self.done_users:
            statistic[user] = Score(arsenal=self.done_users[user][0])
        return statistic

    def CheckNotifyIfCritical(self):
        critical = common.settings.GetSetting("critical_threshold")
        if self.progress > critical and self.progress < 120: # critical value is calculated on thoughts that further 14+14 hits will trigger Rage
            log.info("Arsenal is critical! %s/120", self.progress)
            text = ICON_ARS+" %s/120.\n‼️ Вставайте на паузу!" % self.progress
            if self.crit_notification:
                common.bot.delete_message(self.crit_notification.chat.id, self.crit_notification.message_id).wait()
            self.crit_notification = common.bot.send_message(common.warchat_id, text).wait()
            if common.settings.GetSetting("critical_pin") and not common.DEBUG_MODE:
                common.bot.pin_chat_message(self.crit_notification.chat.id,
                                            self.crit_notification.message_id,
                                            disable_notification=False)
            log.debug("Arsenal critical status notification posted")
            return True
        return False

    # Notify participated users if arsenal has been fired
    def CheckNotifyIfFired(self, except_user=None):
        if self.is_fired and not self.is_fire_notified:
            # get active users from battle check
            activeUsers = common.current_battle.GetActiveUsers()
            for user in self.done_users:
                activeUsers.add(user)
            log.debug(activeUsers)
            now = datetime.datetime.now()
            text = ICON_RAGE+" %0.2d:%0.2d ГОРИТ!" % (now.hour, now.minute)
            if common.current_arscheck and self.check_id == common.current_arscheck.check_id:
                hlp.LogEvent(text)
            for user in activeUsers:
                if user != except_user:
                    common.bot.send_message(user._id, text)
            self.is_fire_notified = True
            notification = common.bot.send_message(common.warchat_id, text).wait()
            if common.settings.GetSetting("pin") and not common.DEBUG_MODE:
                common.bot.pin_chat_message(notification.chat.id, notification.message_id)
            log.debug("Arsenal status notification posted")
            return True
        return False

    def GetNominatedPrefix(self, user):
        return common.statistics.GetNominatedPrefix(user)

    def GetHeader(self):
        iteration = self.progress
        total = 120
        length = 25
        # form progress bar
        percent = iteration if iteration <= 120 else 120
        filledLength = int(length * percent // total)
        bar = '█' * filledLength + '-' * (length - filledLength)
        text =  ICON_ARS+" *Прогресс арсенала:* %s/120\n" % percent
        if self.rage_time:
            text += ICON_RAGE+" *Ярость в %0.2d:%0.2d*\n" % (self.rage_time.hour, self.rage_time.minute)
        text += "\n`|%s|`\n" % bar
        return text

    def GetText(self):
        text = self.GetHeader()
        # list done users
        if self.progress >= 120:
            now = datetime.datetime.now()
            text += ICON_RAGE+" %0.2d:%0.2d ГОРИТ! " % (now.hour, now.minute) +ICON_RAGE+"\n"
        text += "\n"*(len(self.done_users) != 0)
        for user in self.done_users:
            inc = self.done_users[user][0]
            count = self.done_users[user][1]
            is_fired = self.done_users[user][2]
            text += ICON_RAGE*is_fired
            text += " *+%d*" % inc
            text += " %s" % self.GetNominatedPrefix(user)
            text += user.GetString()
            text += " (x%d)\n" % count
        return text

    def Increment(self, user, value, notify=True):
        arsValue = value.replace(cb.ARS_CALLBACK_PREFIX, "")
        inc = 0
        user_fired = False # this variable is needed in order to count ars value for user even if ars is already fired now
        user_newcount = 1
        log.info("%s voted for %s" % (user, arsValue))
        if arsValue == "Cancel":
            if user in self.done_users:
                self.UndoIncrement(user)
                if hlp.NeedCheckBackup(common.current_arscheck):
                    common.current_arscheck.last_backup = datetime.datetime.now()
                    hlp.AWSCheckBackup(common.current_arscheck)
                return True
            log.error("Vote failed - user already reverted his votes")
            if hlp.NeedCheckBackup(common.current_arscheck):
                common.current_arscheck.last_backup = datetime.datetime.now()
                hlp.AWSCheckBackup(common.current_arscheck)
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
        if user in self.done_users:
            user_oldvalue = self.done_users[user][0]
            user_oldcount = self.done_users[user][1]
        user_record = [user_oldvalue+inc, user_oldcount+user_newcount, user_fired]
        log.debug("%s total impact: %s" % (user, str(user_record)))
        self.done_users[user] = user_record
        log.info("Vote successful")
        if notify:
            try:
                if not self.CheckNotifyIfFired(except_user=user) and inc != 0:
                    self.CheckNotifyIfCritical()
            except:
                pass # guide case, do nothing
        if hlp.NeedCheckBackup(common.current_arscheck):
            common.current_arscheck.last_backup = datetime.datetime.now()
            hlp.AWSCheckBackup(common.current_arscheck)
        return True

    # undo arsenal result for user if user made mistake
    def UndoIncrement(self, user):
        log.debug("%s reverting all his votes" % user)
        self.progress -= self.done_users[user][0]
        del self.done_users[user]
        if self.progress < 120:
            log.warning("Rage might've been reverted!")
            self.is_fired = False
            self.is_fire_notified = False
            self.is_postponed = False
            for user in self.done_users:
                self.done_users[user][2] = False
        log.info("Revert successful")
