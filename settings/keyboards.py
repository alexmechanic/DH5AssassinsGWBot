#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Keyboards used in inline settings messages
#

from telebot import types

import settings.messages as msg
from settings.callbacks import *

buttonBack = types.InlineKeyboardButton(text="↩︎ Назад", callback_data=SETTINGS_BACK_CALLBACK)
buttonOn   = types.InlineKeyboardButton(text=msg.BUTTON_ON, callback_data=SETTINGS_ON_CALLBACK)
buttonOff  = types.InlineKeyboardButton(text=msg.BUTTON_OFF, callback_data=SETTINGS_OFF_CALLBACK)

# start
buttonsStart = [ types.InlineKeyboardButton(text=msg.BUTTON_COMMON,    callback_data=SETTINGS_COMMON_CALLBACK),
                 types.InlineKeyboardButton(text=msg.BUTTON_CHECKS,    callback_data=SETTINGS_CHECKS_CALLBACK),
                 types.InlineKeyboardButton(text=msg.BUTTON_STATISTIC, callback_data=SETTINGS_STATISTIC_CALLBACK)
                ]
KEYBOARD_SETTINGS_START = types.InlineKeyboardMarkup(row_width=1)
KEYBOARD_SETTINGS_START.add(*buttonsStart)
SETTINGS_START_OPTIONS = [button.callback_data for button in buttonsStart]


# keyboard for empty group
KEYBOARD_SETTINGS_EMPTY = types.InlineKeyboardMarkup(row_width=1)
KEYBOARD_SETTINGS_EMPTY.add(buttonBack)
SETTINGS_EMPTY_OPTIONS = [buttonBack.callback_data]

# common
buttonsCommon = [types.InlineKeyboardButton(text=msg.BUTTON_COMMON_PIN,            callback_data=SETTINGS_COMMON_PIN_CALLBACK),
                 types.InlineKeyboardButton(text=msg.BUTTON_COMMON_BACKUP_TIMEOUT, callback_data=SETTINGS_COMMON_BACKUP_TIMEOUT_CALLBACK)
                ]
KEYBOARD_SETTINGS_COMMON = types.InlineKeyboardMarkup(row_width=1)
KEYBOARD_SETTINGS_COMMON.add(*buttonsCommon, buttonBack)
SETTINGS_COMMON_OPTIONS = [button.callback_data for button in buttonsCommon]

buttonsPin = [buttonOn, buttonOff]
KEYBOARD_SETTINGS_COMMON_PIN = types.InlineKeyboardMarkup(row_width=2)
KEYBOARD_SETTINGS_COMMON_PIN.add(*buttonsPin, buttonBack)
SETTINGS_COMMON_PIN_OPTIONS = [button.callback_data for button in buttonsPin]

# checks
buttonsChecks = [ types.InlineKeyboardButton(text=msg.BUTTON_PRECHECK, callback_data=SETTINGS_CHECKS_PRECHECK_CALLBACK),
                  types.InlineKeyboardButton(text=msg.BUTTON_BATTLE,   callback_data=SETTINGS_CHECKS_BATTLE_CALLBACK),
                  types.InlineKeyboardButton(text=msg.BUTTON_ARSENAL,  callback_data=SETTINGS_CHECKS_ARSENAL_CALLBACK),
                  types.InlineKeyboardButton(text=msg.BUTTON_NUMBERS,  callback_data=SETTINGS_CHECKS_NUMBERS_CALLBACK),
                  types.InlineKeyboardButton(text=msg.BUTTON_CRYSTALS, callback_data=SETTINGS_CHECKS_CRYSTALS_CALLBACK),
                ]
KEYBOARD_SETTINGS_CHECKS = types.InlineKeyboardMarkup(row_width=2)
KEYBOARD_SETTINGS_CHECKS.add(*buttonsChecks, buttonBack)
SETTINGS_CHECKS_OPTIONS = [button.callback_data for button in buttonsChecks]

# checks - ars
buttonsArs = [types.InlineKeyboardButton(text=msg.BUTTON_ARSENAL_CRIT, callback_data=SETTINGS_CHECKS_ARSENAL_CRIT_THRESHOLD_CALLBACK),
              types.InlineKeyboardButton(text=msg.BUTTON_ARSENAL_PIN,  callback_data=SETTINGS_CHECKS_ARSENAL_CRIT_PIN_CALLBACK)
             ]
KEYBOARD_SETTINGS_ARS = types.InlineKeyboardMarkup(row_width=1)
KEYBOARD_SETTINGS_ARS.add(*buttonsArs, buttonBack)
SETTINGS_ARS_OPTIONS = [button.callback_data for button in buttonsArs]

# checks - crystals
buttonsCrystals = [types.InlineKeyboardButton(text=msg.BUTTON_CRYSTALS_RANGES,  callback_data=SETTINGS_CHECKS_CRYSTALS_RANGES_CALLBACK)]
KEYBOARD_SETTINGS_CRYSTALS = types.InlineKeyboardMarkup(row_width=1)
KEYBOARD_SETTINGS_CRYSTALS.add(*buttonsCrystals, buttonBack)
SETTINGS_CRYSTALS_OPTIONS = [button.callback_data for button in buttonsCrystals]

# statistics
buttonsStatistic = [ types.InlineKeyboardButton(text=msg.BUTTON_STATISTIC_BESTLIST,    callback_data=SETTINGS_STATISTIC_BESTLIST_CALLBACK),
                     types.InlineKeyboardButton(text=msg.BUTTON_STATISTIC_NOMINATIONS, callback_data=SETTINGS_STATISTIC_NOMINATIONS_CALLBACK),
                     types.InlineKeyboardButton(text=msg.BUTTON_STATISTIC_CYCLETIME,   callback_data=SETTINGS_STATISTIC_CYCLE_TIME_CALLBACK),
                    ]
KEYBOARD_SETTINGS_STATISTIC = types.InlineKeyboardMarkup(row_width=1)
KEYBOARD_SETTINGS_STATISTIC.add(*buttonsStatistic, buttonBack)
SETTINGS_STATISTIC_OPTIONS = [button.callback_data for button in buttonsStatistic]
