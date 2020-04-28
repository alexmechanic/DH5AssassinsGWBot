#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class representing numbers check
#

import datetime
from logger import get_logger
from telebot import types

import common
from common import bot
from icons import *
from commands import COMMANDS
import keyboards as kb
import callbacks as cb
import helpers as hlp

log = get_logger("bot." + __name__)

#
# Numbers progress
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.NUMBERS_OPTIONS)
def numbers_check_user(call):
    # print("numbers_check_user")
    # print(call)
    message_id = call.inline_message_id
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    log.debug("User %d (%s %s) is trying to vote for numbers (%s)" % (*user, call.data.replace(cb.NUMBERS_CALLBACK_PREFIX, "")))
    if common.current_numcheck:
        if message_id == common.current_numcheck.check_id:
            ret = common.current_numcheck.CheckUser(user, call.data)
            if (ret):
                if not common.current_numcheck.is_1000: # if reached 1000 - no need to continue numbers check
                    bot.edit_message_text(common.current_numcheck.GetText(), inline_message_id=message_id, 
                                        parse_mode="markdown", reply_markup=kb.KEYBOARD_NUMBERS)
                    common.current_numcheck.CheckNotifyIfAchieved()
                else:
                    common.current_numcheck.DoEndCheck()
                    bot.edit_message_text(common.current_numcheck.GetText(), inline_message_id=message_id, 
                                        parse_mode="markdown")
                    common.current_numcheck.CheckNotifyIfAchieved()
            bot.answer_callback_query(call.id)
            return
    log.error("Numbers check not found!")
    bot.answer_callback_query(call.id, "Неверный чек номеров! Пожалуйста, создайте новый")

#
# Numbers check control
# (war chat keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.NUMBERS_CONTROL_OPTIONS)
def numbers_control(call):
    # print("numbers_control")
    # print(call)
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    log.debug("User %d (%s %s) is trying to control numbers check" % (*user,))
    if not hlp.IsUserAdmin(call):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять чеком номеров!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    if common.current_numcheck:
        if userChoice == kb.NUMBERS_CONTROL_OPTIONS[0]: # make 500
            common.current_numcheck.Do500()
            bot.edit_message_text(common.current_numcheck.GetText(),
                                  inline_message_id=common.current_numcheck.check_id,
                                  parse_mode="markdown", reply_markup=kb.KEYBOARD_NUMBERS)
            common.current_numcheck.CheckNotifyIfAchieved()
            bot.answer_callback_query(call.id, "Отмечено "+ICON_500)
            return
        elif userChoice == kb.NUMBERS_CONTROL_OPTIONS[1]: # make 1000
            common.current_numcheck.Do1000()
            bot.edit_message_text(common.current_numcheck.GetText(),
                                  inline_message_id=common.current_numcheck.check_id,
                                  parse_mode="markdown")
            common.current_numcheck.CheckNotifyIfAchieved()
            bot.answer_callback_query(call.id, "Отмечено "+ICON_1000)
            return
        elif userChoice == kb.NUMBERS_CONTROL_OPTIONS[2]: # stop
            common.current_numcheck.DoEndCheck()
            bot.edit_message_text(common.current_numcheck.GetText(),
                                  inline_message_id=common.current_numcheck.check_id,
                                  parse_mode="markdown")
            bot.answer_callback_query(call.id, "🏁 Чек номеров завершен")
            return
        else:
            log.error("invalid action!")
            bot.answer_callback_query(call.id, "Неверныая команда! Пожалуйста, обратитесь к администратору бота")
    log.error("Numbers check not found!")
    bot.answer_callback_query(call.id, "Неверный чек номеров! Пожалуйста, создайте новый")

#
# Numbers check creation
# (war chat inline query)
#
@bot.inline_handler(lambda query: query.query[:len(COMMANDS["numbers"])] == COMMANDS["numbers"])
def numbers_query_inline(q):
    # print("numbers_query_inline")
    # print(q)
    user = [q.from_user.id, q.from_user.username, q.from_user.first_name]
    log.debug("User %d (%s %s) is trying to create numbers check" % (*user,))
    if not hlp.IsUserAdmin(q): # non-admins cannot post votes
        log.error("Failed (not an admin)")
        hlp.SendHelpNonAdmin(q)
        bot.answer_callback_query(q.id)
        return
    if hlp.CanStartNewBattle():
        log.error("Trying to setup numbers check with no current battle")
        error_text = "Отсутствует активный бой"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_battle")
        return
    res, numbers = hlp.IsNumbersQuery(q)
    if res:
        if hlp.CanStartNewNumbers():
            text = 'Добавить прогресс номеров'
            if len(numbers) == 1:
                text2 = 'по скринам (%s)' % numbers[0]
                kb.SetupNumbersKeyboard(count=int(numbers[0]))
            else:
                text2 = 'по игре (%s)' % ' '.join(str(num) for num in numbers)
                kb.SetupNumbersKeyboard(ingame_nums=numbers)
            res = types.InlineQueryResultArticle('numbers',
                                                 title=text,
                                                 description=text2,
                                                 input_message_content=types.InputTextMessageContent("NUMBERS PLACEHOLDER", parse_mode="markdown"),
                                                 thumb_url="https://i.ibb.co/JRRMLjv/numbers.png",
                                                 reply_markup=kb.KEYBOARD_NUMBERS
                                                 )
            bot.answer_inline_query(q.id, [res], is_personal=True, cache_time=2)
        elif not hlp.CanStartNewNumbers():
            log.error("Trying to setup another numbers check while current has not reached 500/1000")
            error_text = "Уже имеется активный чек номеров"
            bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                    switch_pm_text=error_text, switch_pm_parameter="existing_numbers")
    else:
        log.error("Failed (invalid query)")
        error_text = "Неверный формат запроса"
        bot.answer_inline_query(q.id, [], is_personal=True, cache_time=2,
                                switch_pm_text=error_text, switch_pm_parameter="existing_numbers")


