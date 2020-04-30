#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# @assassinsgwbot
# Main bot module
#

import telebot, os, time
from telebot import types
from logger import get_logger
from flask import Flask, request

import common
from common import bot
from icons import *
from battle import *
from warprecheck import *
from arsenal import *
from numberscheck import *
from screens import *
from commands import COMMANDS
import keyboards as kb
import callbacks as cb
import helpers as hlp

log = get_logger("bot")

DOUBLESHOP_TIME = [4, [17, 58], [18, 13]]
DOUBLESHOP_TIME_CALLED = False

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
    if r.result_id == 'battle':
        log.debug("User %d (%s %s) created battle check (%s)" % (*user, r.query))
        times = hlp.IsCheckTimeQuery(r)[1]
        common.current_battle = Battle(times[0], times[1])
        common.current_battle.SetMessageID(r.inline_message_id)
        bot.edit_message_text(common.current_battle.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_CHECK)
    elif r.result_id == 'precheck':
        log.debug("User %d (%s %s) created pre-check" % (*user,))
        common.current_precheck = WarPreCheck()
        common.current_precheck.SetMessageID(r.inline_message_id)
        bot.edit_message_text(common.current_precheck.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_PRECHECK)
    elif r.result_id == 'arsenal':
        log.debug("User %d (%s %s) created arsenal check" % (*user,))
        common.current_arscheck = Arsenal()
        common.current_arscheck.SetMessageID(r.inline_message_id)
        common.current_arscheck.SetRage(common.rage_time_workaround)
        bot.edit_message_text(common.current_arscheck.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_ARS)
    elif r.result_id == 'numbers':
        res, numbers = hlp.IsNumbersQuery(r)
        if len(numbers) == 1:
            log.debug("User %d (%s %s) created screens numbers check (%s)" % (*user, numbers[0]))
            common.current_numcheck = NumbersCheck(int(numbers[0]))
            common.current_numcheck.SetMessageID(r.inline_message_id)
        else:
            log.debug("User %d (%s %s) created in-game numbers check (%s)" % (*user, ' '.join(str(num) for num in numbers)))
            common.current_numcheck = NumbersCheck(len(numbers), ingame=True, ingame_nums=numbers)
            common.current_numcheck.SetMessageID(r.inline_message_id)
        bot.edit_message_text(common.current_numcheck.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_NUMBERS)
    else:
        log.error("Invalid chosen inline result incoming!")

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
    if hlp.IsUserAdmin(m):
        if str(userid) == common.ROOT_ADMIN[0]:
            text += "/setadmins обновить список офицеров (в военном чате)\n"
        text += "/reset - аварийный сброс бота\n"
        text += "Также я умею `составлять список противников по скриншотам` из поиска гильдий, " + \
                "если послать их мне в личные сообщения в виде альбома.\n"

        text += "\n*При наличии текущего боя:*\n"
        text += "/bstart - начать бой\n"
        text += "/bstop  - завершить/отменить бой\n"
        text += "/checklist  - получить список всех участвующих в текущем бою\n"
        text += "\n*В военном чате:*\n" + \
                "/warchat - запомнить военный чат _(для отправки сообщений боя)_\n" + \
                "/snow - вызвать Снегурочку! _(только в Вс после окончания ВГ)_\n" + \
                "_@assassinsgwbot чек_ - создать чек перед ВГ\n" + \
                "_@assassinsgwbot XX:XX YY:YY_ - создать чек на бой\n" + \
                "_@assassinsgwbot арс XX:XX_ - создать чек арсенала (при наличии боя)\n" + \
                "_@assassinsgwbot номера X_ - создать чек Х номеров по скринам (при наличии боя)\n" + \
                "_@assassinsgwbot номера X Y Z ..._ - создать чек перечисленных номеров по игре (при наличии боя)\n" + \
                "Разделительные символы времени могут быть любыми (даже пробелом)"
    else:
        pass # stub for adding only non-admin help
    bot.send_message(userid, text, parse_mode="markdown")
    if not hlp.IsUserAdmin(m):
        hlp.SendHelpNonAdmin(m)
    bot.delete_message(m.chat.id, m.message_id)

