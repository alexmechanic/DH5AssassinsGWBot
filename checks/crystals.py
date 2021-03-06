#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class and methods representing check for remaining crystals
#

import datetime
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
BACKUP_NAME = "Crystals.BAK"

#
# Crystals check
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.CRYSTALS_OPTIONS)
def crystals_check_user(call):
    # print("crystals_check_user")
    # print(call)
    message_id = call.inline_message_id
    user = User(call.from_user.id, call.from_user.first_name, call.from_user.username)
    userChoice = call.data
    log.debug("%s is trying to vote for crystals (%s)" % (user, userChoice.replace(cb.CRYSTALS_CALLBACK_PREFIX, "")))
    if not hlp.CanStartNewCryscheck():
        if message_id == common.current_cryscheck.check_id:
            ret = common.current_cryscheck.CheckUser(user, userChoice)
            if (ret):
                bot.edit_message_text(common.current_cryscheck.GetText(), inline_message_id=message_id, 
                                    parse_mode="markdown", reply_markup=kb.KEYBOARD_CRYSTALS)
                bot.answer_callback_query(call.id, common.current_cryscheck.GetVotedText(user, userChoice))
            else:
                log.error("Failed")
                bot.answer_callback_query(call.id, "Вы уже проголосовали (%s)" % userChoice.replace(cb.CRYSTALS_CALLBACK_PREFIX, ""))
            return
    log.error("Crystals check not found!")
    bot.answer_callback_query(call.id, "Неверный чек по кри! Пожалуйста, создайте новый")

#
# Crystals control
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.CRYSTALS_CONTROL_OPTIONS)
def crystals_control(call):
    # print("crystals_control")
    # print(call)
    user = User(call.from_user.id, call.from_user.first_name, call.from_user.username)
    log.debug("%s is trying to control crystals check" % user)
    if not hlp.IsUserAdmin(user):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять чеком!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    if userChoice == kb.CRYSTALS_CONTROL_OPTIONS[0]: # stop
        common.current_cryscheck.DoEndCryscheck()
        bot.edit_message_text(common.current_cryscheck.GetText(), inline_message_id=common.current_cryscheck.check_id, 
                              parse_mode="markdown")
        bot.answer_callback_query(call.id, "🏁 Чек завершен")
        return
    log.error("Crystals check not found!")
    bot.answer_callback_query(call.id, "Неверный чек по кри! Пожалуйста, создайте новый")

#
# Crystals check creation
# (war chat inline query)
#
@bot.inline_handler(lambda query: query.query == COMMANDS["crystals"])
def crystals_query_inline(q):
    # print("crystals_query_inline")
    # print(q)
    user = User(q.from_user.id, q.from_user.first_name, q.from_user.username)
    log.debug("%s is trying to create crystals check" % user)
    if not hlp.IsUserAdmin(user): # non-admins cannot post votes
        log.error("Failed (not an admin)")
        hlp.SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    if hlp.CanStartNewCryscheck():
        ranges = common.settings.GetSetting("crystals_ranges")
        kb.SetupCrystalsKeyboard(maxvalue=ranges[0], step=ranges[1])
        res = types.InlineQueryResultArticle('cryscheck',
                                            title='Создать чек по кри',
                                            description='0 - %d, шаг %d' % ranges,
                                            input_message_content=types.InputTextMessageContent(ICON_CRYSTAL+" *Чек по кри*", parse_mode="markdown"),
                                            thumb_url="https://i.ibb.co/b7XSWQr/crystal.png",
                                            reply_markup=kb.KEYBOARD_CRYSTALS)
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=2)
    else:
        log.error("Trying to setup another crystals check while current is not finished")
        error_text = "Уже имеется активный чек по кри"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_crystals")


def aws_crystals_backup():
    """
    Backup current crystals into pickle file.
    Upload to AWS
    """
    log.debug("AWS Crystals check backup started")
    with open(BACKUP_NAME, 'wb') as backup:
        pickle.dump(common.current_cryscheck, backup, pickle.HIGHEST_PROTOCOL)
        backup.close()
    if hlp.AWSUploadFile(BACKUP_NAME):
        log.debug("Crystals check has been successfully uploaded to AWS cloud.")
    else:
        log.error("Crystals check AWS upload failed.")

def aws_crystals_restore():
    """
    Restore current crystals from pickle file (download from AWS).
    """
    log.debug("AWS Crystals check restore started")
    try:
        # download backup
        filepath = hlp.AWSDownloadFile(BACKUP_NAME)
        if filepath == None:
            raise Exception("Crystals check AWS download failed.")
        log.debug("Crystals check has been successfully downloaded from AWS cloud.")
        # unwrap and set object
        with open(filepath, 'rb') as f:
            common.current_cryscheck = pickle.load(f)
            f.close()
        # restore crystals keyboard
        kb.SetupCrystalsKeyboard(maxvalue=common.current_cryscheck.max, step=common.current_cryscheck.step)
        log.debug("Restoring Crystals check successful (AWS)")
    except Exception as err:
        log.error("Restoring Crystals check failed (AWS): %s", str(err))


class Crystals():
    check_id = None
    is_postponed = False
    max = 0
    step = 0
    users = {} # {range string "A - B": [User]}

    def __init__(self, ranges):
        self.max = int(ranges[0])
        self.step = int(ranges[1])
        self.users = {}
        value = (0, self.step-1)
        # calculate avaliable keys for choices
        keys = []
        while value[1] <= self.max:
            key = "%d-%d" % value
            keys.append(key)
            value = (value[1]+1, value[1]+self.step)
        # do not forget remainder
        if self.max % self.step:
            value = (value[0]+1, self.max)
            key = "%d-%d" % value
            keys.append(key)
        # add one key for more than max value
        key = "%d+" % self.max
        keys.append(key)
        # setup dict for keys
        for key in keys:
            self.users[key] = []
        log.info("New crystals check created")

    def SetMessageID(self, message_id):
        self.check_id = message_id
        log.debug("Set inline message_id: %s" % self.check_id)

    def DoEndCryscheck(self):
        self.is_postponed = True
        aws_crystals_backup()
        log.info("Crystals check ended")

    def GetHeader(self):
        return ICON_CRYSTAL+" *Чек по кри:*\n"

    def GetText(self):
        text = self.GetHeader()
        text += "🛑 Голование завершено 🛑\n" * self.is_postponed

        for step in self.users:
            if len(self.users[step]) > 0:
                text += "\n*%s (%d):*\n" % (step, len(self.users[step]))
                for user in self.users[step]:
                    text += ICON_MEMBER + " "
                    text += user.GetString() + "\n"
        return text

    def GetVotedText(self, user, action):
        text = "Вы отметили '"
        for step in self.users:
            if user in self.users[step]:
                return text + step + "'"
        return None

    def CheckUser(self, user, action):
        ret = True
        action = action.replace(cb.CRYSTALS_CALLBACK_PREFIX, "")
        log.info("User %d (%s %s) voted for %s" % (user._id, user.name, user.username, action))
        if user in self.users[action]:
            log.error("Vote failed - already voted the same")
            ret = False
        else:
            for step in self.users:
                try:
                    self.users[step].remove(user)
                    break
                except ValueError:
                    pass # do not react if user is not in list
            self.users[action].append(user)
            log.info("Vote successful")
        if ret:
            aws_crystals_backup()
        return ret
