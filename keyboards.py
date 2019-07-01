#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#

from telebot import types
from icons import *

# keyboards
# battle check (from the battle chat)
KEYBOARD_CHECK = types.InlineKeyboardMarkup(row_width=6)
buttonPlus     = types.InlineKeyboardButton(text=ICON_CHECK, callback_data=CHECK_CHECK_CALLBACK)
buttonRage     = types.InlineKeyboardButton(text=ICON_RAGE, callback_data=CHECK_RAGE_CALLBACK)
buttonFast     = types.InlineKeyboardButton(text=ICON_FAST, callback_data=CHECK_FAST_CALLBACK)
buttonArsenal  = types.InlineKeyboardButton(text=ICON_ARS, callback_data=CHECK_ARS_CALLBACK)
buttonThinking = types.InlineKeyboardButton(text=ICON_THINK, callback_data=CHECK_THINK_CALLBACK)
buttonCancel   = types.InlineKeyboardButton(text=ICON_CANCEL, callback_data=CHECK_CANCEL_CALLBACK)
buttonStart    = types.InlineKeyboardButton(text=ICON_START, callback_data=CHECK_START_CALLBACK)
buttonStop     = types.InlineKeyboardButton(text=ICON_STOP, callback_data=CHECK_STOP_CALLBACK)
KEYBOARD_CHECK.add(buttonPlus, buttonRage, buttonFast,
                   buttonArsenal, buttonThinking, buttonCancel,
                   buttonStart, buttonStop)

# check for started battle
KEYBOARD_LATE = types.InlineKeyboardMarkup(row_width=2)
buttonLate    = types.InlineKeyboardButton(text=ICON_LATE, callback_data=CHECK_LATE_CALLBACK)
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

# battle arsenal
KEYBOARD_ARS    = types.InlineKeyboardMarkup(row_width=7)
buttonArs8      = types.InlineKeyboardButton(text="+8", callback_data=ARS_8_CALLBACK)
buttonArs9      = types.InlineKeyboardButton(text="+9", callback_data=ARS_9_CALLBACK)
buttonArs10     = types.InlineKeyboardButton(text="+10", callback_data=ARS_10_CALLBACK)
buttonArs11     = types.InlineKeyboardButton(text="+11", callback_data=ARS_11_CALLBACK)
buttonArs12     = types.InlineKeyboardButton(text="+12", callback_data=ARS_12_CALLBACK)
buttonArs13     = types.InlineKeyboardButton(text="+13", callback_data=ARS_13_CALLBACK)
buttonArs14     = types.InlineKeyboardButton(text="+14", callback_data=ARS_14_CALLBACK)
buttonArs24     = types.InlineKeyboardButton(text="+24", callback_data=ARS_24_CALLBACK)
buttonArs27     = types.InlineKeyboardButton(text="+27", callback_data=ARS_27_CALLBACK)
buttonArs30     = types.InlineKeyboardButton(text="+30", callback_data=ARS_30_CALLBACK)
buttonArs33     = types.InlineKeyboardButton(text="+33", callback_data=ARS_33_CALLBACK)
buttonArs36     = types.InlineKeyboardButton(text="+36", callback_data=ARS_36_CALLBACK)
buttonArs39     = types.InlineKeyboardButton(text="+39", callback_data=ARS_39_CALLBACK)
buttonArs42     = types.InlineKeyboardButton(text="+42", callback_data=ARS_42_CALLBACK)
buttonArs0      = types.InlineKeyboardButton(text="+0", callback_data=ARS_0_CALLBACK)
buttonArsCancel = types.InlineKeyboardButton(text=ICON_CANCEL, callback_data=ARS_CANCEL_CALLBACK)
buttonArsFull   = types.InlineKeyboardButton(text=ICON_RAGE, callback_data=ARS_FULL_CALLBACK)
KEYBOARD_ARS.add(buttonArs8, buttonArs9, buttonArs10, buttonArs11, buttonArs12, buttonArs13, buttonArs14,
                 buttonArs24, buttonArs27, buttonArs30, buttonArs33, buttonArs36, buttonArs39, buttonArs42,
                 buttonArs0, buttonArsCancel, buttonArsFull)
ARS_OPTIONS = [ buttonArs8.callback_data,
                buttonArs9.callback_data,
                buttonArs10.callback_data,
                buttonArs11.callback_data,
                buttonArs12.callback_data,
                buttonArs13.callback_data,
                buttonArs14.callback_data,
                buttonArs24.callback_data,
                buttonArs27.callback_data,
                buttonArs30.callback_data,
                buttonArs33.callback_data,
                buttonArs36.callback_data,
                buttonArs39.callback_data,
                buttonArs42.callback_data,
                buttonArs0.callback_data,
                buttonArsCancel.callback_data,
                buttonArsFull.callback_data
              ]
# battle control (from the bot chat)
KEYBOARD_START      = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
KEYBOARD_STOP       = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
buttonStartPrivate  = types.KeyboardButton(text=ICON_START+" Запустить")
buttonStopPrivate   = types.KeyboardButton(text=ICON_STOP+" Завершить")
buttonCancelPrivate = types.KeyboardButton(text=ICON_EXIT+" Отмена")
KEYBOARD_START.add(buttonStartPrivate, buttonCancelPrivate)
KEYBOARD_STOP.add(buttonStopPrivate, buttonCancelPrivate)

CHECK_CONTROL_OPTIONS_PRIVATE = [buttonStartPrivate.text, buttonStopPrivate.text, buttonCancelPrivate]

# war pre-check
KEYBOARD_PRECHECK = types.InlineKeyboardMarkup(row_width=6)
buttonFr          = types.InlineKeyboardButton(text=ICON_FR, callback_data=PRECHECK_FR_CALLBACK)
buttonSat         = types.InlineKeyboardButton(text=ICON_SAT, callback_data=PRECHECK_SAT_CALLBACK)
buttonSun         = types.InlineKeyboardButton(text=ICON_SUN, callback_data=PRECHECK_SUN_CALLBACK)
buttonFull        = types.InlineKeyboardButton(text=ICON_CHECK, callback_data=PRECHECK_FULL_CALLBACK)
buttonThinking    = types.InlineKeyboardButton(text=ICON_THINK, callback_data=PRECHECK_THINK_CALLBACK)
buttonCancel      = types.InlineKeyboardButton(text=ICON_CANCEL, callback_data=PRECHECK_CANCEL_CALLBACK)
buttonStop        = types.InlineKeyboardButton(text=ICON_STOP, callback_data=PRECHECK_STOP_CALLBACK)
KEYBOARD_PRECHECK.add(buttonFr, buttonSat, buttonSun,
                      buttonFull, buttonThinking, buttonCancel,
                      buttonStop)

PRECHECK_OPTIONS = [buttonFr.callback_data,
                    buttonSat.callback_data,
                    buttonSun.callback_data,
                    buttonFull.callback_data,
                    buttonThinking.callback_data,
                    buttonCancel.callback_data,
                   ]
PRECHECK_CONTROL_OPTIONS = [buttonStop.callback_data]