class NumbersCheck():
    check_id = None
    count = 1
    ingame = False
    numbers = {} # {number: value (0-3)}
    users = {}   # {userid: [numbers done]}
    is_500 = False
    is_1000 = False
    times = {} # {"500": datetime, "1000": datetime}
    is_postponed = False # set when 500 or 1000 is gained

    def __init__(self, count=30, ingame=False, ingame_nums=None):
        self.numbers = {}
        self.ingame = ingame
        if ingame:
            self.count = len(ingame_nums)
            for i in ingame_nums:
                self.numbers[i] = 3
        else:
            self.count = count
            for i in range(1, count+1):
                self.numbers[i] = 3
        self.users = {}
        self.is_500 = False
        self.is_1000 = False
        self.times = {"500": None, "1000": None}
        self.is_postponed = False
        log.info("New numbers check created (%d)" % count)

    def SetMessageID(self, message_id):
        self.check_id = message_id
        log.debug("Set inline message_id: %s" % self.check_id)

    def DoEndCheck(self):
        self.is_postponed = True
        log.info("Numbers check stopped")

    def Do500(self):
        if self.is_500:
            return
        for number, value in self.numbers.items():
            if value == 3:
                self.numbers[number] = value - 1
        self.times["500"] = datetime.datetime.now()
        self.is_500 = True

    def Do1000(self):
        if self.is_1000:
            return
        now = datetime.datetime.now()
        for number in self.numbers:
            self.numbers[number] = 0
        self.times["500"] = now
        self.times["1000"] = now
        self.is_500 = True
        self.is_1000 = True
        self.DoEndCheck()

    def CheckNotifyIfAchieved(self):
        if self.is_1000:
            common.bot.send_message(common.warchat_id, "%s ❗" % ICON_1000)
        elif self.is_500:
            common.bot.send_message(common.warchat_id, "%s ❗" % ICON_500)

    def GetHeader(self):
        return ICON_SWORDS+" *Прогресс номеров " + \
                "(по скринам)"*(not self.ingame) + "(по игре)"*(self.ingame) + ":*\n"

    def GetText(self):
        text = self.GetHeader()
        empty_nums = []
        # output numbers in 2 columns
        numbers_table = ""
        nonempty_nums = {}
        stars_left = [0, 0]
        for number, value in self.numbers.items():
            if value > 0:
                nonempty_nums[number] = value
                stars_left[1] += value
                if value == 3:
                    stars_left[0] += 1
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
                text += ("*%2d: *" % keys[i]) + ICON_STAR*values[i] + "      "*(3-values[i])
                if i < rows-1: # not last row
                    text += ("* %2d: *" % keys[i+rows]) + ICON_STAR*values[i+rows] + "\n"
                else:
                    if odd == 0:
                        text += ("* %2d: *" % keys[i+rows]) + ICON_STAR*values[i+rows] + "\n"
                    else:
                        text += "\n"

        if len(empty_nums) > 0:
            text += "\n*Пустые: *"
            for number in empty_nums[:-1]:
                text += str(number) + ", "
            text += str(empty_nums[-1]) + "\n"

        if not self.is_500:
            text += ("\nДо %s:       %d " % (ICON_500, stars_left[0])) + ICON_STAR + "\n"
        if not self.is_1000:
            text += "\n"*self.is_500 + ("До %s: %d " % (ICON_1000, stars_left[1])) + ICON_STAR + "\n"

        if self.is_500 or self.is_1000:
            text += "\n*Достигнутые цели:*\n"
        if self.is_500:
            text += ("(%0.2d:%0.2d) %s ❗\n" % (self.times["500"].hour, self.times["500"].minute, ICON_500))*self.is_500 
        if self.is_1000:
            text += ("(%0.2d:%0.2d) %s ❗\n" % (self.times["1000"].hour, self.times["1000"].minute, ICON_1000))*self.is_1000
        return text

    def CheckUser(self, user, value):
        ret = True
        userid = user[0]
        try:
            number_to_check = int(value.replace(cb.NUMBERS_CALLBACK_PREFIX, ""))
        except: # user hit Cancel
            return self.UncheckUser(user) 
        log.info("User %d (%s %s) voted for %d" % (*user, number_to_check))
        oldValue = self.numbers[number_to_check]
        if oldValue == 0: # can't set number below 0
            log.error("Vote failed - number is already empty")
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
        log.info("Vote successful")
        return True

    # undo numbers result for user if user made mistake
    def UncheckUser(self, user):
        log.debug("User %d (%s %s) reverting all his votes" % (user[0], user[1], user[2]))
        userNumbers = []
        userid = user[0]
        modified = False
        # obtain user impact
        for user in self.users:
            if user == userid: # record exist
                userNumbers = self.users[user]
                modified = True
                del self.users[user]
                break
        # revoke numbers hit
        for number in userNumbers:
            self.numbers[number] = self.numbers[number] + 1
        log.info("Revert successful")
        return modified

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
            if not self.is_500:
                log.debug("Reached 500")
                log.debug("Users impact:")
                log.debug(' '.join('{}: {}'.format(*user) for user in self.users.items()))
        if is_1000:
            self.times["1000"] = now
            self.is_postponed = True
            if not self.is_1000:
                log.debug("Reached 1000")
                log.debug("Users impact:")
                log.debug(' '.join('{}: {}'.format(*user) for user in self.users.items()))
        self.is_500 = is_500
        self.is_1000 = is_1000
