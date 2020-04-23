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

current_battle   = None
current_precheck = None
current_arscheck = None
current_numcheck = None

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
    elif r.result_id == '2': # send urgent message
        log.debug("User %d (%s %s) sent urgent message to war chat" % (*user,))
        bot.send_message(r.from_user.id, "Пожалуйста, не забывайте, что " +
                         "отправлять в военный чат следует только особо важные сведения!")
    elif r.result_id == '3': # ars check
        global current_arscheck
        log.debug("User %d (%s %s) created arsenal check" % (*user,))
        current_arscheck = Arsenal()
        current_arscheck.SetMessageID(r.inline_message_id)
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
# GW Pre-check
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

@bot.inline_handler(lambda query: query.query == "чек")
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
                                            'Создать чек перед ВГ ✅💤❌', 
                                            types.InputTextMessageContent("PRECHECK PLACEHOLDER", parse_mode="markdown"),
                                            reply_markup=kb.KEYBOARD_PRECHECK)
        bot.answer_inline_query(q.id, [res], is_personal=True)
    else:
        log.error("Trying to setup another pre-check while current is not finished")
        error_text = "Уже имеется активный чек"
        bot.answer_inline_query(q.id, [], is_personal=True,
                                switch_pm_text=error_text, switch_pm_parameter="existing_precheck")

#
# Numbers progress for battle
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
            if not current_numcheck.is_1000:
                ret = current_numcheck.CheckUser(user, call.data)
                if (ret):
                    bot.edit_message_text(current_numcheck.GetText(), inline_message_id=message_id, 
                                        parse_mode="markdown", reply_markup=kb.KEYBOARD_NUMBERS)
            bot.answer_callback_query(call.id)
            return
    log.error("Numbers check not found!")
    bot.answer_callback_query(call.id, "Неверный чек номеров! Пожалуйста, создайте новый")

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
        if userChoice == kb.NUMBERS_CONTROL_OPTIONS[0]: # stop
            current_numcheck.DoEndCheck()
            bot.edit_message_text(current_numcheck.GetText(),
                                  inline_message_id=current_numcheck.check_id,
                                  parse_mode="markdown")
            bot.answer_callback_query(call.id, "🏁 Чек номеров завершен")
            return
    log.error("Numbers check not found!")
    bot.answer_callback_query(call.id, "Неверный чек номеров! Пожалуйста, создайте новый")

@bot.inline_handler(lambda query: query.query[:4] == "номера")
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
        bot.answer_inline_query(q.id, [], is_personal=True,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")
        return
    res, numbers = hlp.IsNumbersQuery(q)
    if res:
        if CanStartNewNumbers():
            text = 'Добавить прогресс номеров '
            if len(numbers) == 1:
                text += 'по скринам (%s)' % numbers[0]
                kb.SetupNumbersKeyboard(count=int(numbers[0]))
            else:
                text += 'по игре (%s)' % ' '.join(str(num) for num in numbers)
                kb.SetupNumbersKeyboard(ingame_nums=numbers)
            res = types.InlineQueryResultArticle('4',
                                                 text,
                                                 types.InputTextMessageContent("NUMBERS PLACEHOLDER", parse_mode="markdown"),
                                                 reply_markup=kb.KEYBOARD_NUMBERS
                                                 )
            bot.answer_inline_query(q.id, [res], is_personal=True)
        elif not CanStartNewNumbers():
            log.error("Trying to setup another numbers check while current has not reached 500/1000")
            error_text = "Уже имеется активный чек номеров"
            bot.answer_inline_query(q.id, [], is_personal=True,
                                    switch_pm_text=error_text, switch_pm_parameter="existing_numbers")
    else:
        log.error("Failed (invalid query)")
        error_text = "Неверный формат запроса"
        bot.answer_inline_query(q.id, [], is_personal=True,
                                switch_pm_text=error_text, switch_pm_parameter="existing_numbers")

#
# Battle check
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
                if current_battle.is_started:
                    markup = kb.KEYBOARD_LATE
                bot.edit_message_text(current_battle.GetText(), inline_message_id=message_id, 
                                    parse_mode="markdown", reply_markup=markup)
                bot.answer_callback_query(call.id, current_battle.GetVotedText(userChoice))
            else:
                log.error("Failed")
                bot.answer_callback_query(call.id, "Вы уже проголосовали (%s)" % userChoice.replace(cb.CHECK_CALLBACK_PREFIX, ""))
            return
    log.error("Battle not found!")
    bot.answer_callback_query(call.id, "Неверный чек боя! Пожалуйста, создайте новый")

#
# Battle control (from war inline chat)
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
        if userChoice == kb.CHECK_CONTROL_OPTIONS[0]: # start
            current_battle.DoStartBattle()
            bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                                  parse_mode="markdown", reply_markup=kb.KEYBOARD_LATE)
            bot.answer_callback_query(call.id, "⚔️ Бой запущен")
            current_battle.BattleStartNotifyActiveUsers(bot)
            return
        elif userChoice == kb.CHECK_CONTROL_OPTIONS[1]: # stop
            current_battle.DoEndBattle()
            bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                                  parse_mode="markdown")
            bot.answer_callback_query(call.id, "🏁 Бой завершен")
            return
    log.error("Battle not found!")
    bot.answer_callback_query(call.id, "Неверный чек боя! Пожалуйста, создайте новый")