#
# Start pending battle
# (private bot chat)
#
@bot.message_handler(commands=['warchat'])
def command_set_warchat(m):
    if hlp.IsInPrivateChat(m):
        hlp.SendHelpWrongChat(m.from_user.id, "/warchat", "запомнить военный чат", False)
        return
    bot.delete_message(m.chat.id, m.message_id)
    if not hlp.IsUserAdmin(m):
        hlp.SendHelpNonAdmin(m)
        return
    
    if common.warchat_id != None and common.warchat_id == m.chat.id:
        bot.send_message(m.from_user.id, ICON_CANCEL+" Военный чат уже задан!")
    else:
        common.warchat_id = m.chat.id
        log.info("war chat set: ", common.warchat_id)
        bot.send_message(m.from_user.id, ICON_CHECK+" Военный чат успешно задан!")


#
# Start utility command
# (private bot chat)
#
@bot.message_handler(commands=['start'])
def command_start(m):
    # print("command_start")
    # print(m)
    if not hlp.IsInPrivateChat(m):
        bot.delete_message(m.chat.id, m.message_id)
        hlp.SendHelpWrongChat(m.from_user.id, "/start", "просмотреть информацию о бое", True)
        return
    if not hlp.IsUserAdmin(m):
        hlp.SendHelpNonAdmin(m)
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
            if not hlp.CanStartNewBattle():
                text =  "Текущий бой: %0.2d:%0.2d / %0.2d:%0.2d.\n\n" \
                        % (common.current_battle.time["check"].hour, common.current_battle.time["check"].minute,
                           common.current_battle.time["start"].hour, common.current_battle.time["start"].minute)
                text += ("Чтобы начать новый бой, необходимо завершить (%s) предыдущий.\n" % ICON_STOP) + \
                         "Если бой был назначен ошибочно - остановите бой, " + \
                         "затем создайте новый, а старое сообщение удалите."
                bot.send_message(m.chat.id, text)
            else:
                hlp.SendHelpNoBattle(m.chat.id)
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
    if not hlp.IsInPrivateChat(m):
        bot.delete_message(m.chat.id, m.message_id)
        hlp.SendHelpWrongChat(m.from_user.id, "/bstart", "начать бой", True)
        return
    if not hlp.IsUserAdmin(m):
        hlp.SendHelpNonAdmin(m)
        return
    if not hlp.CanStartNewBattle():
        if not common.current_battle.is_started:
            text = "Запустить текущий бой [%0.2d:%0.2d]?" \
                    % (common.current_battle.time["start"].hour, common.current_battle.time["start"].minute)
            bot.send_message(m.chat.id, text, reply_markup=kb.KEYBOARD_START)
        else:
            bot.send_message(m.chat.id, "Бой уже запущен")
    else:
        hlp.SendHelpNoBattle(m.chat.id)

#
# Stop current battle
# (private bot chat)
#
@bot.message_handler(commands=['bstop'])
def command_battle_stop(m):
    if not hlp.IsInPrivateChat(m):
        bot.delete_message(m.chat.id, m.message_id)
        hlp.SendHelpWrongChat(m.from_user.id, "/bstop", "завершить или отменить бой", True)
        return
    if not hlp.IsUserAdmin(m):
        hlp.SendHelpNonAdmin(m)
        return
    if not hlp.CanStartNewBattle():
        if not common.current_battle.is_postponed:
            text = "Завершить текущий бой [%0.2d:%0.2d]?" \
                    % (common.current_battle.time["start"].hour, common.current_battle.time["start"].minute)
            bot.send_message(m.chat.id, text, reply_markup=kb.KEYBOARD_STOP)
        else:
            bot.send_message(m.chat.id, "Бой уже завершен")
    else:
        hlp.SendHelpNoBattle(m.chat.id)

