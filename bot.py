#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# @assassinsgwbot
#

import telebot, datetime, re
from battle import *
from warprecheck import *
from telebot import types
from keyboards import *

DOUBLESHOP_TIME = [4, [17, 58], [18, 13]]
DOUBLESHOP_TIME_CALLED = False

with open("TOKEN", "r") as tfile:
    TOKEN = tfile.readline().strip('\n')
    print("read token: '%s'" % TOKEN)
    tfile.close()

bot = telebot.TeleBot(TOKEN)

ROOT_ADMIN = 187678932 # creator
admins = { 187678932: "alex1489" }

current_battle = None
current_precheck = None
time_pattern = r'(?:\d|[01]\d|2[0-3])\D[0-5]\d'

#####################
# Support functions #
#####################
def IsUserAdmin(message):
    global admins
    if message.from_user.id in admins:
        return True
    else:
        return False

def IsInPrivateChat(message):
    if message.chat.id == message.from_user.id:
        return True
    return False

def CanStartNewPrecheck():
    global current_precheck
    res = current_precheck == None
    if not res:
        res = current_precheck.is_postponed
    return res

def CanStartNewBattle():
    global current_battle
    res = current_battle == None
    if not res:
        res = current_battle.is_postponed
    return res

def IsCheckTime(query): # return if query contains check time and check time list
    times = re.findall(time_pattern, query.query)
    if times != [] and len(times) == 2:
        return True, times
    return False, None

def SendHelpNonAdmin(message):
    text =  "Мной могут управлять только офицеры гильдии.\n"
    text += "Обратитесь к одному из офицеров за подробностями:\n\n"
    for admin in admins:
        text += "[%s](tg://user?id=%d)\n" % (admins[admin], admin)
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
# GW Pre-check
#
@bot.callback_query_handler(func=lambda call: call.data in PRECHECK_OPTIONS)
def precheck_check_user(call):
    global current_precheck
    # print("precheck_check_user")
    # print(call)
    message_id = call.inline_message_id
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    userChoice = call.data
    if message_id == current_precheck.check_id:
        ret = current_precheck.CheckUser(user, userChoice)
        if (ret):
            bot.edit_message_text(current_precheck.GetText(), inline_message_id=message_id, 
                                parse_mode="markdown", reply_markup=KEYBOARD_PRECHECK)
            bot.answer_callback_query(call.id, current_precheck.GetVotedText(user, userChoice))
        else:
            bot.answer_callback_query(call.id, "Вы уже проголосовали (%s)" % userChoice)
        return
    print("ERROR: pre-check not found!")

@bot.callback_query_handler(func=lambda call: call.data in PRECHECK_CONTROL_OPTIONS)
def precheck_control(call):
    global current_precheck
    # print("precheck_control")
    # print(call)
    if not IsUserAdmin(call):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять чеком!")
        return
    userChoice = call.data
    if userChoice == PRECHECK_CONTROL_OPTIONS[0]: # stop
        current_precheck.DoEndPrecheck()
        bot.edit_message_text(current_precheck.GetText(), inline_message_id=current_precheck.check_id, 
                              parse_mode="markdown")
        bot.answer_callback_query(call.id, "🏁 Чек завершен")
        return
    print("ERROR: pre-check not found!")

@bot.chosen_inline_handler(lambda result: result.result_id == '1')
def precheck_init_vote(r):
    global current_precheck
    # print("battle_init_vote")
    # print(r)
    current_precheck = WarPreCheck()
    current_precheck.SetMessageID(r.inline_message_id)

@bot.inline_handler(lambda query: query.query == "precheck")
def precheck_query_inline(q):
    global current_precheck
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
                                            reply_markup=KEYBOARD_PRECHECK)
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=30)
    else:
        print("ERROR: trying to set another pre-check while current is not finished")
        error_text = "Уже имеется активный чек"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=30,
                                switch_pm_text=error_text, switch_pm_parameter="existing_precheck")

