#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# @assassinsgwbot
# Main bot module
#

import telebot, os, time, datetime
from telebot import types
from logger import get_logger
from flask import Flask, request

import common
from common import bot
from icons import *
from checks.battle import *
from checks.warprecheck import *
from checks.crystals import *
from checks.arsenal import *
from checks.numberscheck import *
from checks.screens import *
from settings.settings import *
from statistics import *
from guide import *
from commands import COMMANDS
import keyboards as kb
import callbacks as cb
import helpers as hlp

log = get_logger("bot.root")

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
    user = User(r.from_user.id, r.from_user.first_name, r.from_user.username)
    if r.result_id == 'battle':
        log.debug("%s created battle check (%s)" % (user, r.query))
        _, time, comment = hlp.IsCheckTimeQuery(r)
        hlp.LogEvent(ICON_SWORDS + " %s назначил бой на %s" % (user.GetString(with_link=False), time))
        common.current_battle = Battle(time, comment)
        common.current_battle.SetMessageID(r.inline_message_id)
        bot.edit_message_text(common.current_battle.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=common.current_battle.keyboard)
    elif r.result_id == 'precheck':
        log.debug("%s created pre-check" % user)
        common.current_precheck = WarPreCheck()
        common.current_precheck.SetMessageID(r.inline_message_id)
        bot.edit_message_text(common.current_precheck.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_PRECHECK)
    elif r.result_id == 'cryscheck':
        ranges = common.settings.GetSetting("crystals_ranges")
        log.debug("%s created crystals check" % user)
        common.current_cryscheck = Crystals(ranges)
        common.current_cryscheck.SetMessageID(r.inline_message_id)
        bot.edit_message_text(common.current_cryscheck.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_CRYSTALS)
    elif r.result_id == 'arsenal':
        log.debug("%s created arsenal check" % user)
        _, time = hlp.IsArsQuery(r)
        hlp.LogEvent(ICON_ARS + " %s создал чек арсенала (ярость в %s)" % (user.GetString(with_link=False), time))
        common.current_arscheck = Arsenal(time)
        common.current_arscheck.SetMessageID(r.inline_message_id)
        bot.edit_message_text(common.current_arscheck.GetText(), inline_message_id=r.inline_message_id,
                              parse_mode="markdown", reply_markup=kb.KEYBOARD_ARS).wait()
        rage_msg_text = ICON_RAGE+" *Ярость в %0.2d:%0.2d*" % (common.current_arscheck.rage_time.hour, common.current_arscheck.rage_time.minute)
        rage_msg = bot.send_message(common.warchat_id, rage_msg_text, parse_mode="markdown").wait()
        common.current_arscheck.SetRageMessageID(rage_msg.message_id)
        if common.settings.GetSetting("pin") and not common.DEBUG_MODE:
            bot.pin_chat_message(common.warchat_id, rage_msg.message_id)
    elif r.result_id == 'numbers':
        log.debug("%s created numbers check" % user)
        _, numbers = hlp.IsNumbersQuery(r)
        if len(numbers) == 1:
            hlp.LogEvent(ICON_NUMBERS + " %s создал чек номеров (%s)" % (user.GetString(with_link=False), numbers[0]))
            log.debug("%s created screens numbers check (%s)" % (user, numbers[0]))
            common.current_numcheck = NumbersCheck(int(numbers[0]))
            common.current_numcheck.SetMessageID(r.inline_message_id)
        else:
            hlp.LogEvent(ICON_NUMBERS + " %s создал чек номеров по игре (%s)" % (user.GetString(with_link=False), len(numbers)))
            log.debug("%s created in-game numbers check (%s)" % (user, ' '.join(str(num) for num in numbers)))
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
    text += "/help вывод этой справки\n"
    text += "/admins вывод списка офицеров\n"
    if hlp.IsUserAdmin(m.from_user.id):
        if str(userid) == common.ROOT_ADMIN[0]:
            text += "/settings изменить глобальные настройки бота\n"
            text += "/statbackup создать резервную копию текущей статистики\n"
            text += "/statrestore восстановить статистику по резервной копии\n"
            text += "/debug ВКЛ/ВЫКЛ режим отладки\n"
        text += "/officer инструкция для офицеров\n"
        text += "/reset аварийный сброс бота\n"
        # text += "\nТакже я умею `составлять список противников по скриншотам` из поиска гильдий, " + \
        #         "если послать их мне в личные сообщения в виде альбома.\n"

        text += "\n %s *При наличии текущего боя:*\n" % ICON_SWORDS
        text += "/bstart начать бой\n"
        text += "/bstop завершить/отменить бой\n"
        text += "/checklist получить список всех участвующих в текущем бою\n"

        text += "\n🗡 *В военном чате:*\n"
        if str(userid) == common.ROOT_ADMIN[0]:
            text += "/setadmins обновить список офицеров (в военном чате)\n"
            text += "/logchat запомнить чат событий\n"
            text += "/debugchat запомнить чат отладки\n"
        text += "/warchat запомнить военный чат _(для отправки сообщений боя)_\n"
        text += "/best показать список лучших _(только после окончания ВГ [Вс, Пн] )_\n"
        # text += "/snow вызвать Снегурочку! _(только в Вс после окончания ВГ)_\n"
    else:
        pass # stub for adding only non-admin help
    bot.send_message(userid, text, parse_mode="markdown")
    if not hlp.IsUserAdmin(m.from_user.id):
        hlp.SendHelpNonAdmin(m)
    bot.delete_message(m.chat.id, m.message_id)

