#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#

from telebot import types
from icons import *

# keyboards
# battle check (from the battle chat)
KEYBOARD_CHECK = types.InlineKeyboardMarkup(row_width=3)
buttonPlus = types.InlineKeyboardButton(text=ICON_CHECK, callback_data=CHECK_CHECK_CALLBACK)
buttonRage = types.InlineKeyboardButton(text=ICON_RAGE, callback_data=CHECK_RAGE_CALLBACK)
buttonFast = types.InlineKeyboardButton(text=ICON_FAST, callback_data=CHECK_FAST_CALLBACK)
buttonArsenal = types.InlineKeyboardButton(text=ICON_ARS, callback_data=CHECK_ARS_CALLBACK)
buttonThinking = types.InlineKeyboardButton(text=ICON_THINK, callback_data=CHECK_THINK_CALLBACK)
buttonCancel = types.InlineKeyboardButton(text=ICON_CANCEL, callback_data=CHECK_CANCEL_CALLBACK)
buttonStart = types.InlineKeyboardButton(text=ICON_START, callback_data=CHECK_START_CALLBACK)
buttonStop = types.InlineKeyboardButton(text=ICON_STOP, callback_data=CHECK_STOP_CALLBACK)
KEYBOARD_CHECK.add(buttonPlus, buttonRage, buttonFast,
                   buttonArsenal, buttonThinking, buttonCancel,
                   buttonStart, buttonStop)

# for started battle
KEYBOARD_LATE = types.InlineKeyboardMarkup(row_width=2)
buttonLate = types.InlineKeyboardButton(text=ICON_LATE, callback_data=CHECK_LATE_CALLBACK)
KEYBOARD_LATE.add(buttonCancel, buttonLate, buttonStop)

CHECK_OPTIONS = [buttonPlus.callback_data,
                 buttonRage.callback_data,
                 buttonFast.callback_data,
                 buttonArsenal.callback_data,
                 buttonThinking.callback_data,
                 buttonCancel.callback_data,
                 buttonLate.callback_data,
                ]
CHECK_CONTROL_OPTIONS = [buttonStart.callback_data,
                         buttonStop.callback_data,
                        ]

# battle control (from the bot chat)
KEYBOARD_START = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
KEYBOARD_STOP = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
buttonStartPrivate = types.KeyboardButton(text=ICON_START+" Запустить")
buttonStopPrivate = types.KeyboardButton(text=ICON_STOP+" Завершить")
buttonCancelPrivate = types.KeyboardButton(text=ICON_EXIT+" Отмена")
KEYBOARD_START.add(buttonStartPrivate, buttonCancelPrivate)
KEYBOARD_STOP.add(buttonStopPrivate, buttonCancelPrivate)

CHECK_CONTROL_OPTIONS_PRIVATE = [buttonStartPrivate.text, buttonStopPrivate.text, buttonCancelPrivate]

# war pre-check
KEYBOARD_PRECHECK = types.InlineKeyboardMarkup(row_width=3)
buttonFr = types.InlineKeyboardButton(text=ICON_FR, callback_data=PRECHECK_FR_CALLBACK)
buttonSat = types.InlineKeyboardButton(text=ICON_SAT, callback_data=PRECHECK_SAT_CALLBACK)
buttonSun = types.InlineKeyboardButton(text=ICON_SUN, callback_data=PRECHECK_SUN_CALLBACK)
buttonThinking = types.InlineKeyboardButton(text=ICON_THINK, callback_data=PRECHECK_THINK_CALLBACK)
buttonSpacer = types.InlineKeyboardButton(text=" ", callback_data="PreCheck_spacer")
buttonCancel = types.InlineKeyboardButton(text=ICON_CANCEL, callback_data=PRECHECK_CANCEL_CALLBACK)
buttonStop = types.InlineKeyboardButton(text=ICON_STOP, callback_data=PRECHECK_STOP_CALLBACK)
KEYBOARD_PRECHECK.add(buttonFr, buttonSat, buttonSun,
                      buttonThinking, buttonSpacer, buttonCancel,
                      buttonStop)

PRECHECK_OPTIONS = [buttonFr.callback_data,
                    buttonSat.callback_data,
                    buttonSun.callback_data,
                    buttonThinking.callback_data,
                    buttonCancel.callback_data,
                   ]
PRECHECK_CONTROL_OPTIONS = [buttonStop.callback_data]
