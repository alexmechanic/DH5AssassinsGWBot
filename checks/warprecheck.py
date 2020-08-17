#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class and methods representing pre-check for Guild war
#

import pickle
from logger import get_logger
from telebot import types

import common
from common import bot
from icons import *
from commands import COMMANDS
from statistics import User
import keyboards as kb
import callbacks as cb
import helpers as hlp

log = get_logger("bot." + __name__)

BACKUP_NAME = "WarPreCheck.BAK"

#
# Pre-check actions
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.PRECHECK_OPTIONS)
def precheck_check_user(call):
    # print("precheck_check_user")
    # print(call)
    message_id = call.inline_message_id
    user = User(call.from_user.id, call.from_user.first_name, call.from_user.username)
    userChoice = call.data
    log.debug("%s is trying to vote for pre-check (%s)" % (user, userChoice.replace(cb.PRECHECK_CALLBACK_PREFIX, "")))
    if not hlp.CanStartNewPrecheck():
        if message_id == common.current_precheck.check_id:
            ret = common.current_precheck.CheckUser(user, userChoice)
            if (ret):
                bot.edit_message_text(common.current_precheck.GetText(), inline_message_id=message_id, 
                                    parse_mode="markdown", reply_markup=kb.KEYBOARD_PRECHECK)
                bot.answer_callback_query(call.id, common.current_precheck.GetVotedText(user, userChoice))
            else:
                log.error("Failed")
                bot.answer_callback_query(call.id, "Вы уже проголосовали (%s)" % userChoice.replace(cb.PRECHECK_CALLBACK_PREFIX, ""))
            return
    log.error("Pre-check not found!")
    bot.answer_callback_query(call.id)

#
# Pre-check control
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.PRECHECK_CONTROL_OPTIONS)
def precheck_control(call):
    # print("precheck_control")
    # print(call)
    user = User(call.from_user.id, call.from_user.first_name, call.from_user.username)
    log.debug("%s is trying to control pre-check" % user)
    if not hlp.IsUserAdmin(user):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять чеком!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    if userChoice == kb.PRECHECK_CONTROL_OPTIONS[0]: # stop
        common.current_precheck.DoEndPrecheck()
        bot.edit_message_text(common.current_precheck.GetText(), inline_message_id=common.current_precheck.check_id, 
                              parse_mode="markdown")
        bot.answer_callback_query(call.id, "🏁 Чек завершен")
        return
    log.error("Pre-check not found!", "Неверный чек ВГ! Пожалуйста, создайте новый")

#
# GW pre-check creation
# (war chat inline query)
#
@bot.inline_handler(lambda query: query.query == COMMANDS["precheck"])
def precheck_query_inline(q):
    # print("precheck_query_inline")
    # print(q)
    user = User(q.from_user.id, q.from_user.first_name, q.from_user.username)
    log.debug("%s is trying to create pre-check" % user)
    if not hlp.IsUserAdmin(user): # non-admins cannot post votes
        log.error("Failed (not an admin)")
        hlp.SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    if hlp.CanStartNewPrecheck():
        res = types.InlineQueryResultArticle('precheck',
                                            title='Создать чек перед ВГ',
                                            description='🗓✅💤❌',
                                            input_message_content=types.InputTextMessageContent("📝 *Чек перед ВГ*", parse_mode="markdown"),
                                            thumb_url="https://i.ibb.co/G79HtRG/precheck.png",
                                            reply_markup=kb.KEYBOARD_PRECHECK)
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=2)
    else:
        log.error("Trying to setup another pre-check while current is not finished")
        error_text = "Уже имеется активный чек"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_precheck")


def aws_precheck_backup():
    """
    Backup  current precheck into pickle file.
    Upload to AWS
    """
    log.debug("AWS Pre-check backup started")
    with open(BACKUP_NAME, 'wb') as backup:
        pickle.dump(common.current_precheck, backup, pickle.HIGHEST_PROTOCOL)
        backup.close()
    if hlp.AWSUploadFile(BACKUP_NAME):
        log.debug("Pre-check has been successfully uploaded to AWS cloud.")
    else:
        log.error("Pre-check AWS upload failed.")

def aws_precheck_restore():
    """
    Restore  current precheck from pickle file (download from AWS).
    """
    log.debug("AWS Pre-check restore started")
    try:
        # download backup
        filepath = hlp.AWSDownloadFile(BACKUP_NAME)
        if filepath == None:
            raise Exception("Pre-check AWS download failed.")
        log.debug("Pre-check has been successfully downloaded from AWS cloud.")
        # unwrap and set object
        with open(filepath, 'rb') as f:
            common.current_precheck = pickle.load(f)
            f.close()
        log.debug("Restoring Pre-check successful (AWS)")
    except Exception as err:
        log.error("Restoring Pre-check failed (AWS): %s", str(err))