#
# Help guide for officer
# (private bot chat)
#
@bot.message_handler(commands=["officer"])
def show_help_officer(m):
    userid = m.from_user.id
    if hlp.IsUserAdmin(m.from_user.id):
        text =  ICON_OFFICER+" *Инструкция по ведению боя для офицера*\n" + \
                "\n_Все команды следует вводить в военном чате_\n"
        text += "\n0️⃣ *До начала ВГ*\n" + \
                "`@assassinsgwbot чек` - создать чек перед ВГ.\n" + \
                "+ _Лучше создавать заранее, а завершать перед первым боем_\n"
        text += "\n1️⃣ *Начало боя*\n" + \
                "`@assassinsgwbot бой XX:XX необязательный_комментарий` - создать чек на бой\n" + \
                "+ _После запуска поиска нажать на '"+ICON_ROLL+"', чтобы пришло уведомление в чат_\n" + \
                "+ _Когда бой начнется, нажать на '"+ICON_START+"', чтобы пришло уведомление в чат и в личку участников_\n" + \
                "+ _Если кто-нибудь опоздает к началу и отметится позже, в чат придет уведомление_\n" + \
                "+ _После окончания боя нажать на '"+ICON_STOP+"', чтобы завершить бой и все другие активные чеки_\n"
        text += "\n2️⃣ *Арсенал и ярость*\n" + \
                "`@assassinsgwbot арс XX:XX` - создать чек арсенала (указывается время ярости)\n" + \
                "+ _Отдельным сообщением дать указания, кому и сколько бить арсенал_\n" + \
                "+ _При заполнении полосы до критической отметки в чат придет уведомление (регулируется администратором бота)_\n" + \
                "+ _При полном заполнении полосы в чат и в личку участников придет уведомление о ярости_\n"
        text += "\n3️⃣ *Атака номеров*\n" + \
                "`@assassinsgwbot номера N` - создать чек N номеров по скринам \n" + \
                "`@assassinsgwbot номера X Y Z ...` - создать чек перечисленных номеров по игре\n" + \
                "+ _Сами скрины посылаются в чат вручную_\n" + \
                "+ _В качестве альтернативы можно послать скрины в личку бота в виде альбома, и он выдаст текстовую версию номеров_\n" + \
                "+ _Кнопки '"+ICON_500+"' и '"+ICON_1000+"' доступны только вам, используйте при необходимости_\n" + \
                "+ _При достижении отметки '"+ICON_1000+"' чек номеров автоматически завершится_\n" + \
                "+ _Если требуется 'добить' номера по игре, не бойтесь завершить текущий чек и начать новый_\n"
        text += "\n4️⃣ *Прочее*\n" + \
                "`@assassinsgwbot кри` - создать чек по кри\n" + \
                "+ _Иногда бывает полезно (особенно на топах) проверить, сколько кри осталось у бойцов_\n" + \
                "+ _Примечание: настройки кнопок регулируются администратором бота_\n"
    else:
        pass # stub for adding only non-admin help
    bot.send_message(userid, text, parse_mode="markdown")
    if not hlp.IsUserAdmin(m.from_user.id):
        hlp.SendHelpNonAdmin(m)
    bot.delete_message(m.chat.id, m.message_id)

