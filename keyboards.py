#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Keyboards used in inline check messages
#

from telebot import types
from icons import *
from callbacks import *

#
# Function that counts maximum row width for inline keyboard based on total buttons count
#
def FitButtons(total, maxwdth=5):
  if total <= maxwdth:
      return total
  else:
      new_count = maxwdth
      for i in range(2, maxwdth):
          count_try = total // i + total % i
          if count_try <= maxwdth:
              return count_try
  return -1

# keyboards
# battle check (from the battle chat)
KEYBOARD_CHECK = types.InlineKeyboardMarkup(row_width=3)
KEYBOARD_CHECK_ROLLED = types.InlineKeyboardMarkup(row_width=3)
buttonPlus     = types.InlineKeyboardButton(text=ICON_CHECK,  callback_data=CHECK_CHECK_CALLBACK)
buttonRage     = types.InlineKeyboardButton(text=ICON_RAGE,   callback_data=CHECK_RAGE_CALLBACK)
buttonFast     = types.InlineKeyboardButton(text=ICON_FAST,   callback_data=CHECK_FAST_CALLBACK)
buttonArsenal  = types.InlineKeyboardButton(text=ICON_ARS,    callback_data=CHECK_ARS_CALLBACK)
buttonThinking = types.InlineKeyboardButton(text=ICON_THINK,  callback_data=CHECK_THINK_CALLBACK)
buttonCancel   = types.InlineKeyboardButton(text=ICON_CANCEL, callback_data=CHECK_CANCEL_CALLBACK)
buttonRoll     = types.InlineKeyboardButton(text=ICON_ROLL,   callback_data=CHECK_ROLL_CALLBACK)
buttonStart    = types.InlineKeyboardButton(text=ICON_START,  callback_data=CHECK_START_CALLBACK)
buttonStop     = types.InlineKeyboardButton(text=ICON_STOP,   callback_data=CHECK_STOP_CALLBACK)
KEYBOARD_CHECK.add(buttonPlus, buttonRage, buttonFast,
                   buttonArsenal, buttonThinking, buttonCancel,
                   buttonRoll, buttonStart, buttonStop)
KEYBOARD_CHECK_ROLLED.add(buttonPlus, buttonRage, buttonFast,
                          buttonArsenal, buttonThinking, buttonCancel,
                          buttonStart, buttonStop)
# check for started battle
KEYBOARD_LATE = types.InlineKeyboardMarkup(row_width=2)
buttonLate    = types.InlineKeyboardButton(text=ICON_CHECK, callback_data=CHECK_LATE_CALLBACK)
KEYBOARD_LATE.add(buttonLate, buttonCancel, buttonStop)

CHECK_OPTIONS = [buttonPlus.callback_data,
                 buttonRage.callback_data,
                 buttonFast.callback_data,
                 buttonArsenal.callback_data,
                 buttonThinking.callback_data,
                 buttonCancel.callback_data,
                 buttonLate.callback_data,
                ]
CHECK_CONTROL_OPTIONS = [buttonRoll.callback_data,
                         buttonStart.callback_data,
                         buttonStop.callback_data,
                        ]

# battle arsenal
KEYBOARD_ARS    = types.InlineKeyboardMarkup(row_width=5)
buttonsArs      = [types.InlineKeyboardButton(text="+8", callback_data=ARS_8_CALLBACK),
                   types.InlineKeyboardButton(text="+9", callback_data=ARS_9_CALLBACK),
                   types.InlineKeyboardButton(text="+10", callback_data=ARS_10_CALLBACK),
                   types.InlineKeyboardButton(text="+11", callback_data=ARS_11_CALLBACK),
                   types.InlineKeyboardButton(text="+12", callback_data=ARS_12_CALLBACK),
                   types.InlineKeyboardButton(text="+13", callback_data=ARS_13_CALLBACK),
                   types.InlineKeyboardButton(text="+14", callback_data=ARS_14_CALLBACK),
                   types.InlineKeyboardButton(text="+24", callback_data=ARS_24_CALLBACK),
                   types.InlineKeyboardButton(text="+27", callback_data=ARS_27_CALLBACK),
                   types.InlineKeyboardButton(text="+30", callback_data=ARS_30_CALLBACK),
                   types.InlineKeyboardButton(text="+33", callback_data=ARS_33_CALLBACK),
                   types.InlineKeyboardButton(text="+36", callback_data=ARS_36_CALLBACK),
                   types.InlineKeyboardButton(text="+39", callback_data=ARS_39_CALLBACK),
                   types.InlineKeyboardButton(text="+42", callback_data=ARS_42_CALLBACK),
                   types.InlineKeyboardButton(text="+0", callback_data=ARS_0_CALLBACK),
                   types.InlineKeyboardButton(text=ICON_CANCEL, callback_data=ARS_CANCEL_CALLBACK),
                   types.InlineKeyboardButton(text=ICON_RAGE, callback_data=ARS_FULL_CALLBACK),
                   types.InlineKeyboardButton(text=ICON_STOP, callback_data=ARS_STOP_CALLBACK)
                   ]