class WarPreCheck():
    check_id = None
    is_postponed = False
    daily = {}
    thinking = {}
    cancels = {}

    dayKeys = { 5: TEXT_FR, 6: TEXT_SAT, 7: TEXT_SUN }

    def __init__(self):
        self.daily = {}
        self.thinking = {}
        self.cancels = {}
        log.info("New pre-check created")

    def SetMessageID(self, message_id):
        self.check_id = message_id
        log.debug("Set inline message_id: %s" % self.check_id)

    def DoEndPrecheck(self):
        self.is_postponed = True
        aws_precheck_backup()
        log.info("Pre-check ended")

    def GetHeader(self):
        return "📝 *Чек перед ВГ:*\n"

    def GetText(self):
        text = self.GetHeader()
        text += "🛑 Голование завершено 🛑\n" * self.is_postponed

        if len(self.daily) > 0:
            text += "\n" + ICON_CALENDAR+" *%d идут:*\n" % len(self.daily)
        for user, days in self.daily.items():
            text += ICON_MEMBER+" "
            text += user.GetString()
            text += " _("
            if len(days) == 3:
                text += "все дни"
            else:
                text += ", ".join(self.dayKeys[i] for i in days)
            text += ")_\n"

        if len(self.thinking) > 0:
            text += "\n" + "*%d думают:*\n" % len(self.thinking)
        for user in self.thinking:
            text += ICON_THINK + " " 
            text += user.GetString() + "\n"

        if len(self.cancels) > 0:
            text += "\n" + "*%d не идут:*\n" % len(self.cancels)
        for user in self.cancels:
            text += ICON_CANCEL + " "
            text += user.GetString() + "\n"

        return text

    def GetVotedText(self, user, action):
        text = "Вы "
        if action == cb.PRECHECK_FR_CALLBACK:
            if user not in self.daily or 5 not in self.daily[user]:
                text += "не "
            return text + "участвуете в пятницу"
        if action == cb.PRECHECK_SAT_CALLBACK:
            if not self.daily[user] or 6 not in self.daily[user]:
                text += "не "
            return text + "участвуете в субботу"
        if action == cb.PRECHECK_SUN_CALLBACK:
            if not self.daily[user] or 7 not in self.daily[user]:
                text += "не "
            return text + "участвуете в воскресенье"
        elif action == cb.PRECHECK_FULL_CALLBACK:
            return text + "участвуете все дни"
        elif action == cb.PRECHECK_THINK_CALLBACK:
            return text + "еще не решили. Постарайтесь определиться к началу ВГ!"
        elif action == cb.PRECHECK_CANCEL_CALLBACK:
            return text + "не будете участвовать в этой ВГ"

    def CheckUser(self, user, action):
        ret = True
        log.info("User %s voted for %s" % (user, action.replace(cb.PRECHECK_CALLBACK_PREFIX, "")))
        if action in [cb.PRECHECK_FULL_CALLBACK, cb.PRECHECK_FR_CALLBACK, cb.PRECHECK_SAT_CALLBACK, cb.PRECHECK_SUN_CALLBACK]:
            ret = self.SetDaily(user, action)
        elif action == cb.PRECHECK_THINK_CALLBACK:
            ret = self.SetThinking(user)
        elif action == cb.PRECHECK_CANCEL_CALLBACK:
            ret = self.SetCancel(user)
        if ret:
            log.info("Vote successful")
        else:
            log.error("Vote failed - already voted the same")
        aws_precheck_backup()
        return ret

    def SetDaily(self, user, action):
        if action == cb.PRECHECK_FULL_CALLBACK:
            self.daily[user] = [5, 6, 7]
        else:
            daysList = [cb.PRECHECK_FR_CALLBACK, cb.PRECHECK_SAT_CALLBACK, cb.PRECHECK_SUN_CALLBACK]
            dayIndex = daysList.index(action)+5
            try: # if already checked - uncheck
                self.daily[user].remove(dayIndex)
            except: # if not - check
                try:
                    self.daily[user].append(dayIndex)
                except KeyError: # if list is empty - create one with only item
                    self.daily[user] = [dayIndex]
        if self.daily[user] == []: # empty list workaround - delete user key
            del self.daily[user]
        else: # sort days keys to stay in calendary order
            print(self.daily[user])
            self.daily[user].sort()
        # remove user from other lists
        if user in self.thinking: del self.thinking[user]
        if user in self.cancels: del self.cancels[user]
        return True

    def SetThinking(self, user):
        if user in self.thinking: # cannot think more than once
            return False
        # remove user from other lists
        if user in self.daily: del self.daily[user]
        if user in self.cancels: del self.cancels[user]
        self.thinking[user] = 1 # just a placeholder
        return True

    def SetCancel(self, user):
        if user in self.cancels: # cannot cancel more than once
            return False
        # remove user from other lists
        if user in self.daily: del self.daily[user]
        if user in self.thinking: del self.thinking[user]
        self.cancels[user] = 1
        return True
