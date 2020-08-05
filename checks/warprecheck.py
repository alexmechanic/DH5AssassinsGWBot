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
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    userChoice = call.data
    log.debug("User %d (%s %s) is trying to vote for pre-check (%s)" % (*user, userChoice.replace(cb.PRECHECK_CALLBACK_PREFIX, "")))
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
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    log.debug("User %d (%s %s) is trying to control pre-check" % (*user,))
    if not hlp.IsUserAdmin(user[0]):
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
    user = [q.from_user.id, q.from_user.username, q.from_user.first_name]
    log.debug("User %d (%s %s) is trying to create pre-check" % (*user,))
    if not hlp.IsUserAdmin(user[0]): # non-admins cannot post votes
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

        active = len(self.friday) + len(self.saturday) + len(self.sunday)
        activeDict = {**self.friday, **self.saturday, **self.sunday}
        if active > 0:
            text += "\n" + ICON_CALENDAR+" *%d идут:*\n" % active
        for k, v in activeDict.items():
            text += ICON_MEMBER+" "
            text += User(k, v[0], v[1]).GetString()
            text += " _("
            if k in self.friday and k in self.saturday and k in self.sunday:
                text += "все дни"
            else:
                dayPrinted = False
                if k in self.friday:
                    text += "Пт"
                    dayPrinted = True
                if k in self.saturday:
                    text += ", " * dayPrinted
                    text += "Сб"
                    dayPrinted = True
                if k in self.sunday:
                    text += ", " * dayPrinted
                    text += "Вс"
            text += ")_\n"

        if len(self.thinking) > 0:
            text += "\n" + "*%d думают:*\n" % len(self.thinking)
        for k, v in self.thinking.items():
            text += ICON_THINK + " " 
            text += User(k, v[0], v[1]).GetString() + "\n"

        if len(self.cancels) > 0:
            text += "\n" + "*%d не идут:*\n" % len(self.cancels)
        for k, v in self.cancels.items():
            text += ICON_CANCEL + " "
            text += User(k, v[0], v[1]).GetString() + "\n"

        return text

    def GetVotedText(self, user, action):
        text = "Вы "
        if action == cb.PRECHECK_FR_CALLBACK:
            if user[0] not in self.friday:
                text += "не "
            return text + "участвуете в пятницу"
        if action == cb.PRECHECK_SAT_CALLBACK:
            if user[0] not in self.saturday:
                text += "не "
            return text + "участвуете в субботу"
        if action == cb.PRECHECK_SUN_CALLBACK:
            if user[0] not in self.sunday:
                text += "не "
            return text + "участвуете в воскресенье"
        elif action == cb.PRECHECK_FULL_CALLBACK:
            return text + "участвуете все дни"
        elif action == cb.PRECHECK_THINK_CALLBACK:
            return text + "еще не решили. Постарайтесь определиться к началу ВГ!"
        elif action == cb.PRECHECK_CANCEL_CALLBACK:
            return text + "не будете участвовать в этой ВГ. Жаль"

    def CheckUser(self, user, action):
        ret = True
        log.info("User %d (%s %s) voted for %s" % (*user, action.replace(cb.PRECHECK_CALLBACK_PREFIX, "")))
        if action == cb.PRECHECK_FR_CALLBACK:
            ret = self.SetFriday(user)
        if action == cb.PRECHECK_SAT_CALLBACK:
            ret = self.SetSaturday(user)
        if action == cb.PRECHECK_SUN_CALLBACK:
            ret = self.SetSunday(user)
        elif action == cb.PRECHECK_FULL_CALLBACK:
            ret = self.SetFull(user)
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