#
# Get check list for current battle
# (private bot chat)
#
@bot.message_handler(commands=['checklist'])
def command_battle_checklist(m):
    if not hlp.IsInPrivateChat(m):
        bot.delete_message(m.chat.id, m.message_id)
        hlp.SendHelpWrongChat(m.from_user.id, "/checklist", "получить список участвующих в бою", True)
        return
    if not hlp.IsUserAdmin(m):
        hlp.SendHelpNonAdmin(m)
        return
    if not hlp.CanStartNewBattle():
        checklist = ""
        for user in common.current_battle.GetActiveUsersNames():
            checklist += user + "\n"
        bot.send_message(m.chat.id, checklist)
    else:
        hlp.SendHelpNoBattle(m.chat.id)

#
# Update bot admins list
# (war chat where admins reside)
#
@bot.message_handler(commands=["setadmins"])
def setup_admins(m):
    
    # print("setup_admins")
    # print(m)
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to update admins list" % (*user,))
    if not hlp.IsUserAdmin(m):
        log.error("Failed (not an admin)")
        hlp.SendHelpNonAdmin(m)
        return
    if hlp.IsInPrivateChat(m):
        log.error("Failed (in private chat)")
        hlp.SendHelpWrongChat(user[0], "/setadmins", "обновить список офицеров", False)
        return
    is_chat_admin = False
    chat_admins = bot.get_chat_administrators(m.chat.id).wait()
    for admin in chat_admins:
        if admin.user.id == user[0]:
            is_chat_admin = True
            break
    if not is_chat_admin:
        log.error("Failed (not a chat admin)")
        hlp.SendHelpNonAdmin(m)
        return
    admins = {}
    for admin in chat_admins:
        if str(admin.user.id) != common.ROOT_ADMIN[0] and admin.user.username != common.BOT_USERNAME:
            name_record = admin.user.first_name
            if admin.user.username != None:
                name_record += " (" + admin.user.username + ")"
            admins[str(admin.user.id)] = name_record
    common.SaveAdminsList(admins)
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
    if not hlp.IsInPrivateChat(m):
        bot.delete_message(m.chat.id, m.message_id)
        hlp.SendHelpWrongChat(user[0], "/admins", "посмотреть список офицеров", True)
        return
    text =  "Список офицеров:\n\n"
    text += "👁 %s _[администратор бота]_\n" % common.ROOT_ADMIN[1]
    for admin in common.admins:
        if common.BOT_USERNAME not in admin or admin != common.ROOT_ADMIN[1]:
            if str(user[0]) == ROOT_ADMIN[0]: # show admins IDs for root admin
                text += ICON_MEMBER+" %s _(ID=%s)_\n" % (common.admins[admin], admin)
            else:
                text += (ICON_MEMBER+" %s\n" % common.admins[admin])
    bot.send_message(user[0], text, parse_mode="markdown")
    return

#
# Emergency reset all checks
# (private bot chat)
#
@bot.message_handler(commands=['reset'])
def command_reset(m):
    if not hlp.IsInPrivateChat(m):
        bot.delete_message(m.chat.id, m.message_id)
        hlp.SendHelpWrongChat(m.from_user.id, "/reset", "выполнить полный сброс бота", True)
        return
    if not hlp.IsUserAdmin(m):
        hlp.SendHelpNonAdmin(m)
        return
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to reset bot" % (*user,))
    bot.send_message(m.chat.id, "Выполнить полный сброс?", reply_markup=kb.KEYBOARD_RESET)

