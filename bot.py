#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# @assassinsgwbot
#

import telebot, datetime, re, json, sys, os
from icons import *
from battle import Battle
from warprecheck import WarPreCheck
from arsenal import Arsenal
from numberscheck import NumbersCheck
from commands import COMMANDS
from telebot import types
import keyboards as kb
import callbacks as cb
import helpers as hlp
from logger import get_logger
from flask import Flask, request

log = get_logger("bot")

DOUBLESHOP_TIME = [4, [17, 58], [18, 13]]
DOUBLESHOP_TIME_CALLED = False

# setup proxy if asked
if len(sys.argv) > 1:
    if sys.argv[1] == '1':
        telebot.apihelper.proxy = {'http':'http://73.55.76.54:8080'}

if "HEROKU" in list(os.environ.keys()):
    TOKEN = os.environ['TOKEN']
    log.info("[HEROKU] read token: '%s'" % TOKEN)
else:
    with open("TOKEN", "r") as tfile: # local run
        TOKEN = tfile.readline().strip('\n')
        log.info("[LOCAL] read token: '%s'" % TOKEN)
        tfile.close()

bot = telebot.TeleBot(TOKEN)

BOT_USERNAME = "assassinsgwbot"
ROOT_ADMIN = [] # creator
admins = {}

warchat_id       = None
current_battle   = None
current_precheck = None
current_arscheck = None
current_numcheck = None
rage_time_workaround = []

def CanStartNewPrecheck():
    res = current_precheck == None
    if not res:
        res = current_precheck.is_postponed
    return res

def CanStartNewBattle():
    res = current_battle == None
    if not res:
        res = current_battle.is_postponed
    return res

def CanStartNewArs():
    res = current_arscheck == None
    if not res:
        res = current_arscheck.is_fired
    return res

def CanStartNewNumbers():
    res = current_numcheck == None
    if not res:
        res = current_numcheck.is_postponed
    return res

def IsUserAdmin(message):
    if str(message.from_user.id) in admins or \
       str(message.from_user.id) == ROOT_ADMIN[0]:
        return True
    else:
        return False

def IsInPrivateChat(message):
    if message.chat.id == message.from_user.id:
        return True
    return False

def SendHelpNonAdmin(message):
    text =  "Мной могут управлять только офицеры гильдии.\n"
    text += "Обратитесь к одному из офицеров за подробностями:\n\n"
    for admin in admins:
        text += "[%s](tg://user?id=%s)\n" % (admins[admin], admin)
    bot.send_message(message.from_user.id, text, parse_mode="markdown")

#
# Manage admins list through file at start
#
# load initial list
with open("ADMINS", "r") as f:
    admins_list = json.load(f)
    ROOT_ADMIN = admins_list[0]
    admins = admins_list[1]
    f.close()
    print("Load root admin: ", ROOT_ADMIN)
    print("Load admins list: ", admins)

# save edited list
def SaveAdminsList():
    admins_list = [ROOT_ADMIN, admins]
    with open("ADMINS", "w") as f:
        json.dump(admins_list, f)
        f.close()
    print("Saved admins list: ", admins_list)

#####################
# Callback handlers #
#####################

