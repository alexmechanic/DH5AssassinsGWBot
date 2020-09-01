#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class and methods representing persistent settings
#

import telebot, os, time, pickle, re
from telebot import types
from logger import get_logger
from flask import Flask, request

import common
from common import bot
from icons import *
import helpers as hlp
import settings.keyboards as kb
import settings.callbacks as cb
import settings.messages as msg

log = get_logger("bot." + __name__)


settings_message_id = None
need_send_again = False
is_wait_command = False

class MenuItem():
    parent = None
    id = 0
    children = []
    name = ""
    header = ""
    description = ""
    keyboard = None
    callbacks = []
    responce_cb = None
    is_active = False
    default_value = 0

    def __init__(self, name=None, header=None, description=None, keyboard=None, callbacks=None, responce_cb=None, default_value=None):
        if not name:
            return None
        self.parent = None
        self.id = 0
        self.children = []
        self.name = name
        self.header = header
        if not description:
            description = msg.TEXT_UNKNOWN
        self.description = description
        self.keyboard = keyboard
        self.callbacks = callbacks
        self.responce_cb = responce_cb
        self.is_active = False
        self.default_value = default_value

    def __eq__(self, other):
        if other == None:
            return False
        return self.id == other.id

    def __ne__(self, other):
        return not(self == other)

    def __repr__(self):
        text = ""
        _iter = self.parent
        while _iter:
            text += "    "
            _iter = _iter.parent
        text += "ID:" + str(self.id) + " {" + self.name + "} "
        if self.header:
            text += "[" + self.header + "]"
        if self.description:
            text += " (" + self.description + ")"
        text += " " + ICON_CHECK*self.is_active
        if not self.id: # root prints full tree
            if len(self.children):
                text += "\n"
            for child in self.children:
                text += child.__repr__()
        return text + "\n"

    def SetParent(self, parent):
        if not isinstance(parent, MenuItem):
            return
        self.parent = parent
        self.id = parent.id*10 + len(parent.children) + 1
        self.parent.children.append(self)

    def AddChild(self, child):
        if not isinstance(parent, MenuItem):
            return
        if child.parent:
            return
        child.parent = self
        child.id = self.id*10 + len(self.children) + 1
        self.children.append(child)

    def AddChild(self, name=None, header=None, description=None, keyboard=None, callbacks=None, responce_cb=None, default_value=None):
        item = MenuItem(name, header, description, keyboard, callbacks, responce_cb, default_value)
        item.SetParent(self)
        return item

    def FindItem(self, name=None, callback=None, responce=None, active=False):
        foundItem = None
        if active:
            if self.is_active:
                return self
            for child in self.children:
                foundItem = child.FindItem(active=active)
                if foundItem:
                    break
        elif name:
            if self.name == name:
                return self
            for child in self.children:
                foundItem = child.FindItem(name=name)
                if foundItem:
                    break
        elif responce:
            if self.responce_cb == responce:
                return self
            for child in self.children:
                foundItem = child.FindItem(responce=responce)
                if foundItem:
                    break
        else:
            if callback in self.callbacks:
                return self
            for child in self.children:
                foundItem = child.FindItem(callback=callback)
                if foundItem:
                    break
        return foundItem