#
# Set war chat
# (chat command)
#
@bot.message_handler(commands=['warchat'])
def command_set_warchat(m):
    if hlp.IsInPrivateChat(m):
        hlp.SendHelpWrongChat(m.from_user.id, "/warchat", "запомнить военный чат", False)
        return
    bot.delete_message(m.chat.id, m.message_id)
    if not hlp.IsUserAdmin(m.from_user.id):
        hlp.SendHelpNonAdmin(m)
        return
    # if common.warchat_id != None and common.warchat_id == m.chat.id:
    current = common.settings.GetSetting("bot_warchat")
    if current and current == m.chat.id:
        bot.send_message(m.from_user.id, ICON_CANCEL+" Этот чат уже задан как военный!")
    else:
        common.warchat_id = m.chat.id
        common.settings.SetSetting("bot_warchat", m.chat.id)
        log.info("war chat set: %d", common.warchat_id)
        bot.send_message(m.from_user.id, ICON_CHECK+" Военный чат успешно задан!")
        aws_settings_backup()


#
# Set log chat
# (chat command)
#
@bot.message_handler(commands=['logchat'])
def command_set_logchat(m):
    if hlp.IsInPrivateChat(m):
        hlp.SendHelpWrongChat(m.from_user.id, "/logchat", "запомнить чат событий", False)
        return
    bot.delete_message(m.chat.id, m.message_id)
    if not hlp.IsUserAdmin(m.from_user.id):
        hlp.SendHelpNonAdmin(m)
        return
    # if common.logchat_id != None and common.logchat_id == m.chat.id:
    current = common.settings.GetSetting("bot_logchat")
    if current and current == m.chat.id:
        bot.send_message(m.from_user.id, ICON_CANCEL+" Этот чат уже задан как чат событий!")
    else:
        common.logchat_id = m.chat.id
        common.settings.SetSetting("bot_logchat", m.chat.id)
        log.info("log chat set: %d", common.logchat_id)
        bot.send_message(m.from_user.id, ICON_CHECK+" Чат событий успешно задан!")
        aws_settings_backup()


#
# Set log chat
# (chat command)
#
@bot.message_handler(commands=['debugchat'])
def command_set_debugchat(m):
    if hlp.IsInPrivateChat(m):
        hlp.SendHelpWrongChat(m.from_user.id, "/debugchat", "запомнить чат отладки", False)
        return
    bot.delete_message(m.chat.id, m.message_id)
    if not hlp.IsUserAdmin(m.from_user.id):
        hlp.SendHelpNonAdmin(m)
        return
    # if common.logchat_id != None and common.logchat_id == m.chat.id:
    current = common.settings.GetSetting("bot_debugchat")
    if current and current == m.chat.id:
        bot.send_message(m.from_user.id, ICON_CANCEL+" Этот чат уже задан как чат отладки!")
    else:
        common.debugchat_id = m.chat.id
        common.settings.SetSetting("bot_debugchat", m.chat.id)
        log.info("debug chat set: %d", common.debugchat_id)
        bot.send_message(m.from_user.id, ICON_CHECK+" Чат отладки успешно задан!")
        aws_settings_backup()


