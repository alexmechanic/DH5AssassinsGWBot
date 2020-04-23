#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Various support functions
#

import re
from collections import Counter
from commands import COMMANDS

def IsCheckTimeQuery(query): # return if query contains check time and check time list
    times = re.findall(r'(?:\d|[01]\d|2[0-3])\D[0-5]\d', query.query)
    if times != [] and len(times) == 2:
        return True, times
    return False, None

def IsNumbersQuery(query): # return if query contains numbers check and the list of numbers
    res = re.findall(r'номера ', query.query)
    if res != [] and len(res) == 1:
        numbers_list = query.query.replace(COMMANDS["numbers"] + " ", "")
        numbers_all = re.findall(r'\b(\d?\d)\b', numbers_list)
        numbers_correct = re.findall(r'\b([1-9]|[1-2]\d|[3][0])\b', numbers_list)
        if len(numbers_all) != len(numbers_correct):
            return False, None
        else:
            duplicates = [k for k, v in Counter(numbers_correct).items() if v > 1]
            if len(duplicates) > 0: # check for more than 1 repeats of same number
                return False, None
            else:
                return True, [int(num) for num in numbers_correct]
    else:
        return False, None

def SendHelpNoBattle(chat_id, bot):
    error_text =  "Текущий активный бой отсутствует.\n"
    error_text += "Начните новый бой, упомянув меня в военном чате и задав время чека/боя.\n"
    error_text += "*Пример*: @assassinsgwbot 13:40 14:00"
    bot.send_message(chat_id, error_text, parse_mode="markdown")