def CreateMenu():
    menu = MenuItem(name="root", description="⚙️ Список настроек:", keyboard=kb.KEYBOARD_SETTINGS_START, callbacks=kb.SETTINGS_START_OPTIONS)
    # Common
    common = menu.AddChild("common",
                           msg.BUTTON_COMMON, msg.TEXT_COMMON,
                           kb.KEYBOARD_SETTINGS_COMMON,
                           kb.SETTINGS_COMMON_OPTIONS,
                           cb.SETTINGS_COMMON_CALLBACK)
    common.AddChild("pin",
                    msg.BUTTON_COMMON_PIN, msg.TEXT_COMMON_PIN,
                    kb.KEYBOARD_SETTINGS_COMMON_PIN,
                    kb.SETTINGS_COMMON_PIN_OPTIONS,
                    cb.SETTINGS_COMMON_PIN_CALLBACK,
                    0)
    common.AddChild("backup_timeout",
                    msg.BUTTON_COMMON_BACKUP_TIMEOUT, msg.TEXT_COMMON_BACKUP_TIMEOUT,
                    kb.KEYBOARD_SETTINGS_EMPTY,
                    kb.SETTINGS_EMPTY_OPTIONS,
                    cb.SETTINGS_COMMON_BACKUP_TIMEOUT_CALLBACK,
                    15)
    # Checks
    checks = menu.AddChild("checks",
                           msg.BUTTON_CHECKS, msg.TEXT_CHECKS,
                           kb.KEYBOARD_SETTINGS_CHECKS,
                           kb.SETTINGS_CHECKS_OPTIONS,
                           cb.SETTINGS_CHECKS_CALLBACK)
    checks.AddChild("precheck",
                    msg.BUTTON_PRECHECK, msg.TEXT_PRECHECK + "\n" + msg.TEXT_UNKNOWN,
                    kb.KEYBOARD_SETTINGS_EMPTY,
                    kb.SETTINGS_EMPTY_OPTIONS,
                    cb.SETTINGS_CHECKS_PRECHECK_CALLBACK)
    checks.AddChild("battle",
                    msg.BUTTON_BATTLE, msg.TEXT_BATTLE + "\n" + msg.TEXT_UNKNOWN,
                    kb.KEYBOARD_SETTINGS_EMPTY,
                    kb.SETTINGS_EMPTY_OPTIONS,
                    cb.SETTINGS_CHECKS_BATTLE_CALLBACK)
    ars = checks.AddChild("arsenal",
                          msg.BUTTON_ARSENAL, msg.TEXT_ARSENAL,
                          kb.KEYBOARD_SETTINGS_ARS,
                          kb.SETTINGS_ARS_OPTIONS,
                          cb.SETTINGS_CHECKS_ARSENAL_CALLBACK)
    ars.AddChild("critical_threshold",
                 msg.BUTTON_ARSENAL_CRIT, msg.TEXT_ARSENAL_CRIT,
                 kb.KEYBOARD_SETTINGS_EMPTY,
                 kb.SETTINGS_EMPTY_OPTIONS,
                 cb.SETTINGS_CHECKS_ARSENAL_CRIT_THRESHOLD_CALLBACK,
                 120)
    ars.AddChild("critical_pin",
                 msg.BUTTON_ARSENAL_PIN, msg.TEXT_ARSENAL_PIN,
                 kb.KEYBOARD_SETTINGS_COMMON_PIN,
                 kb.SETTINGS_COMMON_PIN_OPTIONS,
                 cb.SETTINGS_CHECKS_ARSENAL_CRIT_PIN_CALLBACK,
                 0)
    checks.AddChild("numbers",
                    msg.BUTTON_NUMBERS, msg.TEXT_NUMBERS + "\n" + msg.TEXT_UNKNOWN,
                    kb.KEYBOARD_SETTINGS_EMPTY,
                    kb.SETTINGS_EMPTY_OPTIONS,
                    cb.SETTINGS_CHECKS_NUMBERS_CALLBACK)
    crystals = checks.AddChild("crystals",
                    msg.BUTTON_CRYSTALS, msg.TEXT_CRYSTALS,
                    kb.KEYBOARD_SETTINGS_CRYSTALS,
                    kb.SETTINGS_CRYSTALS_OPTIONS,
                    cb.SETTINGS_CHECKS_CRYSTALS_CALLBACK)
    crystals.AddChild("crystals_ranges",
                      msg.BUTTON_CRYSTALS_RANGES, msg.TEXT_CRYSTALS_RANGES,
                      kb.KEYBOARD_SETTINGS_EMPTY,
                      kb.SETTINGS_EMPTY_OPTIONS,
                      cb.SETTINGS_CHECKS_CRYSTALS_RANGES_CALLBACK,
                      (5000, 500))
    # Statistic
    statistic = menu.AddChild("statistic",
                              msg.BUTTON_STATISTIC, msg.TEXT_STATISTIC,
                              kb.KEYBOARD_SETTINGS_STATISTIC,
                              kb.SETTINGS_STATISTIC_OPTIONS,
                              cb.SETTINGS_STATISTIC_CALLBACK)
    statistic.AddChild("bestlist",
                       msg.BUTTON_STATISTIC_BESTLIST, msg.TEXT_STATISTIC_BESTLIST,
                       kb.KEYBOARD_SETTINGS_EMPTY,
                       kb.SETTINGS_EMPTY_OPTIONS,
                       cb.SETTINGS_STATISTIC_BESTLIST_CALLBACK,
                       3)
    statistic.AddChild("nominations",
                       msg.BUTTON_STATISTIC_NOMINATIONS, msg.TEXT_STATISTIC_NOMINATIONS,
                       kb.KEYBOARD_SETTINGS_EMPTY,
                       kb.SETTINGS_EMPTY_OPTIONS,
                       cb.SETTINGS_STATISTIC_NOMINATIONS_CALLBACK,
                       1)
    statistic.AddChild("cycletime",
                       msg.BUTTON_STATISTIC_CYCLETIME, msg.TEXT_STATISTIC_CYCLETIME,
                       kb.KEYBOARD_SETTINGS_EMPTY,
                       kb.SETTINGS_EMPTY_OPTIONS,
                       cb.SETTINGS_STATISTIC_CYCLE_TIME_CALLBACK,
                       4)
    return menu

Menu = CreateMenu()
activeMenu = Menu