#
# Toggle debug mode
# (private bot chat)
#
@bot.message_handler(commands=['debug'])
def command_toggle_debug_mode(m):
    if not hlp.IsInPrivateChat(m):
        hlp.SendHelpWrongChat(m.from_user.id, "/debug", "ВКЛ/ВЫКЛ режим отладки", True)
        return
    bot.delete_message(m.chat.id, m.message_id)
    if not hlp.IsUserAdmin(m.from_user.id) or str(m.from_user.id) != common.ROOT_ADMIN[0]:
        hlp.SendHelpNonAdmin(m)
        return
    # switch mode
    common.DEBUG_MODE = not common.DEBUG_MODE
    bot.send_message(m.from_user.id, "🔨 Режим отладки *%s*!" % ("ВКЛЮЧЕН" if common.DEBUG_MODE else "ОТКЛЮЧЕН"), parse_mode="markdown").wait()
    if common.DEBUG_MODE:
        text  = "🛸 Все сообщения перенаправляются в чат отладки\n"
        text += "📌 Закрепление сообщений отключено\n"
        text += "📈 Запись статистики не ведется\n\n"
        text += "‼️ Не забудьте выключить режим после завершения отладки"
        bot.send_message(m.from_user.id, text)
        # switch war chat and debug chat
        warchat_backup = common.warchat_id
        common.warchat_id = common.debugchat_id
        common.debugchat_id = warchat_backup
    else:
        # switch war chat and debug chat back
        warchat_backup = common.debugchat_id
        common.debugchat_id = common.warchat_id
        common.warchat_id = warchat_backup




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
    if not hlp.IsUserAdmin(m.from_user.id):
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
                text =  "Текущий бой: %0.2d:%0.2d.\n\n" % (*common.current_battle.GetTime(start=True),)
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
        elif inline_error == "existing_crystals":
            text =  "Уже имеетя активный чек по кри\n\n" + \
                    ("Чтобы начать чек по кри заново, необходимо завершить (%s) предыдущий.\n" % ICON_STOP) + \
                    "Если чек был добавлен ошибочно - завершите чек, " + \
                    "затем создайте новый, а старое сообщение удалите."
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
    if not hlp.IsUserAdmin(m.from_user.id):
        hlp.SendHelpNonAdmin(m)
        return
    if not hlp.CanStartNewBattle():
        if not common.current_battle.is_started:
            text = "Запустить текущий бой [%0.2d:%0.2d]?" % (*common.current_battle.GetTime(start=True),)
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
    if not hlp.IsUserAdmin(m.from_user.id):
        hlp.SendHelpNonAdmin(m)
        return
    if not hlp.CanStartNewBattle():
        if not common.current_battle.is_postponed:
            text = "Завершить текущий бой [%0.2d:%0.2d]?" % (*common.current_battle.GetTime(start=True),)
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
    if not hlp.IsUserAdmin(m.from_user.id):
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
    if not hlp.IsUserAdmin(m.from_user.id):
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
    common.aws_admins_backup(newlist=admins)
    bot.send_message(m.chat.id, ICON_OFFICER+" Список офицеров обновлен")
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
            if str(user[0]) == common.ROOT_ADMIN[0]: # show admins IDs for root admin
                text += ICON_MEMBER+" %s _(ID=%s)_\n" % (common.admins[admin], admin)
            else:
                text += (ICON_MEMBER+" %s\n" % common.admins[admin])
    bot.send_message(user[0], text, parse_mode="markdown")
    return

#
# Emergency reset all checks query
# (private bot chat)
#
@bot.message_handler(commands=['reset'])
def command_reset(m):
    if not hlp.IsInPrivateChat(m):
        bot.delete_message(m.chat.id, m.message_id)
        hlp.SendHelpWrongChat(m.from_user.id, "/reset", "выполнить полный сброс бота", True)
        return
    if not hlp.IsUserAdmin(m.from_user.id):
        hlp.SendHelpNonAdmin(m)
        return
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to reset bot" % (*user,))
    bot.send_message(m.chat.id, "Выполнить полный сброс?", reply_markup=kb.KEYBOARD_RESET)