#
# Battle check creation (war inline chat query)
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
                                            '[%s/%s] Создать чек на бой ✅💤❌' % (times[0], times[1]), 
                                            types.InputTextMessageContent("BATTLE PLACEHOLDER", parse_mode="markdown"),
                                            reply_markup=kb.KEYBOARD_CHECK)
        bot.answer_inline_query(q.id, [res], is_personal=True)
    else:
        log.error("Trying to setup another battle while current is not finished")
        error_text = "Уже имеется активный бой в %0.2d:%0.2d" \
                     % (current_battle.time["start"].hour, current_battle.time["start"].minute)
        bot.answer_inline_query(q.id, [], is_personal=True,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")

#
# Arsenal progress for battle
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
# Arsenal creation (war inline chat)
#
@bot.inline_handler(lambda query: query.query[:3] == "арс")
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
        bot.answer_inline_query(q.id, [], is_personal=True,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")
        return
    if CanStartNewArs():
        res = types.InlineQueryResultArticle('3',
                                             'Добавить прогресс арса 📦 |████--| Х/120',
                                             types.InputTextMessageContent("ARS PLACEHOLDER", parse_mode="markdown"),
                                             reply_markup=kb.KEYBOARD_ARS)
        bot.answer_inline_query(q.id, [res], is_personal=True)
    else:
        log.error("Trying to setup another arsenal check while current has not been fired")
        error_text = "Уже имеется активный чек арсенала"
        bot.answer_inline_query(q.id, [], is_personal=True,
                                switch_pm_text=error_text, switch_pm_parameter="existing_arsenal")

#
# Urgent message from non-admin user
#
@bot.inline_handler(lambda query: query.query[:3] == "!!!")
def urgent_query_inline(q):
    # print("urgent_query_inline")
    # print(q)
    user = [q.from_user.id, q.from_user.username, q.from_user.first_name]
    log.debug("User %d (%s %s) is trying to create send urgent message (%s)" % (*user, q.query))
    if IsUserAdmin(q): # non-admins cannot post votes
        log.error("Failed (is admin)")
        bot.send_message(q.from_user.id, "Офицеры могут писать сообщения в чат напрямую")
        bot.answer_callback_query(q.id)
        return
    text =  "[%s (%s)](tg://user?id=%d):" % (q.from_user.first_name, q.from_user.username, q.from_user.id)
    message = q.query.replace("!!!", "")
    if message != "" or message != " ":
        text += message
        urgent_message = types.InputTextMessageContent(text, parse_mode="markdown")
        res = types.InlineQueryResultArticle('2',
                                             '‼️ Отправить срочное сообщение', 
                                             urgent_message)
        bot.answer_inline_query(q.id, [res], is_personal=True)
    else:
        log.error("Failed (invalid query)")
        error_text = "Неверный формат запроса"
        bot.answer_inline_query(q.id, [], is_personal=True,
                                switch_pm_text=error_text, switch_pm_parameter="urgent_message")

####################
# Command handlers #
####################
@bot.message_handler(commands=["help"])
def show_help(m):
    userid = m.from_user.id
    text =  ICON_SWORDS+" Привет! Я военный бот гильдии *Assassins*\n"
    text += "🎮 Игра: *Dungeon Hunter V*"
    text += "\n\n📃 *Список моих команд*:\n"
    text += "/help - вывод этой справки\n"
    if IsUserAdmin(m):
        text += "/бой - вывод информации о текущем бое (если есть).\n"
        text += "/admin list - вывод текущего списка офицеров\n"
        text += "\n*При наличии текущего боя:*\n"
        text += "/старт - начать бой\n"
        text += "/стоп  - завершить/отменить бой\n"
        if str(userid) == ROOT_ADMIN[0]:
            text += "/setadmins обновить список офицеров (в военном чате)\n"
        text += "\n*В военном чате:*\n" + \
                "_@assassinsgwbot чек_ - создать чек перед ВГ\n" + \
                "_@assassinsgwbot XX:XX YY:YY_ - создать чек на бой\n" + \
                "_@assassinsgwbot арс_ - создать чек арсенала (при наличии боя)\n" + \
                "_@assassinsgwbot номера X_ - создать чек Х номеров по скринам (при наличии боя)\n" + \
                "_@assassinsgwbot номера X Y Z ..._ - создать чек перечисленных номеров по игре (при наличии боя)"
    else:
        text += "\n*В военном чате:*\n" + \
                "_@assassinsgwbot !!! <текст>_ - отправить срочное сообщение"
    bot.send_message(userid, text, parse_mode="markdown")
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
    bot.delete_message(m.chat.id, m.message_id)

@bot.message_handler(commands=['бой'])
def command_start(m):
    print("command_start")
    print(m)
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    inline_error = m.text.replace("/бой ", "")
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


@bot.message_handler(commands=['старт'])
def command_battle_start(m):
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    if not CanStartNewBattle():
        text = "Запустить текущий бой [%0.2d:%0.2d]?" \
                % (current_battle.time["start"].hour, current_battle.time["start"].minute)
        bot.send_message(m.chat.id, text, reply_markup=kb.KEYBOARD_START)
    else:
        hlp.SendHelpNoBattle(m.chat.id, bot)

@bot.message_handler(commands=['стоп'])
def command_battle_stop(m):
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    if not CanStartNewBattle():
        text = "Завершить текущий бой [%0.2d:%0.2d]?" \
                % (current_battle.time["start"].hour, current_battle.time["start"].minute)
        bot.send_message(m.chat.id, text, reply_markup=kb.KEYBOARD_STOP)
    else:
        hlp.SendHelpNoBattle(m.chat.id, bot)

#
# Update bot admins list (from war chat where admins reside)
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
# Manage admins in private bot chat
#
@bot.message_handler(commands=["admin"])
def manage_admins(m):
    # print("manage_admins")
    # print(m)
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to manage admins" % (*user,))
    userid = m.from_user.id
    nick   = user[1] if user[1] != None else ""
    name_record = user[2] + " " + nick
    is_chat_admin = False
    if not IsInPrivateChat(m):
        for admin in bot.get_chat_administrators(m.chat.id):
            if admin.user.id == user[0]:
                is_chat_admin = True
                break
        if not is_chat_admin:
            log.error("Failed (not a chat admin)")
            SendHelpNonAdmin(m)
            return
    if not IsUserAdmin(m):
        log.error("Failed (not an admin)")
        SendHelpNonAdmin(m)
        return
    command = m.text.replace("/admin ", "") if m.text != "/admin" else ""
    if command == "list": # list admins
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
    else:
        log.error("Failed (invalid command): %s" % command)
        bot.send_message(user[0], "Неизвестная команда. Для справки используйте /help.")

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
    if m.text == buttonStart.text:
        current_battle.DoStartBattle()
        bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_LATE)
        bot.send_message(m.chat.id, "✅ Бой успешно запущен", reply_markup=markup)
        current_battle.BattleStartNotifyActiveUsers(bot)
    elif m.text == buttonStop.text:
        current_battle.DoEndBattle()
        bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                              parse_mode="markdown")
        bot.send_message(m.chat.id, "❎ Бой успешно завершен", reply_markup=markup)
    else: # Отмена
        bot.send_message(m.chat.id, "⛔️ Действие отменено", reply_markup=markup)