#
# Back button press
#
@bot.callback_query_handler(func=lambda call: call.data in kb.buttonBack.callback_data)
def settings_back(c):
    global activeMenu
    retfunc = None
    if activeMenu.parent == None:
        retfunc = change_settings
    elif activeMenu.parent.parent == None:
        retfunc = change_settings
    else:
        retfunc = settings_navigate
        c.data  = activeMenu.parent.responce_cb
    activeMenu = activeMenu.parent
    try:
        bot.answer_callback_query(c.id)
    except:
        pass
    retfunc(c)

#
# Update setting message
#
@bot.message_handler(func=lambda message: activeMenu and activeMenu.parent and is_wait_command)
def update_setting(m):
    global activeMenu, is_wait_command, need_send_again
    result = False
    if activeMenu.name == "critical_threshold":
        try:
            newvalue = int(m.text)
            if newvalue < 0 or newvalue >= 120:
                raise ValueError("Некорректное значение! Попробуйте снова.")
            common.settings.SetSetting(activeMenu.id, newvalue)
            result = True
        except Exception as err:
            bot.send_message(m.from_user.id, str(err))
    if activeMenu.name == "backup_timeout":
        try:
            newvalue = int(m.text)
            if newvalue < 0 or newvalue > 1440:
                raise ValueError("Некорректное значение! Попробуйте снова.")
            common.settings.SetSetting(activeMenu.id, newvalue)
            result = True
        except Exception as err:
            bot.send_message(m.from_user.id, str(err))
    elif activeMenu.name == "crystals_ranges":
        try:
            values = re.findall(r'\b(\d+)\b', m.text)
            if values != [] and len(values) == 2: # exactly 2 numbers
                # max >= step, step > 0
                if int(values[0]) < int(values[1]) or int(values[1]) <= 0: 
                    raise ValueError("Некорректные значения! Попробуйте снова.")
                    # not too much buttons
                if int(values[0]) // int(values[1]) > 30:
                    raise ValueError("Слишком много вариантов! Попробуйте снова.")
            else:
                raise ValueError("Некорректные значения! Попробуйте снова.")
            common.settings.SetSetting(activeMenu.id, (int(values[0]), int(values[1])))
            result = True
        except Exception as err:
            bot.send_message(m.from_user.id, str(err))
    elif activeMenu.parent.name == "statistic": # statistic settings
        try:
            newvalue = int(m.text)
            if activeMenu.name in ["bestlist", "nominations"]:
                if newvalue > 10:
                    raise ValueError("Некорректное значение! Попробуйте снова.")
            elif activeMenu.name == "cycletime":
                if newvalue > 100:
                    raise ValueError("Некорректное значение! Попробуйте снова.")
            else:
                pass # TODO: add further options
            common.settings.SetSetting(activeMenu.id, newvalue)
            result = True
        except Exception as err:
            bot.send_message(m.from_user.id, str(err))
    else: # TODO: add further options
        pass
    if result:
        is_wait_command = False
        need_send_again = True
        aws_settings_backup()
        settings_back(m)


#
# Settings command
# (private bot chat)
# Level 1 options
#
@bot.message_handler(commands=["settings"])
def change_settings(m):
    global Menu, activeMenu, settings_message_id, need_send_again
    if hlp.IsUserAdmin(m.from_user.id) and str(m.from_user.id) == common.ROOT_ADMIN[0]:
        text = activeMenu.description
        reply = activeMenu.keyboard
    else:
        text =  "Изменять глобальные настройки может только главный администратор бота.\n"
        text += "Обратитесь за подробностями к [%s](tg://user?id=%s)\n" % (common.ROOT_ADMIN[1], common.ROOT_ADMIN[0])
        reply = None
    try:
        bot.delete_message(m.from_user.id, m.message_id)
    except:
        pass
    if need_send_again:
        bot.delete_message(m.from_user.id, settings_message_id)
        settings_message_id = None 
        need_send_again = False
    if not settings_message_id:
        settings_message_id = bot.send_message(m.from_user.id, text, parse_mode="markdown", reply_markup=reply).wait().message_id
    else:
        bot.edit_message_text(text, m.from_user.id, settings_message_id, parse_mode="markdown", reply_markup=reply).wait()