#
# Emergency reset all checks processing
# (private bot chat)
#
@bot.message_handler(func=lambda message: message.text in kb.RESET_CONTROL_OPTIONS)
def hard_reset(m):
    # it is a bug actually to use privately generated keyboard buttons outside private bot chat
    # should not happen in any case, but who knows?
    if not hlp.IsInPrivateChat(m):
        return
    if not hlp.IsUserAdmin(m.from_user.id):
        hlp.SendHelpNonAdmin(m)
        return
    markup = types.ReplyKeyboardRemove(selective=False)
    if m.text == kb.RESET_CONTROL_OPTIONS[1]: # cancel
        bot.send_message(m.from_user.id, "⛔️ Действие отменено", reply_markup=markup)
        log.debug("Reset calcelled")
        return
    if not hlp.CanStartNewPrecheck(): # should hit 'end' to start another
        common.current_precheck.DoEndPrecheck()
        bot.edit_message_text(common.current_precheck.GetText(), inline_message_id=common.current_precheck.check_id,
                              parse_mode="markdown")
        common.current_precheck = None
    if common.current_cryscheck: # postponed is not a condition that check ended
        common.current_cryscheck.DoEndCryscheck()
        bot.edit_message_text(common.current_cryscheck.GetText(), inline_message_id=common.current_cryscheck.check_id,
                              parse_mode="markdown")
        common.current_cryscheck = None
    reset_battlechecks(m)
    try:
        bot.send_message(m.from_user.id, ICON_CHECK+" Бот успешно сброшен", reply_markup=markup)
    except: # no need to send private message if checks have been reset via battle control
        pass
    log.debug("Reset successful")


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
    if not hlp.IsUserAdmin(m.from_user.id):
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
        reset_battlechecks(m)
        bot.send_message(m.chat.id, "❎ Бой успешно завершен", reply_markup=markup)
    else: # Отмена
        bot.send_message(m.chat.id, "⛔️ Действие отменено", reply_markup=markup)


#
# Handler updating internal chat members list
# (add new user)
#
@bot.message_handler(func=lambda m: True, content_types=['new_chat_participant'])
def on_user_joins(m):
    id = str(m.new_chat_participant.id)
    if id not in common.WarChatMembers.keys():
        common.WarChatMembers[id] = { "blame_cnt": 0 }
    common.WarChatMembers[id]["is_active"] = True
    common.aws_warchat_members_backup()



#
# Handler updating internal chat members list
# (disactivate left user)
#
@bot.message_handler(func=lambda m: True, content_types=['left_chat_participant'])
def on_user_leaves(m):
    id = str(m.left_chat_participant.id)
    if id in common.WarChatMembers.keys():
        del common.WarChatMembers[id]
        # TODO how to fix leave-join abuse? this does not work if user was actually kicked from guild
        # common.WarChatMembers[id]["is_active"] = False
        common.aws_warchat_members_backup()


