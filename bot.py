#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# @assassinsgwbot
#

import telebot, datetime, re, json, sys
from battle import *
from warprecheck import *
from arsenal import *
from numberscheck import *
from telebot import types
import keyboards as kb

DOUBLESHOP_TIME = [4, [17, 58], [18, 13]]
DOUBLESHOP_TIME_CALLED = False

# setup proxy if asked
if len(sys.argv) > 1:
    if sys.argv[1] == '1':
        telebot.apihelper.proxy = {'http':'http://73.55.76.54:8080'}

with open("TOKEN", "r") as tfile:
    TOKEN = tfile.readline().strip('\n')
    print("read token: '%s'" % TOKEN)
    tfile.close()

bot = telebot.TeleBot(TOKEN)

BOT_USERNAME = "assassinsgwbot"
ROOT_ADMIN = [] # creator
admins = {}

current_battle   = None
current_precheck = None
current_arscheck = None
current_numcheck = None
time_pattern = r'(?:\d|[01]\d|2[0-3])\D[0-5]\d'
count_pattern = r'[1-9]\d*'

#
# Manage admins list through file
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
# Support functions #
#####################
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

def IsCheckTime(query): # return if query contains check time and check time list
    times = re.findall(time_pattern, query.query)
    if times != [] and len(times) == 2:
        return True, times
    return False, None

def IsNumber(query): # return if query contains numbers count
    count = re.findall(count_pattern, query.query)
    if count != [] and len(count) == 1:
        return True, int(count[0])
    return False, None

def SendHelpNonAdmin(message):
    text =  "Мной могут управлять только офицеры гильдии.\n"
    text += "Обратитесь к одному из офицеров за подробностями:\n\n"
    for admin in admins:
        text += "[%s](tg://user?id=%s)\n" % (admins[admin], admin)
    bot.send_message(message.from_user.id, text, parse_mode="markdown")

def SendHelpNoBattle(chat_id):
    error_text =  "Текущий активный бой отсутствует.\n"
    error_text += "Начните новый бой, упомянув меня в военном чате и задав время чека/боя.\n"
    error_text += "*Пример*: @assassinsgwbot 13:40 14:00"
    bot.send_message(chat_id, error_text, parse_mode="markdown")

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
    if r.result_id == '0': # battle check
        global current_battle
        times = re.findall(time_pattern, r.query)
        current_battle = Battle(times[0], times[1])
        current_battle.SetMessageID(r.inline_message_id)
    elif r.result_id == '1': # pre-check
        global current_precheck
        current_precheck = WarPreCheck()
        current_precheck.SetMessageID(r.inline_message_id)
    elif r.result_id == '2': # send urgent message
        bot.send_message(r.from_user.id, "Пожалуйста, не забывайте, что " +
                         "отправлять в военный чат следует только особо важные сведения!")
    elif r.result_id == '3': # ars check
        global current_arscheck
        current_arscheck = Arsenal()
        current_arscheck.SetMessageID(r.inline_message_id)
    elif r.result_id == '4': # numbers check
        global current_numcheck
        count = IsNumber(r)
        if count[0]:
            current_numcheck = NumbersCheck(int(count[1]))
            current_numcheck.SetMessageID(r.inline_message_id)

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
    if message_id == current_precheck.check_id:
        ret = current_precheck.CheckUser(user, userChoice)
        if (ret):
            bot.edit_message_text(current_precheck.GetText(), inline_message_id=message_id, 
                                parse_mode="markdown", reply_markup=kb.KEYBOARD_PRECHECK)
            bot.answer_callback_query(call.id, current_precheck.GetVotedText(user, userChoice))
        else:
            bot.answer_callback_query(call.id, "Вы уже проголосовали (%s)" % userChoice)
        return
    print("ERROR: pre-check not found!")

@bot.callback_query_handler(func=lambda call: call.data in kb.PRECHECK_CONTROL_OPTIONS)
def precheck_control(call):
    # print("precheck_control")
    # print(call)
    if not IsUserAdmin(call):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять чеком!")
        return
    userChoice = call.data
    if userChoice == kb.PRECHECK_CONTROL_OPTIONS[0]: # stop
        current_precheck.DoEndPrecheck()
        bot.edit_message_text(current_precheck.GetText(), inline_message_id=current_precheck.check_id, 
                              parse_mode="markdown")
        bot.answer_callback_query(call.id, "🏁 Чек завершен")
        return
    print("ERROR: pre-check not found!")

@bot.inline_handler(lambda query: query.query == "precheck")
def precheck_query_inline(q):
    # print("query_inline_precheck")
    # print(q)
    if not IsUserAdmin(q): # non-admins cannot post votes
        SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    if CanStartNewBattle():
        res = types.InlineQueryResultArticle('1',
                                            'Создать чек перед ВГ ✅💤❌', 
                                            types.InputTextMessageContent(WarPreCheck().GetHeader(),
                                            parse_mode="markdown"),
                                            reply_markup=kb.KEYBOARD_PRECHECK)
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=30)
    else:
        print("ERROR: trying to set another pre-check while current is not finished")
        error_text = "Уже имеется активный чек"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=30,
                                switch_pm_text=error_text, switch_pm_parameter="existing_precheck")

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
            bot.answer_callback_query(call.id, "Вы уже проголосовали (%s)" % userChoice.replace(CHECK_CALLBACK_PREFIX, ""))
        return
    print("ERROR: battle not found!")

