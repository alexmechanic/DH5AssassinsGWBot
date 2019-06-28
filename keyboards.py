#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#

from telebot import types
from icons import *

# keyboards
# check (from the battle chat)
KEYBOARD_CHECK = types.InlineKeyboardMarkup(row_width=3)
buttonPlus = types.InlineKeyboardButton(text=ICON_CHECK, callback_data=ICON_CHECK)
buttonRage = types.InlineKeyboardButton(text=ICON_RAGE, callback_data=ICON_RAGE)
buttonFast = types.InlineKeyboardButton(text=ICON_FAST, callback_data=ICON_FAST)
buttonArsenal = types.InlineKeyboardButton(text=ICON_ARS, callback_data=ICON_ARS)
buttonThinking = types.InlineKeyboardButton(text=ICON_THINK, callback_data=ICON_THINK)
buttonCancel = types.InlineKeyboardButton(text=ICON_CANCEL, callback_data=ICON_CANCEL)
buttonStart = types.InlineKeyboardButton(text=ICON_START, callback_data=ICON_START)
buttonStop = types.InlineKeyboardButton(text=ICON_STOP, callback_data=ICON_STOP)
KEYBOARD_CHECK.add(buttonPlus, buttonRage, buttonFast,
                   buttonArsenal, buttonThinking, buttonCancel,
                   buttonStart, buttonStop)

# for started battle
KEYBOARD_LATE = types.InlineKeyboardMarkup(row_width=2)
buttonLate = types.InlineKeyboardButton(text=ICON_LATE, callback_data=ICON_LATE)
KEYBOARD_LATE.add(buttonCancel, buttonLate, buttonStop)

CHECK_OPTIONS = [ICON_CHECK, ICON_RAGE, ICON_FAST,
                 ICON_ARS, ICON_THINK, ICON_CANCEL, ICON_LATE]
CONTROL_OPTIONS = [ICON_START, ICON_STOP]

# battle control (from the bot chat)
KEYBOARD_START = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
KEYBOARD_STOP = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
buttonStartPrivate = types.KeyboardButton(text=ICON_START+" Запустить")
buttonStopPrivate = types.KeyboardButton(text=ICON_STOP+" Завершить")
buttonCancelPrivate = types.KeyboardButton(text=ICON_EXIT+" Отмена")
KEYBOARD_START.add(buttonStartPrivate, buttonCancelPrivate)
KEYBOARD_STOP.add(buttonStopPrivate, buttonCancelPrivate)

CONTROL_OPTIONS_PRIVATE = [buttonStartPrivate.text, buttonStopPrivate.text, buttonCancelPrivate]
