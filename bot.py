#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# @assassinsgwbot
#

import telebot, datetime, re
from battle import *
from telebot import types
from keyboards import *

DOUBLESHOP_TIME = [4, [17, 58], [18, 13]]
DOUBLESHOP_TIME_CALLED = False

with open("TOKEN", "r") as tfile:
    TOKEN = tfile.readline().strip('\n')
    print("read token: '%s'" % TOKEN)
    tfile.close()

bot = telebot.TeleBot(TOKEN)

admins = {}
current_battle = None

def CanStartNewBattle():
    global current_battle
    res = current_battle == None
    if not res:
        res = current_battle.is_postponed
    return res

def SendHelpNoBattle(chat_id):
    error_text =  "Текущий активный бой отсутствует.\n"
    error_text += "Начните новый бой, упомянув меня в военном чате и задав время чека/боя:\n"
    error_text += "Пример: @assassinsgwbot 13:40 14:00"
    bot.send_message(chat_id, error_text)

@bot.callback_query_handler(func=lambda call: True)
def battle_check_user(call):
    global current_battle
    print("check_user")
    print(call)
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
        return
    print("ERROR: battle not found!")

@bot.chosen_inline_handler(lambda chosen_inline_result: True)
def battle_init_vote(r):
    global current_battle
    print("test_chosen")
    print(r)
    if r.result_id == '0':
        times = re.findall(r'(?:\d|[01]\d|2[0-3]):[0-5]\d', r.query)
        current_battle = Battle(times[0], times[1])
        current_battle.SetMessageID(r.inline_message_id)


@bot.inline_handler(lambda query: True)
def query_inline_text(q):
    global current_battle
    print(q)
    print(current_battle)
    times = re.findall(r'(?:\d|[01]\d|2[0-3]):[0-5]\d', q.query)
    if times != [] and len(times) == 2:
        if CanStartNewBattle():
            new_battle = Battle(times[0], times[1]) # here we create new battle just to get complete message text below
            res = types.InlineQueryResultArticle('0',
                                                '[%s / %s] Создать голосование ✅💤❌' % (times[0], times[1]), 
                                                types.InputTextMessageContent(new_battle.GetText(),
                                                parse_mode="markdown"),
                                                reply_markup=KEYBOARD_CHECK)
            bot.answer_callback_query(q.id)
            bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=30)
        else:
            print("ERROR: trying to set another battle while current is not finished")
            error_text = "Уже имеется активный бой в %0.2d:%0.2d" \
                         % (current_battle.time["start"].hour, current_battle.time["start"].minute)
            bot.answer_inline_query(q.id, [], is_personal=True, cache_time=30,
                                    switch_pm_text=error_text, switch_pm_parameter="existing_battle")

@bot.message_handler(commands=['start'])
def command_start(m):
    global current_battle
    print("start_message")
    print(m)
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
    if not CanStartNewBattle():
        text = "Запустить текущий бой [%0.2d / %0.2d]?" \
                % (current_battle.time["start"].hour, current_battle.time["start"].minute)
        bot.send_message(m.chat.id, text, reply_markup=KEYBOARD_START)
    else:
        SendHelpNoBattle(m.chat.id)

@bot.message_handler(commands=['bstop'])
def command_battle_stop(m):
    global current_battle
    if not CanStartNewBattle():
        text = "Завершить текущий бой [%0.2d / %0.2d]?" \
                % (current_battle.time["start"].hour, current_battle.time["start"].minute)
        bot.send_message(m.chat.id, text, reply_markup=KEYBOARD_STOP)
    else:
        SendHelpNoBattle(m.chat.id)

@bot.message_handler(func=lambda message: message.text in [buttonStart.text, buttonStop.text, buttonCancel.text])
def battle_control(m):
    global current_battle
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
    global DOUBLESHOP_TIME_CALLED
    print(m)
    now = datetime.datetime.now()
    time_to_check = [now.weekday(), now.hour, now.minute]
    if now.weekday() == DOUBLESHOP_TIME[0]:
        if now.hour >= DOUBLESHOP_TIME[1][0] and now.hour <= DOUBLESHOP_TIME[2][0]:
            if now.minute >= DOUBLESHOP_TIME[1][1] and now.minute <= DOUBLESHOP_TIME[2][1]:
                if not DOUBLESHOP_TIME_CALLED:
                    bot.send_message(m.chat.id, "*Двойная закупка в лавке гильдии!*", parse_mode="markdown")
                    DOUBLESHOP_TIME_CALLED = True
    else:
        DOUBLESHOP_TIME_CALLED = False

bot.polling(none_stop=False, interval=0, timeout=20)