@bot.callback_query_handler(func=lambda call: call.data in kb.CHECK_CONTROL_OPTIONS)
def battle_control(call):
    # print("battle_control")
    # print(call)
    if not IsUserAdmin(call):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять боем!")
        return
    userChoice = call.data
    if userChoice == kb.CHECK_CONTROL_OPTIONS[0]: # start
        current_battle.DoStartBattle()
        bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_LATE)
        bot.answer_callback_query(call.id, "⚔️ Бой запущен")
        return
    elif userChoice == kb.CHECK_CONTROL_OPTIONS[1]: # stop
        current_battle.DoEndBattle()
        bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                              parse_mode="markdown")
        bot.answer_callback_query(call.id, "🏁 Бой завершен")
        return
    print("ERROR: battle not found!")

@bot.inline_handler(lambda query: IsCheckTime(query)[0])
def battle_query_inline(q):
    # print("query_inline_check")
    # print(q)
    if not IsUserAdmin(q): # non-admins cannot post votes
        SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    times = IsCheckTime(q)[1]
    if CanStartNewBattle():
        res = types.InlineQueryResultArticle('0',
                                            '[%s/%s] Создать чек на бой ✅💤❌' % (times[0], times[1]), 
                                            types.InputTextMessageContent(Battle(times[0], times[1]).GetHeader(),
                                            parse_mode="markdown"),
                                            reply_markup=kb.KEYBOARD_CHECK)
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=30)
    else:
        print("ERROR: trying to set another battle while current is not finished")
        error_text = "Уже имеется активный бой в %0.2d:%0.2d" \
                     % (current_battle.time["start"].hour, current_battle.time["start"].minute)
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=30,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")

#
# Arsenal progress for battle
#
@bot.callback_query_handler(func=lambda call: call.data in kb.ARS_OPTIONS)
def arsenal_check_user(call):
    # print("ars_check_user")
    # print(call)
    message_id = call.inline_message_id
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    userChoice = call.data
    if message_id == current_arscheck.check_id:
        ret = current_arscheck.Increment(user, userChoice)
        if (ret):
            bot.edit_message_text(current_arscheck.GetProgressText(), inline_message_id=message_id, 
                                parse_mode="markdown", reply_markup=kb.KEYBOARD_ARS)
            bot.answer_callback_query(call.id)
        else:
            bot.answer_callback_query(call.id)
        return
    print("ERROR: ars check not found!")

@bot.inline_handler(lambda query: query.query[:3] == "ars")
def arsenal_query_inline(q):
    # print("arsenal_query_inline")
    # print(q)
    if not IsUserAdmin(q): # non-admins cannot post votes
        SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    if CanStartNewBattle():
        print("ERROR: trying to set ars check with no current battle")
        error_text = "Отсутствует активный бой"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=30,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")
        return
    if CanStartNewArs():
        res = types.InlineQueryResultArticle('3',
                                             'Добавить прогресс арса 📦 |████--| Х/120',
                                             types.InputTextMessageContent(Arsenal().GetHeader(), parse_mode="markdown"),
                                             reply_markup=kb.KEYBOARD_ARS)
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=30)
    else:
        bot.send_message(q.from_user.id, "Прогресс арсенала уже создан!")

#
# Numbers progress for battle
#
@bot.callback_query_handler(func=lambda call: call.data in kb.NUMBERS_OPTIONS)
def numbers_check_user(call):
    # print("numbers_check_user")
    # print(call)
    message_id = call.inline_message_id
    if message_id == current_numcheck.check_id:
        if not current_numcheck.is_1000:
            ret = current_numcheck.CheckUser(call.from_user.id, call.data)
            if (ret):
                bot.edit_message_text(current_numcheck.GetText(), inline_message_id=message_id, 
                                    parse_mode="markdown", reply_markup=kb.KEYBOARD_NUMBERS)
        bot.answer_callback_query(call.id)
        return
    print("ERROR: numbers check not found!")

@bot.inline_handler(lambda query: query.query[:4] == "nums")
def numbers_query_inline(q):
    # print("numbers_query_inline")
    # print(q)
    if not IsUserAdmin(q): # non-admins cannot post votes
        SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    if CanStartNewBattle():
        print("ERROR: trying to set numbers check with no current battle")
        error_text = "Отсутствует активный бой"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=30,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")
        return
    count = IsNumber(q)
    if CanStartNewNumbers() and count[0]:
        kb.SetupNumbersKeyboard(int(count[1]))
        res = types.InlineQueryResultArticle('4',
                                             'Добавить прогресс номеров (%s)' % count[1],
                                             types.InputTextMessageContent(NumbersCheck(int(count[1])).GetText(), parse_mode="markdown"),
                                             reply_markup=kb.KEYBOARD_NUMBERS)
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=30)
    elif not CanStartNewNumbers():
        bot.send_message(q.from_user.id, "Прогресс номеров уже создан!")

