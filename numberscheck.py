#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#

import datetime
from icons import *

class NumbersCheck():
    check_id = None
    count = 1
    numbers = {} # {number: value (0-3)}
    users = {}   # {userid: [numbers done]}
    is_500 = False
    is_1000 = False
    times = {} # {"500": datetime, "1000": datetime}
    is_postponed = False # set when 500 or 1000 is gained

    def __init__(self, count):
        self.count = count
        self.numbers = {}
        for i in range(1, count+1):
            self.numbers[i] = 3
        self.users = {}
        self.is_500 = False
        self.is_1000 = False
        self.times = {"500": None, "1000": None}
        self.is_postponed = False

    def SetMessageID(self, message_id):
        # print("Set Numbers ID: " + str(message_id))
        self.check_id = message_id

    def GetHeader(self):
        return "⚔️ *Прогресс номеров (по скринам):*\n"

    def GetText(self):
        text = self.GetHeader()
        empty_nums = []
        # output numbers in 2 columns
        numbers_table = ""
        nonempty_nums = {}
        for number, value in self.numbers.items():
            if value > 0:
                nonempty_nums[number] = value
            else:
                empty_nums.append(number)
        
        if len(nonempty_nums) > 0:
            text += "\n"
            odd  = len(nonempty_nums) % 2
            rows = len(nonempty_nums) // 2 + odd
            counter = 1
            keys = list(nonempty_nums.keys())
            values = list(nonempty_nums.values())
            for i in range(0, rows):
                text += ("*%2d: *" % keys[i]) + "⭐️"*values[i] + "      "*(3-values[i])
                if i < rows-1: # not last row
                    text += ("* %2d: *" % keys[i+rows]) + "⭐️"*values[i+rows] + "\n"
                else:
                    if odd == 0:
                        text += ("* %2d: *" % keys[i+rows]) + "⭐️"*values[i+rows] + "\n"
                    else:
                        text += "\n"

        if len(empty_nums) > 0:
            text += "\n*Пустые: *"
            for number in empty_nums[:-1]:
                text += str(number) + ", "
            text += str(empty_nums[-1]) + "\n"

        if self.is_500 or self.is_1000:
            text += "\n*Достигнутые цели:*\n"
        if self.is_500:
            text += ("(%0.2d:%0.2d) 5️⃣0️⃣0️⃣ ❗\n" % (self.times["500"].hour, self.times["500"].minute))*self.is_500 
        if self.is_1000:
            text += ("(%0.2d:%0.2d) 1️⃣0️⃣0️⃣0️⃣ ❗\n" % (self.times["1000"].hour, self.times["1000"].minute))*self.is_1000
        return text

    def CheckUser(self, userid, value):
        ret = True
        number_to_check = int(value.replace(NUMBERS_CALLBACK_PREFIX, ""))
        oldValue = self.numbers[number_to_check]
        if oldValue == 0: # can't set number below 0
            return False
        # update number value
        self.numbers[number_to_check] = (oldValue - 1)
        # record user action
        done = False
        for user in self.users:
            if user == userid: # record exist
                oldRecord = self.users[user]
                oldRecord.append(number_to_check)
                self.users[user] = oldRecord
                done = True
        # user record is new
        if not done:
            self.users[userid] = [number_to_check]
        self.CheckAchievements()
        return True

    def CheckAchievements(self):
        is_500 = True
        is_1000 = True
        for number, value in self.numbers.items():
            if value > 0:
                is_1000 = False
            if value == 3:
                is_500 = False
            if is_500 == False and is_1000 == False:
                break # save time consume for iterating list if no condition is already met
        now = datetime.datetime.now()
        if is_500:
            self.times["500"] = now
            self.is_postponed = True
        if is_1000:
            self.times["1000"] = now
            self.is_postponed = True
        self.is_500 = is_500
        self.is_1000 = is_1000