#
# Blame command
# (chat command)
# NOTE: blame list is not updated for past GW if this command was not called!
#
@bot.message_handler(commands=["gwblame"])
def blame_for_gw(m):
    # print("blame_for_gw")
    # print(m)
    user = User(m.from_user.id, m.from_user.first_name, m.from_user.username)
    log.debug("User %s is trying to use /gwblame" % user)
    if not hlp.IsUserAdmin(user._id):
        log.error("Failed (not an admin)")
        hlp.SendHelpNonAdmin(m)
        return
    if hlp.IsInPrivateChat(m):
        log.error("Failed (in private chat)")
        hlp.SendHelpWrongChat(user._id, "/gwblame", "поругать тунеядцев за ВГ", False)
        return
    # allow only once per week
    elapsed = int((datetime.datetime.now() - common.gwblame_timestamp).total_seconds())
    if elapsed < 1*60*60*24*6:
        common.bot.send_message(user._id, "Поругать тунеядцев можно только один раз в неделю!")
        log.error("Failed: wrong time")
        return

    users_to_blame = {} # {userid: {blame_desc}}
    users_to_kick  = [] # [userid]
    users_checked  = [user._id for user in common.current_precheck.daily.keys()]
    users_bailed   = [user._id for user in common.current_precheck.cancels.keys()]
    users_scored   = [user._id for user in common.statistics.statistics[0].stats.keys()] 
    # form list of users to blame
    for user in common.WarChatMembers.keys():
        blame_desc = { "is_going": False,
                       "is_scored": False
                     }
        # WarChatMembers user -> checked in preckeck as not-going? -> dont blame
        if int(user) in users_bailed:
            continue
        elif int(user) in users_checked:
            blame_desc["is_going"] = True
        # WarChatMembers user -> in any statistics? -> dont blame
        # TODO add option to check for minimal scores
        if int(user) in users_scored:
            continue
        else:
            blame_desc["is_scored"] = False
        users_to_blame[str(user)] = blame_desc
    # set text for blame message
    common.bot.send_chat_action(common.warchat_id, "typing")
    text = "🦞 *Список тунеядцев последней ВГ*:\n\n"
    if len(users_to_blame) > 0:
        for user in users_to_blame:
            user_o = bot.get_chat_member(common.warchat_id, int(user)).wait()
            print(user_o)
            user_string = User(user_o.user.id, user_o.user.first_name, user_o.user.username).GetString()
            text += ICON_MEMBER+" %s" % user_string
            text += " " + ICON_LIST*(not users_to_blame[user]["is_going"])
            text += " " + ICON_STAR*(not users_to_blame[user]["is_scored"])
            text += "\n"
            common.WarChatMembers[user]["blame_cnt"] = common.WarChatMembers[user]["blame_cnt"] + 1
    else:
        text += "_(список пуст)_"
    # hide command from chat history
    bot.delete_message(m.chat.id, m.message_id)
    bot.send_message(common.warchat_id, text, parse_mode="markdown")
    # imitate typing
    common.bot.send_chat_action(common.warchat_id, "typing").wait()
    time.sleep(3)
    # form users list to suggest kick
    for user in common.WarChatMembers.keys():
        if common.WarChatMembers[user]["blame_cnt"] > 2:
            users_to_kick.append(int(user))
    # set text to kick message
    if len(users_to_kick) > 0:
        text = "☠️ Рекомендуется кик:\n\n"
        for user in users_to_kick:
            user_o = bot.get_chat_member(common.warchat_id, user).wait()
            print(user_o)
            user_string = User(user_o.user.id, user_o.user.first_name, user_o.user.username).GetString()
            text += ICON_MEMBER+" %s _(%d)_\n" % (user_string, common.WarChatMembers[str(user)]["blame_cnt"])
        bot.send_message(common.warchat_id, text, parse_mode="markdown")
    common.gwblame_timestamp = datetime.datetime.now()
    common.aws_warchat_members_backup()

#
# Forgive command
# (chat command)
#
@bot.message_handler(commands=["gwforgive"])
def forgive_for_gw(m):
    # print("forgive_for_gw")
    # print(m)
    user = User(m.from_user.id, m.from_user.first_name, m.from_user.username)
    log.debug("User %s is trying to use /gwforgive" % user)
    if not hlp.IsUserAdmin(user._id):
        log.error("Failed (not an admin)")
        hlp.SendHelpNonAdmin(m)
        return
    if hlp.IsInPrivateChat(m):
        log.error("Failed (in private chat)")
        hlp.SendHelpWrongChat(user._id, "/gwforgive", "простить тунеядцев за ВГ", False)
        return
    for user in common.WarChatMembers.keys():
        common.WarChatMembers[user]["blame_cnt"] = 0
    # hide command from chat history
    bot.delete_message(m.chat.id, m.message_id)
    bot.send_message(m.chat.id, "🙏 Всем игрокам прощено тунеядство на ВГ!")