#
# Battle check
#
@bot.callback_query_handler(func=lambda call: call.data in CHECK_OPTIONS)
def battle_check_user(call):
    global current_battle
    # print("battle_check_user")
    # print(call)
    message_id = call.inline_message_id
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    userChoice = call.data
    if message_id == current_battle.check_id:
        ret = current_battle.CheckUser(user, userChoice)
        if (ret):
            markup = KEYBOARD_CHECK
            if current_battle.is_started:
                markup = KEYBOARD_LATE
            bot.edit_message_text(current_battle.GetText(), inline_message_id=message_id, 
                                parse_mode="markdown", reply_markup=markup)
            bot.answer_callback_query(call.id, current_battle.GetVotedText(userChoice))
        else:
            bot.answer_callback_query(call.id, "Вы уже проголосовали (%s)" % userChoice)
        return
    print("ERROR: battle not found!")

@bot.callback_query_handler(func=lambda call: call.data in CHECK_CONTROL_OPTIONS)
def battle_control(call):
    global current_battle
    # print("battle_control")
    # print(call)
    if not IsUserAdmin(call):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять боем!")
        return
    userChoice = call.data
    if userChoice == CONTROL_OPTIONS[0]: # start
        current_battle.DoStartBattle()
        bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                              parse_mode="markdown", reply_markup=KEYBOARD_LATE)
        bot.answer_callback_query(call.id, "⚔️ Бой запущен")
        return
    elif userChoice == CONTROL_OPTIONS[1]: # stop
        current_battle.DoEndBattle()
        bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                              parse_mode="markdown")
        bot.answer_callback_query(call.id, "🏁 Бой завершен")
        return
    print("ERROR: battle not found!")

@bot.chosen_inline_handler(lambda result: result.result_id == '0')
def battle_init_vote(r):
    global current_battle
    # print("battle_init_vote")
    # print(r)
    times = re.findall(time_pattern, r.query)
    current_battle = Battle(times[0], times[1])
    current_battle.SetMessageID(r.inline_message_id)

@bot.inline_handler(lambda query: IsCheckTime(query)[0])
def battle_query_inline(q):
    global current_battle
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
                                            reply_markup=KEYBOARD_CHECK)
        bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=30)
    else:
        print("ERROR: trying to set another battle while current is not finished")
        error_text = "Уже имеется активный бой в %0.2d:%0.2d" \
                     % (current_battle.time["start"].hour, current_battle.time["start"].minute)
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=30,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")

#
# Urgent message from non-admin user
#
@bot.chosen_inline_handler(lambda result: result.result_id == '2')
def urgent_remind_user(r):
    # print("urgent_remind_user")
    # print(r)
    bot.send_message(r.from_user.id, "Пожалуйста, не забывайте, что " + 
                     "отправлять в военный чат следует только особо важные сведения!")

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

###################
# Command handlers #
###################
@bot.message_handler(commands=["help"])
def show_help(m):
    userid = m.from_user.id
    text =  "⚔️ Привет! Я военный бот гильдии *Assassins*\n"
    text += "🎮 Игра: *Dungeon Hunter V*"
    text += "\n\n📃 *Список моих команд*:\n"
    text += "/help - вывод этой справки\n"
    if IsUserAdmin(m):
        text += "/start - вывод информации о текущем бое (если есть).\n"
        text += "/admin list - вывод текущего списка офицеров\n"
        if userid == ROOT_ADMIN:
            text += "/admin delete <ID> - удаление офицера по ID\n"
        text += "\n*При наличии текущего боя:*\n"
        text += "/bstart - начать бой\n"
        text += "/bstop  - завершить/отменить бой\n"
        text += "\n*В военном чате:*\n" + \
                "_@assassinsgwbot precheck_ - создать чек перед ВГ\n" + \
                "_@assassinsgwbot XX:XX YY:YY_ - создать чек на бой"
    if not IsUserAdmin(m):
        text += "\n*В военном чате:*\n" + \
                "_@assassinsgwbot !!! <текст>_ - отправить срочное сообщение"
    bot.send_message(userid, text, parse_mode="markdown")
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)

@bot.message_handler(commands=['start'])
def command_start(m):
    global current_battle
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
    global current_battle
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    if not CanStartNewBattle():
        text = "Запустить текущий бой [%0.2d:%0.2d]?" \
                % (current_battle.time["start"].hour, current_battle.time["start"].minute)
        bot.send_message(m.chat.id, text, reply_markup=KEYBOARD_START)
    else:
        SendHelpNoBattle(m.chat.id)