#
# Chosen inline result handler
#
@bot.chosen_inline_handler(lambda result: True)
def chosen_inline_handler(r):
    # print("chosen_inline_handler")
    # print(r)
    user = [r.from_user.id, r.from_user.username, r.from_user.first_name]
    if r.result_id == '0': # battle check
        global current_battle
        log.debug("User %d (%s %s) created battle check (%s)" % (*user, r.query))
        times = hlp.IsCheckTimeQuery(r)[1]
        current_battle = Battle(times[0], times[1])
        current_battle.SetMessageID(r.inline_message_id)
        bot.edit_message_text(current_battle.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_CHECK)
    elif r.result_id == '1': # pre-check
        global current_precheck
        log.debug("User %d (%s %s) created pre-check" % (*user,))
        current_precheck = WarPreCheck()
        current_precheck.SetMessageID(r.inline_message_id)
        bot.edit_message_text(current_precheck.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_PRECHECK)
    elif r.result_id == '3': # ars check
        global current_arscheck
        log.debug("User %d (%s %s) created arsenal check" % (*user,))
        current_arscheck = Arsenal()
        current_arscheck.SetMessageID(r.inline_message_id)
        current_arscheck.SetRage(rage_time_workaround)
        bot.edit_message_text(current_arscheck.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_ARS)
    elif r.result_id == '4': # numbers check
        global current_numcheck
        res, numbers = hlp.IsNumbersQuery(r)
        if len(numbers) == 1:
            log.debug("User %d (%s %s) created screens numbers check (%s)" % (*user, numbers[0]))
            current_numcheck = NumbersCheck(int(numbers[0]))
            current_numcheck.SetMessageID(r.inline_message_id)
        else:
            log.debug("User %d (%s %s) created in-game numbers check (%s)" % (*user, ' '.join(str(num) for num in numbers)))
            current_numcheck = NumbersCheck(len(numbers), ingame=True, ingame_nums=numbers)
            current_numcheck.SetMessageID(r.inline_message_id)
        bot.edit_message_text(current_numcheck.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_NUMBERS)

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
    if current_precheck:
        if message_id == current_precheck.check_id:
            ret = current_precheck.CheckUser(user, userChoice)
            if (ret):
                bot.edit_message_text(current_precheck.GetText(), inline_message_id=message_id, 
                                    parse_mode="markdown", reply_markup=kb.KEYBOARD_PRECHECK)
                bot.answer_callback_query(call.id, current_precheck.GetVotedText(user, userChoice))
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
    if not IsUserAdmin(call):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять чеком!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    if userChoice == kb.PRECHECK_CONTROL_OPTIONS[0]: # stop
        current_precheck.DoEndPrecheck()
        bot.edit_message_text(current_precheck.GetText(), inline_message_id=current_precheck.check_id, 
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
    if not IsUserAdmin(q): # non-admins cannot post votes
        log.error("Failed (not an admin)")
        SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    if CanStartNewPrecheck():
        res = types.InlineQueryResultArticle('1',
                                            title='Создать чек перед ВГ',
                                            description='🗓✅💤❌',
                                            input_message_content=types.InputTextMessageContent("PRECHECK PLACEHOLDER", parse_mode="markdown"),
                                            thumb_url="https://i.ibb.co/G79HtRG/precheck.png",
                                            reply_markup=kb.KEYBOARD_PRECHECK)
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=2)
    else:
        log.error("Trying to setup another pre-check while current is not finished")
        error_text = "Уже имеется активный чек"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_precheck")

#
# Numbers progress
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.NUMBERS_OPTIONS)
def numbers_check_user(call):
    # print("numbers_check_user")
    # print(call)
    message_id = call.inline_message_id
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    log.debug("User %d (%s %s) is trying to vote for numbers (%s)" % (*user, call.data.replace(cb.NUMBERS_CALLBACK_PREFIX, "")))
    if current_numcheck:
        if message_id == current_numcheck.check_id:
            ret = current_numcheck.CheckUser(user, call.data)
            if (ret):
                if not current_numcheck.is_1000: # if reached 1000 - no need to continue numbers check
                    bot.edit_message_text(current_numcheck.GetText(), inline_message_id=message_id, 
                                        parse_mode="markdown", reply_markup=kb.KEYBOARD_NUMBERS)
                else:
                    current_numcheck.DoEndCheck()
                    bot.edit_message_text(current_numcheck.GetText(), inline_message_id=message_id, 
                                        parse_mode="markdown")
            bot.answer_callback_query(call.id)
            return
    log.error("Numbers check not found!")
    bot.answer_callback_query(call.id, "Неверный чек номеров! Пожалуйста, создайте новый")