#
# Battle control
# (private bot chat)
#
@bot.message_handler(func=lambda message: message.text in kb.CHECK_CONTROL_OPTIONS_PRIVATE)
def battle_control(m):
    # it is a bug actually to use privately generated keyboard buttons outside private bot chat
    # should not happen in any case, but who knows?
    if not hlp.IsInPrivateChat(m):
        return
    if not hlp.IsUserAdmin(m):
        hlp.SendHelpNonAdmin(m)
        return
    markup = types.ReplyKeyboardRemove(selective=False)
    if m.text == kb.buttonStartPrivate.text:
        common.current_battle.DoStartBattle()
        bot.edit_message_text(common.current_battle.GetText(), inline_message_id=common.current_battle.check_id, 
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_LATE)
        bot.send_message(m.chat.id, "✅ Бой успешно запущен", reply_markup=markup)
        common.current_battle.BattleStartNotifyActiveUsers()
    elif m.text == kb.buttonStopPrivate.text:
        reset_control(m)
        bot.send_message(m.chat.id, "❎ Бой успешно завершен", reply_markup=markup)
    else: # Отмена
        bot.send_message(m.chat.id, "⛔️ Действие отменено", reply_markup=markup)

#
# Call for fun mode 'Snow White'
# (war chat command)
#
@bot.message_handler(commands=['snow'])
def command_snow(m):
    # print(m)
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to call Snow!" % (*user,))
    if hlp.IsInPrivateChat(m):
        hlp.SendHelpWrongChat(m.from_user.id, "/snow", "вызвать Снегурочку", False)
        return
    bot.delete_message(m.chat.id, m.message_id)
    if not hlp.IsUserAdmin(m):
        log.error("Failed: not an admin")
        hlp.SendHelpNonAdmin(m)
        return
    if not hlp.IsSnowAvailable():
        bot.send_message(user[0], "Ой! Вызвать Снегурочку можно только в воскресенье после окончания ВГ!")
        log.error("Failed: wrong time")
        return
    
    if common.current_snowwhite == {}:
        common.current_snowwhite["message"] = bot.send_message(m.chat.id,
                                             ICON_SNOW+" Всем привет!",
                                             reply_markup=kb.KEYBOARD_SNOWWHITE).wait()
        common.current_snowwhite["praised"] = []
        log.info("Snow White called!")
    else:
        log.error("Snow White is already here!")

#
# Snow White control
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data == cb.SNOW_PRAISE_CALLBACK)
def snow_control(call):
    # print("snow_control")
    # print(call)
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    log.debug("User %d (%s %s) is cheering Snow White" % (*user,))
    
    if common.current_snowwhite != {}:
        if not user[0] in common.current_snowwhite["praised"]:
            log.debug("Praised")
            bot.send_message(call.message.chat.id, hlp.SnowGeneratePraise(user),
                             parse_mode="markdown", disable_notification=True)
            common.current_snowwhite["praised"].append(user[0])
            bot.answer_callback_query(call.id)
        else:
            log.error("Failed: already praised")
            bot.answer_callback_query(call.id, "Поприветствовать Снегурочку можно только один раз!")
        if not hlp.IsSnowAvailable():
            log.info("Snow White overtime, ending")
            bot.delete_message(common.current_snowwhite["message"].chat.id, common.current_snowwhite["message"].message_id)
            bot.send_message(call.message.chat.id,
                             ICON_SNOW+" До встречи в следюущее воскресенье!",
                             disable_notification=True)
            common.current_snowwhite = {}
        return
    log.error("Bug! User pressed Snow White keyboard button with to current_snowwhite!")
    bot.answer_callback_query(call.id)

if "HEROKU" in list(os.environ.keys()):
    log.warning("Running on Heroku, setup webhook")
    server = Flask(__name__)

    @server.route('/bot' + common.TOKEN, methods=['POST'])
    def getMessage():
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200

    @server.route("/")
    def webhook():
        time.sleep(1)
        bot.set_webhook(url='https://' + common.BOT_USERNAME + '.herokuapp.com/bot' + common.TOKEN)
        return "?", 200
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 80)))
else:
    log.warning("Running locally, start polling")
    bot.remove_webhook()
    bot.polling(none_stop=True, interval=0, timeout=20)