@bot.message_handler(commands=['bstop'])
def command_battle_stop(m):
    global current_battle
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    if not CanStartNewBattle():
        text = "Завершить текущий бой [%0.2d:%0.2d]?" \
                % (current_battle.time["start"].hour, current_battle.time["start"].minute)
        bot.send_message(m.chat.id, text, reply_markup=KEYBOARD_STOP)
    else:
        SendHelpNoBattle(m.chat.id)

@bot.message_handler(commands=["admin"])
def manage_admins(m):
    global admins
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    userid = m.from_user.id
    nick   = m.from_user.username
    command = m.text.replace("/admin ", "") if m.text != "/admin" else ""
    if command == "": # save admin
        # cannot use command in private chat
        if IsInPrivateChat(m):
            bot.send_message(userid, "Используйте команду /admin в военном чате, чтобы внести себя в список офицеров!")
            return
        for admin in bot.get_chat_administrators(m.chat.id):
            if admin.user.id == userid:
                if not userid in admins:
                    admins[userid] = nick
                    bot.send_message(userid, "Вы успешно добавлены в список офицеров!")
                else:
                    bot.send_message(userid, "Вы уже есть в списке офицеров!")
                return
        bot.send_message(userid, "Извините, вы не являетесь офицером чата '%s'" % m.chat.title)
    elif command == "list": # list admins
        text =  "Текущий список офицеров:\n\n"
        for admin in admins:
            if admin != ROOT_ADMIN:
                if userid == ROOT_ADMIN: # show admins IDs for root admin
                    text += "👤 %s _(ID=%d)_\n" % (admins[admin], admin)
                else:
                    text += "👤 %s\n" % admins[admin]
            else:
                text += "👁 %s _(администратор бота)_\n" % admins[admin]
        if userid == ROOT_ADMIN:
            text += "\nСписок действий:\n"
            text += "/admin delete _ID_ - удалить офицера"
        bot.send_message(userid, text, parse_mode="markdown")
        return
    elif command[:6] == "delete":
        if userid == ROOT_ADMIN: # deleting admins is for root admin only
            try:
                admin_id = int(command.replace("delete ", ""))
                if admin_id == ROOT_ADMIN:
                    bot.send_message(userid, "Не могу удалить *%s* - это администратор бота." % admins[admin_id], parse_mode="markdown")
                    return
                if admin_id in admins:
                    admin_nick = admins[admin_id]
                    del admins[admin_id]
                    bot.send_message(userid, "Офицер *%s* успешно удален." % admin_nick, parse_mode="markdown")
                else:
                    bot.send_message(userid, "Офицер c ID %d не найден." % admin_id)
            except ValueError:
                bot.send_message(userid, "Неверный фомат ID офицера.")
    else:
        bot.send_message(userid, "Неизвестная команда. Для справки используйте /help.")

@bot.message_handler(func=lambda message: message.text in CHECK_CONTROL_OPTIONS_PRIVATE)
def battle_control(m):
    global current_battle
    if not IsInPrivateChat(m): return
    if not IsUserAdmin(m):
        SendHelpNonAdmin(m)
        return
    markup = types.ReplyKeyboardRemove(selective=False)
    if m.text == buttonStart.text:
        current_battle.DoStartBattle()
        bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                              parse_mode="markdown", reply_markup=KEYBOARD_LATE)
        bot.send_message(m.chat.id, "✅ Бой успешно запущен", reply_markup=markup)
    elif m.text == buttonStop.text:
        current_battle.DoEndBattle()
        bot.edit_message_text(current_battle.GetText(), inline_message_id=current_battle.check_id, 
                              parse_mode="markdown")
        bot.send_message(m.chat.id, "❎ Бой успешно завершен", reply_markup=markup)
    else: # Отмена
        bot.send_message(m.chat.id, "⛔️ Действие отменено", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def check_doubleshop(m):
    if not IsInPrivateChat(m):
        global DOUBLESHOP_TIME_CALLED
        # print(m)
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