#
# Numbers check control
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.NUMBERS_CONTROL_OPTIONS)
def numbers_control(call):
    # print("numbers_control")
    # print(call)
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    log.debug("User %d (%s %s) is trying to control numbers check" % (*user,))
    if not IsUserAdmin(call):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять чеком номеров!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    if current_numcheck:
        if userChoice == kb.NUMBERS_CONTROL_OPTIONS[0]: # make 500
            current_numcheck.Do500()
            bot.edit_message_text(current_numcheck.GetText(),
                                  inline_message_id=current_numcheck.check_id,
                                  parse_mode="markdown", reply_markup=kb.KEYBOARD_NUMBERS)
            bot.answer_callback_query(call.id, "Отмечено "+ICON_500)
            return
        elif userChoice == kb.NUMBERS_CONTROL_OPTIONS[1]: # make 1000
            current_numcheck.Do1000()
            bot.edit_message_text(current_numcheck.GetText(),
                                  inline_message_id=current_numcheck.check_id,
                                  parse_mode="markdown")
            bot.answer_callback_query(call.id, "Отмечено "+ICON_1000)
            return
        elif userChoice == kb.NUMBERS_CONTROL_OPTIONS[2]: # stop
            current_numcheck.DoEndCheck()
            bot.edit_message_text(current_numcheck.GetText(),
                                  inline_message_id=current_numcheck.check_id,
                                  parse_mode="markdown")
            bot.answer_callback_query(call.id, "🏁 Чек номеров завершен")
            return
        else:
            log.error("invalid action!")
            bot.answer_callback_query(call.id, "Неверныая команда! Пожалуйста, обратитесь к администратору бота")
    log.error("Numbers check not found!")
    bot.answer_callback_query(call.id, "Неверный чек номеров! Пожалуйста, создайте новый")