#
# Menu navigation
#
@bot.callback_query_handler(func=lambda call: activeMenu and call.data in activeMenu.callbacks)
def settings_navigate(c):
    global activeMenu, settings_message_id, is_wait_command, need_send_again
    prevMenu = activeMenu
    activeMenu = activeMenu.FindItem(responce=c.data)
    text = ""
    if activeMenu:
        text = activeMenu.description
        if activeMenu.name in ["pin", "critical_pin"]:
            text += "\nСостояние: *%s*" % (msg.BUTTON_ON if common.settings.GetSetting(activeMenu.id, activeMenu.default_value) else msg.BUTTON_OFF)
        elif activeMenu.name == "critical_threshold":
            text += "\nТекущее значение: *%d/120*." % common.settings.GetSetting(activeMenu.id, activeMenu.default_value)
            text += "\nВведите новое значение (без суффикса /120):"
            is_wait_command = True
        elif activeMenu.name == "crystals_ranges":
            text += "\nТекущие значения: Максимум %d, шаг %d." % common.settings.GetSetting(activeMenu.id, activeMenu.default_value)
            text += "\nВведите новые значения (два числа через пробел):"
            is_wait_command = True
        elif activeMenu.name in ["bestlist", "nominations", "cycletime"]:
            text += "\nТекущее значение: *%d*." % common.settings.GetSetting(activeMenu.id, activeMenu.default_value)
            text += "\nВведите новое значение (от 1 до "
            if activeMenu.name == "cycletime":
                text += "100):"
            else:
                text += "10):"
            is_wait_command = True
        elif activeMenu.name in ["backup_timeout"]:
            text += "\nТекущее значение: *%d минут*." % common.settings.GetSetting(activeMenu.id, activeMenu.default_value)
            text += "\nВведите новое значение, от 0 (бекап после каждого действия) до 1440 (24 часа):"
            is_wait_command = True
    elif prevMenu.name in ["pin", "critical_pin"]:
        activeMenu = prevMenu
        text = activeMenu.description
        if c.data == kb.SETTINGS_COMMON_PIN_OPTIONS[0]: # on
            common.settings.SetSetting(activeMenu.id, 1)
        else:                                           # off
            common.settings.SetSetting(activeMenu.id, 0)
        text += "\nСостояние: *%s*" % (msg.BUTTON_ON if common.settings.GetSetting(activeMenu.id, activeMenu.default_value) else msg.BUTTON_OFF)
        bot.answer_callback_query(c.id, ICON_CHECK+" Изменения успешно сохранены")
        aws_settings_backup()
    if need_send_again:
        bot.delete_message(c.from_user.id, settings_message_id)
        settings_message_id = bot.send_message(c.from_user.id, text, reply_markup=activeMenu.keyboard, parse_mode="markdown").wait().message_id
        need_send_again = False
    else:
        bot.edit_message_text(text, c.from_user.id, settings_message_id, reply_markup=activeMenu.keyboard, parse_mode="markdown")
    try:
        bot.answer_callback_query(c.id)
    except:
        pass


def aws_settings_backup(filename="GWBotSettings.BAK", burst=False):
    """
    Backup current settings into pickle file.
    Upload to AWS
    @param burst Do not save backup to file
    """
    log.debug("AWS Statistic backup started")
    # if burst-upload requested (no additional file backup)
    if not burst:
        with open(filename, 'wb') as backup:
            pickle.dump(common.settings, backup, pickle.HIGHEST_PROTOCOL)
            backup.close()
    # upload file
    if hlp.AWSUploadFile(filename):
        log.debug("Settings has been successfully uploaded to AWS cloud.")
    else:
        log.error("Settings AWS upload failed.")

def aws_settings_restore(filename="GWBotSettings.BAK", force=True):
    """
    Restore whole current statistic from pickle file (download from AWS).
    @param force Remove old local backup
    """
    log.debug("AWS Settings restore started")
    try:
        # remove old statistics backup if forced update
        if force:
            if os.path.isfile(filename):
                os.remove(filename)
        # download backup
        filepath = hlp.AWSDownloadFile(filename)
        if filepath == None:
            raise Exception("Settings AWS download failed.")
        log.debug("Settings has been successfully downloaded from AWS cloud.")
        # unwrap and set object
        with open(filepath, 'rb') as f:
            common.settings = pickle.load(f)
            f.close()
        # restore bot chats ids
        common.warchat_id = common.settings.GetSetting("bot_warchat", common.DEFAULT_WARCHAT_ID)
        common.logchat_id = common.settings.GetSetting("bot_logchat", common.DEFAULT_LOGCHAT_ID)
        common.debugchat_id = common.settings.GetSetting("bot_debugchat", common.DEFAULT_DEBUGCHAT_ID)
        log.debug("Restoring settings successful (AWS)")
    except Exception as err:
        log.error("Restoring settings failed (AWS): %s", str(err))


class PersistentSettings():
    settings = {}

    def __init__(self):
        self.settings = {}

    def GetSetting(self, key, default=None):
        global Menu
        try:
            if not isinstance(key, type(Menu.id)): # by name
                item = Menu.FindItem(name=key)
                if item: # if setting belong to Settings Menu
                    key = item.id
                    default = item.default_value
                else: # if setting is global (e.g. chat ids)
                    pass
            return self.settings[key]
        except:
            return default

    def SetSetting(self, key, value):
        self.settings[key] = value

