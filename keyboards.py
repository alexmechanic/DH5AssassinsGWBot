#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
#

from telebot import types

# keyboards
# check
KEYBOARD_CHECK = types.InlineKeyboardMarkup(row_width=3)
buttonPlus = types.InlineKeyboardButton(text="✅", callback_data="✅")
buttonRage = types.InlineKeyboardButton(text="🔥", callback_data="🔥")
buttonArsenal = types.InlineKeyboardButton(text="📦", callback_data="📦")
buttonCancel = types.InlineKeyboardButton(text="❌", callback_data="❌")
buttonThinking = types.InlineKeyboardButton(text="💤", callback_data="💤")
KEYBOARD_CHECK.add(buttonPlus, buttonRage, buttonArsenal, buttonThinking, buttonCancel)

KEYBOARD_LATE = types.InlineKeyboardMarkup(row_width=1)
buttonLate = types.InlineKeyboardButton(text="⏰", callback_data="⏰")
KEYBOARD_LATE.add(buttonLate)

# battle control
KEYBOARD_START = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
KEYBOARD_STOP = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
buttonStart = types.KeyboardButton(text="▶️ Запустить")
buttonStop = types.KeyboardButton(text="⏹ Завершить")
buttonCancel = types.KeyboardButton(text="#️⃣ Отмена")
KEYBOARD_START.add(buttonStart, buttonCancel)
KEYBOARD_STOP.add(buttonStop, buttonCancel)