KEYBOARD_ARS.add(*buttonsArs)

ARS_OPTIONS = [ button.callback_data for button in buttonsArs[:-1]] # do not include stop button
ARS_CONTROL_OPTIONS = [buttonsArs[-1].callback_data] # only stop button

# battle numbers
KEYBOARD_NUMBERS = types.InlineKeyboardMarkup()
buttonsNums      = [types.InlineKeyboardButton(text="1", callback_data=NUMBERS_1_CALLBACK),
                    types.InlineKeyboardButton(text="2", callback_data=NUMBERS_2_CALLBACK),
                    types.InlineKeyboardButton(text="3", callback_data=NUMBERS_3_CALLBACK),
                    types.InlineKeyboardButton(text="4", callback_data=NUMBERS_4_CALLBACK),
                    types.InlineKeyboardButton(text="5", callback_data=NUMBERS_5_CALLBACK),
                    types.InlineKeyboardButton(text="6", callback_data=NUMBERS_6_CALLBACK),
                    types.InlineKeyboardButton(text="7", callback_data=NUMBERS_7_CALLBACK),
                    types.InlineKeyboardButton(text="8", callback_data=NUMBERS_8_CALLBACK),
                    types.InlineKeyboardButton(text="9", callback_data=NUMBERS_9_CALLBACK),
                    types.InlineKeyboardButton(text="10", callback_data=NUMBERS_10_CALLBACK),
                    types.InlineKeyboardButton(text="11", callback_data=NUMBERS_11_CALLBACK),
                    types.InlineKeyboardButton(text="12", callback_data=NUMBERS_12_CALLBACK),
                    types.InlineKeyboardButton(text="13", callback_data=NUMBERS_13_CALLBACK),
                    types.InlineKeyboardButton(text="14", callback_data=NUMBERS_14_CALLBACK),
                    types.InlineKeyboardButton(text="15", callback_data=NUMBERS_15_CALLBACK),
                    types.InlineKeyboardButton(text="16", callback_data=NUMBERS_16_CALLBACK),
                    types.InlineKeyboardButton(text="17", callback_data=NUMBERS_17_CALLBACK),
                    types.InlineKeyboardButton(text="18", callback_data=NUMBERS_18_CALLBACK),
                    types.InlineKeyboardButton(text="19", callback_data=NUMBERS_19_CALLBACK),
                    types.InlineKeyboardButton(text="20", callback_data=NUMBERS_20_CALLBACK),
                    types.InlineKeyboardButton(text="21", callback_data=NUMBERS_21_CALLBACK),
                    types.InlineKeyboardButton(text="22", callback_data=NUMBERS_22_CALLBACK),
                    types.InlineKeyboardButton(text="23", callback_data=NUMBERS_23_CALLBACK),
                    types.InlineKeyboardButton(text="24", callback_data=NUMBERS_24_CALLBACK),
                    types.InlineKeyboardButton(text="25", callback_data=NUMBERS_25_CALLBACK),
                    types.InlineKeyboardButton(text="26", callback_data=NUMBERS_26_CALLBACK),
                    types.InlineKeyboardButton(text="27", callback_data=NUMBERS_27_CALLBACK),
                    types.InlineKeyboardButton(text="28", callback_data=NUMBERS_28_CALLBACK),
                    types.InlineKeyboardButton(text="29", callback_data=NUMBERS_29_CALLBACK),
                    types.InlineKeyboardButton(text="30", callback_data=NUMBERS_30_CALLBACK)
                    ]
buttonsNumsCancel = types.InlineKeyboardButton(text=ICON_CANCEL, callback_data=NUMBERS_CANCEL_CALLBACK)
buttonsNums500    = types.InlineKeyboardButton(text=ICON_500,    callback_data=NUMBERS_500_CALLBACK)
buttonsNums1000   = types.InlineKeyboardButton(text=ICON_1000,   callback_data=NUMBERS_1000_CALLBACK)
buttonsNumsStop   = types.InlineKeyboardButton(text=ICON_STOP,   callback_data=NUMBERS_STOP_CALLBACK)

def SetupNumbersKeyboard(count=30, ingame_nums=None):
    global KEYBOARD_NUMBERS
    row_size = FitButtons(total=count)
    if row_size > 0:
      KEYBOARD_NUMBERS = types.InlineKeyboardMarkup(row_width=row_size)
    else:
      return None
    if count > 0 and count <= 30:
        buttons = []
        if ingame_nums != None:
          for num in ingame_nums: # if check is for in-game numbers - add only specified number buttons
            buttons.append(buttonsNums[num-1])
        else: # else - add all buttons from 1 to counter
          for i in range(count):
              buttons.append(buttonsNums[i])
        KEYBOARD_NUMBERS.add(*buttons)
        KEYBOARD_NUMBERS.add(buttonsNumsCancel, buttonsNumsStop)
        KEYBOARD_NUMBERS.add(buttonsNums500, buttonsNums1000)
    return KEYBOARD_NUMBERS