#
# Numbers check creation
# (war chat inline query)
#
@bot.inline_handler(lambda query: query.query[:len(COMMANDS["numbers"])] == COMMANDS["numbers"])
def numbers_query_inline(q):
    # print("numbers_query_inline")
    # print(q)
    user = [q.from_user.id, q.from_user.username, q.from_user.first_name]
    log.debug("User %d (%s %s) is trying to create numbers check" % (*user,))
    if not IsUserAdmin(q): # non-admins cannot post votes
        log.error("Failed (not an admin)")
        SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    if CanStartNewBattle():
        log.error("Trying to setup numbers check with no current battle")
        error_text = "Отсутствует активный бой"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")
        return
    res, numbers = hlp.IsNumbersQuery(q)
    if res:
        if CanStartNewNumbers():
            text = 'Добавить прогресс номеров'
            if len(numbers) == 1:
                text2 = 'по скринам (%s)' % numbers[0]
                kb.SetupNumbersKeyboard(count=int(numbers[0]))
            else:
                text2 = 'по игре (%s)' % ' '.join(str(num) for num in numbers)
                kb.SetupNumbersKeyboard(ingame_nums=numbers)
            res = types.InlineQueryResultArticle('4',
                                                 title=text,
                                                 description=text2,
                                                 input_message_content=types.InputTextMessageContent("NUMBERS PLACEHOLDER", parse_mode="markdown"),
                                                 thumb_url="https://i.ibb.co/JRRMLjv/numbers.png",
                                                 reply_markup=kb.KEYBOARD_NUMBERS
                                                 )
            bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=2)
        elif not CanStartNewNumbers():
            log.error("Trying to setup another numbers check while current has not reached 500/1000")
            error_text = "Уже имеется активный чек номеров"
            bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                    switch_pm_text=error_text, switch_pm_parameter="existing_numbers")
    else:
        log.error("Failed (invalid query)")
        error_text = "Неверный формат запроса"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_numbers")

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
    if current_battle:
        if message_id == current_battle.check_id:
            ret = current_battle.CheckUser(user, userChoice)
            if (ret):
                markup = kb.KEYBOARD_CHECK
                if current_battle.is_rolling:
                    markup = kb.KEYBOARD_CHECK_ROLLED
                elif current_battle.is_started:
                    markup = kb.KEYBOARD_LATE
                bot.edit_message_text(current_battle.GetText(), inline_message_id=message_id, 
                                    parse_mode="markdown", reply_markup=markup)
                bot.answer_callback_query(call.id, current_battle.GetVotedText(userChoice))
                if warchat_id:
                    if userChoice == cb.CHECK_LATE_CALLBACK:
                        text = ICON_LATE + " [%s (%s)](tg://user?id=%d) Пришел на бой!\n" % (user[1], user[2], user[0])
                        bot.send_message(warchat_id, text, parse_mode="markdown", disable_notification=True)
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
    if not IsUserAdmin(call):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять боем!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    if current_battle:
        notification_text = ""
        if userChoice == kb.CHECK_CONTROL_OPTIONS[0]: # roll
            current_battle.DoRollBattle()
            notification_text = ICON_ROLL+" Крутит"
            KEYBOARD_CHECK_CURRENT = kb.KEYBOARD_CHECK_ROLLED
            bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id,
                                  parse_mode="markdown", reply_markup=kb.KEYBOARD_CHECK_ROLLED)
            bot.answer_callback_query(call.id, notification_text)
            current_battle.BattleRollNotifyActiveUsers(bot)
        elif userChoice == kb.CHECK_CONTROL_OPTIONS[1]: # start
            current_battle.DoStartBattle()
            notification_text = ICON_SWORDS+" Бой запущен"
            KEYBOARD_CHECK_CURRENT = kb.KEYBOARD_LATE
            bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id,
                                  parse_mode="markdown", reply_markup=kb.KEYBOARD_LATE)
            bot.answer_callback_query(call.id, notification_text)
            current_battle.BattleStartNotifyActiveUsers(bot)
        elif userChoice == kb.CHECK_CONTROL_OPTIONS[2]: # stop
            reset_control(call)
            notification_text = ICON_FINISH+" Бой завершен"
            bot.answer_callback_query(call.id, notification_text)
        global warchat_id
        if warchat_id:
            notification = bot.send_message(warchat_id, notification_text, disable_notification=False)
            if userChoice != kb.CHECK_CONTROL_OPTIONS[2]: # stop
                bot.pin_chat_message(notification.chat.id, notification.message_id, disable_notification=False)
            else:
                bot.unpin_chat_message(warchat_id)
            log.debug("Battle status notification posted")
        else:
            log.error("War chat_id is not set, cannot post battle status notification!")
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
    if not IsUserAdmin(q): # non-admins cannot post votes
        log.error("Failed (not an admin)")
        SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    times = hlp.IsCheckTimeQuery(q)[1]
    if CanStartNewBattle():
        res = types.InlineQueryResultArticle('0',
                                            title='[%s/%s] Создать чек на бой' % (times[0], times[1]),
                                            description='✅🔥🚽📦💤❌',
                                            input_message_content=types.InputTextMessageContent("BATTLE PLACEHOLDER", parse_mode="markdown"),
                                            thumb_url="https://i.ibb.co/jb9nVCm/battle.png",
                                            reply_markup=kb.KEYBOARD_CHECK)
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=2)
    else:
        log.error("Trying to setup another battle while current is not finished")
        error_text = "Уже имеется активный бой в %0.2d:%0.2d" \
                     % (current_battle.time["start"].hour, current_battle.time["start"].minute)
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")

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
    if current_arscheck:
        if message_id == current_arscheck.check_id:
            ret = current_arscheck.Increment(user, userChoice)
            if (ret):
                bot.edit_message_text(current_arscheck.GetText(), inline_message_id=message_id,
                                    parse_mode="markdown", reply_markup=kb.KEYBOARD_ARS)
                current_arscheck.CheckNotifyIfFired(current_battle, bot)
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
    if not IsUserAdmin(call):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять чеком арсенала!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    if userChoice == kb.ARS_CONTROL_OPTIONS[0]: # stop
        if (current_arscheck):
            current_arscheck.DoEndArsenal()
            bot.edit_message_text(current_arscheck.GetText(),
                                  inline_message_id=current_arscheck.check_id,
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
    if not IsUserAdmin(q): # non-admins cannot post votes
        log.error("Failed (not an admin)")
        SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    if CanStartNewBattle():
        log.error("Trying to setup arsenal check with no current battle")
        error_text = "Отсутствует активный бой"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")
        return
    rage = hlp.IsArsQuery(q)
    if rage[0]:
        if CanStartNewArs():
            global rage_time_workaround
            rage_time_workaround = rage[1][0]
            res = types.InlineQueryResultArticle('3',
                                                 title='Добавить прогресс арса',
                                                 description='📦 |████--| Х/120\nЯрость в %s' % rage_time_workaround,
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

####################
# Command handlers #
####################

#
# Help command
# (private bot chat)
#
@bot.message_handler(commands=["help"])
def show_help(m):
    userid = m.from_user.id
    text =  ICON_SWORDS+" Привет! Я военный бот гильдии *Assassins*\n"
    text += "🎮 Игра: *Dungeon Hunter V*"
    text += "\n\n📃 *Список моих команд*:\n"
    text += "/help - вывод этой справки\n"
    text += "/admins - вывод списка офицеров\n"
    if IsUserAdmin(m):
        text += "/warchat - запомнить военный чат (для отправки сообщений боя)\n"
        text += "/reset - аварийный сброс бота\n"
        text += "\n*При наличии текущего боя:*\n"
        text += "/bstart - начать бой\n"
        text += "/bstop  - завершить/отменить бой\n"
        text += "/checklist  - получить список всех участвующих в текущем бою\n"
        if str(userid) == ROOT_ADMIN[0]:
            text += "/setadmins обновить список офицеров (в военном чате)\n"
        text += "\n*В военном чате:*\n" + \
                "_@assassinsgwbot чек_ - создать чек перед ВГ\n" + \
                "_@assassinsgwbot XX:XX YY:YY_ - создать чек на бой (разделительные символы могут быть любыми, даже пробелом)\n" + \
                "_@assassinsgwbot арс XX:XX_ - создать чек арсенала (при наличии боя)\n" + \
                "_@assassinsgwbot номера X_ - создать чек Х номеров по скринам (при наличии боя)\n" + \
                "_@assassinsgwbot номера X Y Z ..._ - создать чек перечисленных номеров по игре (при наличии боя)"
    else:
        pass # stub for adding only non-admin help
    bot.send_message(userid, text, parse_mode="markdown")
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
    bot.delete_message(m.chat.id, m.message_id)

#
# Start pending battle
# (private bot chat)
#
@bot.message_handler(commands=['warchat'])
def command_set_warchat(m):
    if IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    global warchat_id
    if warchat_id != None:
        bot.send_message(m.from_user.id, ICON_CANCEL+" Военный чат уже задан!")
    else:
        warchat_id = m.chat.id
        bot.send_message(m.from_user.id, ICON_CHECK+" Военный чат успешно задан!")


#
# Start utility command
# (private bot chat)
#
@bot.message_handler(commands=['start'])
def command_start(m):
    # print("command_start")
    # print(m)
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    inline_error = m.text.replace("/start ", "")
    if inline_error != "":
        if inline_error == "existing_precheck":
            text =  "Уже имеетя активный чек перед ВГ.\n\n" + \
                    ("Чтобы начать чек перед ВГ заново, необходимо остановить (%s) предыдущий.\n" % ICON_STOP) + \
                    "Если чек был назначен ошибочно - завершите чек, " + \
                    "затем создайте новый, а старое сообщение удалите."
            bot.send_message(m.chat.id, text)
        elif inline_error == "existing_battle":
            if not CanStartNewBattle():
                text =  "Текущий бой: %0.2d:%0.2d / %0.2d:%0.2d.\n\n" \
                        % (current_battle.time["check"].hour, current_battle.time["check"].minute,
                           current_battle.time["start"].hour, current_battle.time["start"].minute)
                text += ("Чтобы начать новый бой, необходимо завершить (%s) предыдущий.\n" % ICON_STOP) + \
                         "Если бой был назначен ошибочно - остановите бой, " + \
                         "затем создайте новый, а старое сообщение удалите."
                bot.send_message(m.chat.id, text)
            else:
                hlp.SendHelpNoBattle(m.chat.id, bot)
        elif inline_error == "existing_arsenal":
            text =  "Уже имеетя активный чек арсенала\n\n" + \
                    ("Чтобы начать чек арсенала заново, необходимо поджечь (%s) или остановить (%s) текущий.\n" % (ICON_RAGE, ICON_STOP)) + \
                    "Если чек арса был добавлен ошибочно (или ярость не была задействована в предыдущем бое) - " + \
                    "остановите чек, затем создайте новый, а старое сообщение удалите."
            bot.send_message(m.chat.id, text)
        elif inline_error == "existing_numbers":
            text =  "Уже имеетя активный чек номеров\n\n" + \
                    ("Чтобы начать чек номеров заново, необходимо достичь хотя бы '500' или остановить (%s) его.\n" % ICON_STOP) + \
                    "Если чек номеров был добавлен ошибочно (или не было сделано хотя бы '500') - " + \
                    "остановите чек, затем создайте новый, а старое сообщение удалите."
            bot.send_message(m.chat.id, text)


#
# Start pending battle
# (private bot chat)
#
@bot.message_handler(commands=['bstart'])
def command_battle_start(m):
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    if not CanStartNewBattle():
        if not current_battle.is_started:
            text = "Запустить текущий бой [%0.2d:%0.2d]?" \
                    % (current_battle.time["start"].hour, current_battle.time["start"].minute)
            bot.send_message(m.chat.id, text, reply_markup=kb.KEYBOARD_START)
        else:
            bot.send_message(m.chat.id, "Бой уже запущен")
    else:
        hlp.SendHelpNoBattle(m.chat.id, bot)

#
# Stop current battle
# (private bot chat)
#
@bot.message_handler(commands=['bstop'])
def command_battle_stop(m):
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    if not CanStartNewBattle():
        if not current_battle.is_postponed:
            text = "Завершить текущий бой [%0.2d:%0.2d]?" \
                    % (current_battle.time["start"].hour, current_battle.time["start"].minute)
            bot.send_message(m.chat.id, text, reply_markup=kb.KEYBOARD_STOP)
        else:
            bot.send_message(m.chat.id, "Бой уже завершен")
    else:
        hlp.SendHelpNoBattle(m.chat.id, bot)

#
# Get check list for current battle
# (private bot chat)
#
@bot.message_handler(commands=['checklist'])
def command_battle_checklist(m):
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    if not CanStartNewBattle():
        checklist = ""
        for user in current_battle.GetActiveUsersNames():
            checklist += user + "\n"
        bot.send_message(m.chat.id, checklist)
    else:
        hlp.SendHelpNoBattle(m.chat.id, bot)

#
# Update bot admins list
# (war chat where admins reside)
#
@bot.message_handler(commands=["setadmins"])
def setup_admins(m):
    global admins
    # print("setup_admins")
    # print(m)
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to update admins list" % (*user,))
    if not IsUserAdmin(m):
        log.error("Failed (not an admin)")
        SendHelpNonAdmin(m)
        return
    if IsInPrivateChat(m):
        log.error("Failed (in private chat)")
        bot.send_message(user[0], "Используйте команду /setadmins в военном чате, чтобы обновить список офицеров!")
        return
    is_chat_admin = False
    chat_admins = bot.get_chat_administrators(m.chat.id)
    for admin in chat_admins:
        if admin.user.id == user[0]:
            is_chat_admin = True
            break
    if not is_chat_admin:
        log.error("Failed (not a chat admin)")
        SendHelpNonAdmin(m)
        return
    admins = {}
    for admin in chat_admins:
        if str(admin.user.id) != ROOT_ADMIN[0] and admin.user.username != BOT_USERNAME:
            name_record = admin.user.first_name
            if admin.user.username != None:
                name_record += " (" + admin.user.username + ")"
            admins[str(admin.user.id)] = name_record
    SaveAdminsList()
    bot.send_message(m.chat.id, "👮🏻‍♂️ Список офицеров обновлен")
    log.info("Admins list updated")

#
# Manage admins
# (private bot chat)
#
@bot.message_handler(commands=["admins"])
def manage_admins(m):
    # print("manage_admins")
    # print(m)
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to check admins list" % (*user,))
    if not IsInPrivateChat(m):
        bot.delete_message(m.chat.id, m.message_id)
        bot.send_message(user[0], "Используйте команду /admins в личном чате, чтобы посмотреть список офицеров!")
        return
    text =  "Список офицеров:\n\n"
    text += "👁 %s _[администратор бота]_\n" % ROOT_ADMIN[1]
    for admin in admins:
        if BOT_USERNAME not in admin or admin != ROOT_ADMIN[1]:
            if str(user[0]) == ROOT_ADMIN[0]: # show admins IDs for root admin
                text += ICON_MEMBER+" %s _(ID=%s)_\n" % (admins[admin], admin)
            else:
                text += (ICON_MEMBER+" %s\n" % admins[admin])
    bot.send_message(user[0], text, parse_mode="markdown")
    return

#
# Emergency reset all checks
# (private bot chat)
#
@bot.message_handler(commands=['reset'])
def command_reset(m):
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to reset bot" % (*user,))
    bot.send_message(m.chat.id, "Выполнить полный сброс?", reply_markup=kb.KEYBOARD_RESET)

#
# Emergency reset control
# (private bot chat)
#
@bot.message_handler(func=lambda message: message.text in kb.RESET_CONTROL_OPTIONS)
def reset_control(m):
    try:
        if not IsInPrivateChat(m): return
    except: # issue when resetting checks via battle stop. could be ignored
        pass
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
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
        global current_precheck, current_battle, current_arscheck, current_numcheck
        if current_precheck:
            current_precheck.DoEndPrecheck()
            bot.edit_message_text(current_precheck.GetText(), inline_message_id=current_precheck.check_id,
                                  parse_mode="markdown")
            current_precheck = None
        if current_battle:
            current_battle.DoEndBattle()
            bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id,
                                  parse_mode="markdown")
            current_battle = None
        if current_arscheck:
            current_arscheck.DoEndArsenal()
            bot.edit_message_text(current_arscheck.GetText(), inline_message_id=current_arscheck.check_id,
                                  parse_mode="markdown")
            current_arscheck = None
        if current_numcheck:
            current_numcheck.DoEndCheck()
            bot.edit_message_text(current_numcheck.GetText(), inline_message_id=current_numcheck.check_id,
                                  parse_mode="markdown")
            current_numcheck = None
    try:
        bot.send_message(m.from_user.id, "✅ Бот успешно сброшен", reply_markup=markup)
    except: # no need to send private message if checks have been reset via battle control
        pass
    log.debug("Reset successful")

#
# Battle control (from bot private chat)
#
@bot.message_handler(func=lambda message: message.text in kb.CHECK_CONTROL_OPTIONS_PRIVATE)
def battle_control(m):
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    markup = types.ReplyKeyboardRemove(selective=False)
    if m.text == kb.buttonStartPrivate.text:
        current_battle.DoStartBattle()
        bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_LATE)
        bot.send_message(m.chat.id, "✅ Бой успешно запущен", reply_markup=markup)
        current_battle.BattleStartNotifyActiveUsers(bot)
    elif m.text == kb.buttonStopPrivate.text:
        reset_control(m)
        bot.send_message(m.chat.id, "❎ Бой успешно завершен", reply_markup=markup)
    else: # Отмена
        bot.send_message(m.chat.id, "⛔️ Действие отменено", reply_markup=markup)


if "HEROKU" in list(os.environ.keys()):
    log.warning("Running on Heroku, setup webhook")
    server = Flask(__name__)

    @server.route('/bot' + TOKEN, methods=['POST'])
    def getMessage():
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200

    @server.route("/")
    def webhook():
        sleep(1)
        bot.set_webhook(url='https://' + BOT_USERNAME + '.herokuapp.com/bot' + TOKEN)
        return "?", 200
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 80)))
else:
    log.warning("Running locally, start polling")
    bot.remove_webhook()
    bot.polling(none_stop=True, interval=0, timeout=20)