#
# Call for fun mode 'Snow White'
# (war chat command)
#
# @bot.message_handler(commands=['snow'])
# def command_snow(m):
#     # print(m)
#     user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
#     log.debug("User %d (%s %s) is trying to call Snow!" % (*user,))
#     if hlp.IsInPrivateChat(m):
#         hlp.SendHelpWrongChat(m.from_user.id, "/snow", "вызвать Снегурочку", False)
#         return
#     bot.delete_message(m.chat.id, m.message_id)
#     if not hlp.IsUserAdmin(m.from_user.id):
#         log.error("Failed: not an admin")
#         hlp.SendHelpNonAdmin(m)
#         return
#     if not hlp.IsGWEndingTime():
#         bot.send_message(user[0], "Ой! Вызвать Снегурочку можно только в воскресенье после окончания ВГ!")
#         log.error("Failed: wrong time")
#         return
    
#     if common.current_snowwhite == {}:
#         common.current_snowwhite["message"] = bot.send_message(m.chat.id,
#                                              ICON_SNOW+" Всем привет!",
#                                              reply_markup=kb.KEYBOARD_SNOWWHITE).wait()
#         common.current_snowwhite["praised"] = []
#         log.info("Snow White called!")
#     else:
#         log.error("Snow White is already here!")

#
# Snow White control
# (war chat keyboard action)
#
# @bot.callback_query_handler(func=lambda call: call.data == cb.SNOW_PRAISE_CALLBACK)
# def snow_control(call):
#     # print("snow_control")
#     # print(call)
#     user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
#     log.debug("User %d (%s %s) is cheering Snow White" % (*user,))
    
#     if common.current_snowwhite != {}:
#         if not user[0] in common.current_snowwhite["praised"]:
#             log.debug("Praised")
#             bot.send_message(call.message.chat.id, hlp.SnowGeneratePraise(user),
#                              parse_mode="markdown", disable_notification=True)
#             common.current_snowwhite["praised"].append(user[0])
#             bot.answer_callback_query(call.id)
#         else:
#             log.error("Failed: already praised")
#             bot.answer_callback_query(call.id, "Поприветствовать Снегурочку можно только один раз!")
#         if not hlp.IsGWEndingTime():
#             log.info("Snow White overtime, ending")
#             bot.delete_message(common.current_snowwhite["message"].chat.id, common.current_snowwhite["message"].message_id)
#             bot.send_message(call.message.chat.id,
#                              ICON_SNOW+" До встречи в следюущее воскресенье!",
#                              disable_notification=True)
#             common.current_snowwhite = {}
#         return
#     log.error("Bug! User pressed Snow White keyboard button with to current_snowwhite!")
#     bot.answer_callback_query(call.id)


#
# Test command
# (debug command)
#
@bot.message_handler(commands=["test"])
def debug_test_command(m):
    log.info("debug_test_command")
    # print(m)
    if common.DEBUG_MODE:
        import tempfile
        log.debug("Debug mode is ON, processing...")
        user = User(m.from_user.id, m.from_user.first_name, m.from_user.username)
        text = "User %s sent /test command." % user
        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix='.txt')
        # write whole message object into file (change on needs)
        temp_file.write(str(m))
        temp_file.close()
        with open(temp_file.name, "r") as tfile:
            bot.send_document(common.warchat_id, tfile, caption=text, disable_notification=True).wait()
            tfile.close()
        os.remove(temp_file.name)


def AWSRestore():
    aws_settings_restore()
    common.aws_admins_restore()
    common.aws_warchat_members_restore()
    aws_stat_restore()
    aws_precheck_restore()
    aws_crystals_restore()
    # attempt to restore battle checks (use class names here!)
    hlp.AWSCheckRestore("Battle")
    hlp.AWSCheckRestore("Arsenal")
    hlp.AWSCheckRestore("NumbersCheck")


if __name__ == '__main__':
    if "HEROKU" in list(os.environ.keys()):
        log.warning("Running on Heroku, setup webhook")
        server = Flask(__name__)
        AWSRestore()
        bot.send_message(int(common.ROOT_ADMIN[0]), "🔧 Бот запущен!")

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
        AWSRestore()
        bot.send_message(int(common.ROOT_ADMIN[0]), "🔧 Бот запущен!")

        bot.polling(none_stop=True, interval=0, timeout=20)