# @bot.message_handler(func=lambda message: not IsUserAdmin(message))
# def nonadmin_message(m):
#     user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
#     log.debug("User %d (%s %s) tried to send common message to war chat (%s)" % (*user, m.text))
#     message_id = m.message_id
#     chat_id = m.chat.id
#     bot.delete_message(chat_id, message_id)
#     SendHelpNonAdmin(m)

@bot.message_handler(func=lambda message: True)
def check_doubleshop(m):
    # print("check_doubleshop")
    # print(m)
    if not IsInPrivateChat(m):
        global DOUBLESHOP_TIME_CALLED
        now = datetime.datetime.now()
        time_to_check = [now.weekday(), now.hour, now.minute]
        if now.weekday() == DOUBLESHOP_TIME[0]:
            if now.hour >= DOUBLESHOP_TIME[1][0] and now.hour <= DOUBLESHOP_TIME[2][0]:
                if now.minute >= DOUBLESHOP_TIME[1][1] and now.minute <= DOUBLESHOP_TIME[2][1]:
                    if not DOUBLESHOP_TIME_CALLED:
                        bot.send_message(m.chat.id, "💰 *Двойная закупка в лавке гильдии!*", parse_mode="markdown")
                        DOUBLESHOP_TIME_CALLED = True
        else:
            DOUBLESHOP_TIME_CALLED = False
    elif not IsUserAdmin(m):
        SendHelpNonAdmin(m)

if "HEROKU" in list(os.environ.keys()):
    log.warning("Running on Heroku, setup webhook")
    server = Flask(__name__)

    @server.route('/bot' + TOKEN, methods=['POST'])
    def getMessage():
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200

    @server.route("/")
    def webhook():
        bot.remove_webhook()
        bot.set_webhook(url='https://' + BOT_USERNAME + '.herokuapp.com/bot' + TOKEN)
        return "?", 200
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 80)))
else:
    log.warning("Running locally, start polling")
    bot.remove_webhook()
    bot.polling(none_stop=True, interval=0, timeout=20)