NUMBERS_OPTIONS = [ button.callback_data for button in buttonsNums ]
NUMBERS_OPTIONS.append(buttonsNumsCancel.callback_data)
NUMBERS_CONTROL_OPTIONS = [buttonsNums500.callback_data,
                           buttonsNums1000.callback_data,
                           buttonsNumsStop.callback_data]

# battle control (from the bot chat)
KEYBOARD_START      = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2, resize_keyboard=True)
KEYBOARD_STOP       = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2, resize_keyboard=True)
buttonStartPrivate  = types.KeyboardButton(text=ICON_START+" Запустить")
buttonStopPrivate   = types.KeyboardButton(text=ICON_STOP+" Завершить")
buttonCancelPrivate = types.KeyboardButton(text=ICON_EXIT+" Отмена")
KEYBOARD_START.add(buttonStartPrivate, buttonCancelPrivate)
KEYBOARD_STOP.add(buttonStopPrivate, buttonCancelPrivate)

CHECK_CONTROL_OPTIONS_PRIVATE = [buttonStartPrivate.text, buttonStopPrivate.text, buttonCancelPrivate.text]

# war pre-check
KEYBOARD_PRECHECK = types.InlineKeyboardMarkup(row_width=3)
buttonsPrecheck   = [types.InlineKeyboardButton(text=ICON_FR, callback_data=PRECHECK_FR_CALLBACK),
                     types.InlineKeyboardButton(text=ICON_SAT, callback_data=PRECHECK_SAT_CALLBACK),
                     types.InlineKeyboardButton(text=ICON_SUN, callback_data=PRECHECK_SUN_CALLBACK),
                     types.InlineKeyboardButton(text=ICON_CHECK, callback_data=PRECHECK_FULL_CALLBACK),
                     types.InlineKeyboardButton(text=ICON_THINK, callback_data=PRECHECK_THINK_CALLBACK),
                     types.InlineKeyboardButton(text=ICON_CANCEL, callback_data=PRECHECK_CANCEL_CALLBACK),
                     types.InlineKeyboardButton(text=ICON_STOP, callback_data=PRECHECK_STOP_CALLBACK)
                    ]
KEYBOARD_PRECHECK.add(*buttonsPrecheck)

PRECHECK_OPTIONS = [button.callback_data for button in buttonsPrecheck[:-1]] # do not include stop button
PRECHECK_CONTROL_OPTIONS = [buttonsPrecheck[-1].callback_data] # only stop button

# crystals check
KEYBOARD_CRYSTALS = types.InlineKeyboardMarkup()
buttonsCrysStop   = types.InlineKeyboardButton(text=ICON_STOP, callback_data=CRYSTALS_STOP_CALLBACK)

CRYSTALS_OPTIONS = []
CRYSTALS_CONTROL_OPTIONS = [buttonsCrysStop.callback_data]

def SetupCrystalsKeyboard(maxvalue=3000, step=500):
  global KEYBOARD_CRYSTALS
  global CRYSTALS_OPTIONS
  width = 1
  if maxvalue < 10000:
    width = 2
  if maxvalue < 1000:
    width = 3
  KEYBOARD_CRYSTALS = types.InlineKeyboardMarkup(row_width=width)
  value = (0, step)
  buttonsCrystals = []
  while value[1] <= maxvalue:
    suffixText = "%d-%d" % value
    buttonText = ICON_CRYSTAL + " " + suffixText
    buttonCb   = CRYSTALS_CALLBACK_PREFIX + suffixText
    buttonsCrystals.append(types.InlineKeyboardButton(text=buttonText, callback_data=buttonCb))
    CRYSTALS_OPTIONS.append(buttonCb)
    value = (value[1]+1, value[1]+step)
  if maxvalue % step:
    value = (value[0], maxvalue)
    suffixText = "%d-%d" % value
    buttonText = ICON_CRYSTAL + " " + suffixText
    buttonCb   = CRYSTALS_CALLBACK_PREFIX + suffixText
    buttonsCrystals.append(types.InlineKeyboardButton(text=buttonText, callback_data=buttonCb))
    CRYSTALS_OPTIONS.append(buttonCb)
  KEYBOARD_CRYSTALS.add(*buttonsCrystals)
  KEYBOARD_CRYSTALS.add(buttonsCrysStop)

PRECHECK_OPTIONS = [button.callback_data for button in buttonsPrecheck[:-1]] # do not include stop button
PRECHECK_CONTROL_OPTIONS = [buttonsPrecheck[-1].callback_data] # only stop button

# reset bot keyboard (from the bot chat)
KEYBOARD_RESET      = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2, resize_keyboard=True)
buttonReset         = types.KeyboardButton(text=ICON_START+" Сброс")
KEYBOARD_RESET.add(buttonReset, buttonCancelPrivate)

RESET_CONTROL_OPTIONS = [buttonReset.text, buttonCancelPrivate.text]

KEYBOARD_SNOWWHITE = types.InlineKeyboardMarkup(row_width=1)
buttonPraise       = types.InlineKeyboardButton(text=ICON_PRAISE+" Привет!", callback_data=SNOW_PRAISE_CALLBACK)
KEYBOARD_SNOWWHITE.add(buttonPraise)