#
# Urgent message from non-admin user
#
@bot.inline_handler(lambda query: query.query[:3] == "!!!")
def urgent_query_inline(q):
    # print("query_inline_urgent")
    # print(q)
    if IsUserAdmin(q): # non-admins cannot post votes
        bot.send_message(q.from_user.id, "Офицеры могут писать сообщения в чат напрямую.")
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
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=30)

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
        text += "/start - вывод информации о текущем бое (если есть).\n"
        text += "/admin list - вывод текущего списка офицеров\n"
        text += "\n*При наличии текущего боя:*\n"
        text += "/bstart - начать бой\n"
        text += "/bstop  - завершить/отменить бой\n"
        if str(userid) == ROOT_ADMIN[0]:
            text += "/setadmins обновить список офицеров (в военном чате)\n"
        text += "\n*В военном чате:*\n" + \
                "_@assassinsgwbot precheck_ - создать чек перед ВГ\n" + \
                "_@assassinsgwbot XX:XX YY:YY_ - создать чек на бой\n" + \
                "_@assassinsgwbot ars_ - создать чек арсенала (при наличии боя)\n" + \
                "_@assassinsgwbot nums X_ - создать чек Х номеров (при наличии боя)"
    else:
        text += "\n*В военном чате:*\n" + \
                "_@assassinsgwbot !!! <текст>_ - отправить срочное сообщение"
    bot.send_message(userid, text, parse_mode="markdown")
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)

@bot.message_handler(commands=['start'])
def command_start(m):
    # print("command_start")
    # print(m)
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    if not CanStartNewBattle():
        text =  "Текущий бой: %0.2d:%0.2d / %0.2d:%0.2d\n" \
            % (current_battle.time["check"].hour, current_battle.time["check"].minute, 
               current_battle.time["start"].hour, current_battle.time["start"].minute)
        text += "/bstart - начать бой\n"
        text += "/bstop  - остановить бой"
        bot.send_message(m.chat.id, text)
    else:
        SendHelpNoBattle(m.chat.id)

@bot.message_handler(commands=['bstart'])
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
        SendHelpNoBattle(m.chat.id)

@bot.message_handler(commands=['bstop'])
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
        SendHelpNoBattle(m.chat.id)

@bot.message_handler(commands=["setadmins"])
def setup_admins(m):
    global admins
    # print("setup_admins")
    # print(m)
    userid = m.from_user.id
    name   = m.from_user.first_name
    nick   = m.from_user.username
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    if IsInPrivateChat(m):
        bot.send_message(userid, "Используйте команду /setadmins в военном чате, чтобы обновить список офицеров!")
        return
    is_chat_admin = False
    chat_admins = bot.get_chat_administrators(m.chat.id)
    for admin in chat_admins:
        if admin.user.id == userid:
            is_chat_admin = True
            break
    if not is_chat_admin:
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


@bot.message_handler(commands=["admin"])
def manage_admins(m):
    # print("manage_admins")
    # print(m)
    userid = m.from_user.id
    name   = m.from_user.first_name
    nick   = m.from_user.username if m.from_user.username != None else ""
    name_record = name + " " + nick
    is_chat_admin = False
    if not IsInPrivateChat(m):
        for admin in bot.get_chat_administrators(m.chat.id):
            if admin.user.id == userid:
                is_chat_admin = True
                break
        if not is_chat_admin:
            SendHelpNonAdmin(m)
            return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    command = m.text.replace("/admin ", "") if m.text != "/admin" else ""
    if command == "list": # list admins
        text =  "Список офицеров:\n\n"
        text += "👁 %s _[администратор бота]_\n" % ROOT_ADMIN[1]
        for admin in admins:
            if BOT_USERNAME not in admin or admin != ROOT_ADMIN[1]:
                if str(userid) == ROOT_ADMIN[0]: # show admins IDs for root admin
                    text += ICON_MEMBER+" %s _(ID=%s)_\n" % (admins[admin], admin)
                else:
                    text += (ICON_MEMBER+" %s\n" % admins[admin])
        bot.send_message(userid, text, parse_mode="markdown")
        return
    else:
        bot.send_message(userid, "Неизвестная команда. Для справки используйте /help.")

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
    elif m.text == buttonStop.text:
        current_battle.DoEndBattle()
        bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                              parse_mode="markdown")
        bot.send_message(m.chat.id, "❎ Бой успешно завершен", reply_markup=markup)
    else: # Отмена
        bot.send_message(m.chat.id, "⛔️ Действие отменено", reply_markup=markup)

@bot.message_handler(func=lambda message: not IsUserAdmin(message))
def nonadmin_message(m):
    print(m)
    message_id = m.message_id
    chat_id = m.chat.id
    bot.delete_message(chat_id, message_id)
    SendHelpNonAdmin(m)

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

bot.polling(none_stop=True, interval=0, timeout=20)
