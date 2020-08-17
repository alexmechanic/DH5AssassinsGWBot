#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class and methods representing numbers check
#

import datetime
from logger import get_logger
from telebot import types

import common
from common import bot
from icons import *
from statistics import User, Score
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
    user = User(call.from_user.id, call.from_user.first_name, call.from_user.username)
    log.debug("%s is trying to vote for numbers (%s)" % (user, call.data.replace(cb.NUMBERS_CALLBACK_PREFIX, "")))
    if common.current_numcheck and message_id == common.current_numcheck.check_id:
        is_guide_training = False
        battle_object = common.current_numcheck
    elif user._id in common.user_guiding.keys(): # guide battle example workaround
        is_guide_training = True
        if common.user_guiding[user._id].IsTrainingStage(): # using check is allowed only at several steps of guide
            battle_object = common.user_guiding[user._id].demonstration
        else:
            log.error("Not at training stage, aborting")
            bot.answer_callback_query(call.id, "На данный момент использование чека недоступно")
            return
    else:
        battle_object = None
    if battle_object:
        if battle_object.CheckUser(user, call.data):
            if not battle_object.Is1000(): # if reached 1000 - no need to continue numbers check
                reply = kb.KEYBOARD_NUMBERS
            else:
                battle_object.DoEndCheck()
                reply = None
            if is_guide_training:
                bot.edit_message_text(battle_object.GetText(), user._id, battle_object.check_id,
                                      parse_mode="markdown", reply_markup=reply)
            else:
                bot.edit_message_text(battle_object.GetText(), inline_message_id=message_id, 
                                      parse_mode="markdown", reply_markup=reply)
                battle_object.CheckNotifyIfAchieved(user)
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
    message_id = call.inline_message_id
    user = User(call.from_user.id, call.from_user.first_name, call.from_user.username)
    log.debug("%s is trying to control numbers check" % user)
    if not hlp.IsUserAdmin(user):
        bot.answer_callback_query(call.id, "Только офицеры могут управлять чеком номеров!")
        log.error("Failed (not an admin)")
        return
    userChoice = call.data
    if common.current_numcheck and message_id == common.current_numcheck.check_id:
        if userChoice == kb.NUMBERS_CONTROL_OPTIONS[0]: # make 500
            common.current_numcheck.Do500()
            bot.edit_message_text(common.current_numcheck.GetText(),
                                  inline_message_id=common.current_numcheck.check_id,
                                  parse_mode="markdown", reply_markup=kb.KEYBOARD_NUMBERS)
            common.current_numcheck.CheckNotifyIfAchieved(user)
            bot.answer_callback_query(call.id, "Отмечено "+ICON_500)
            return
        elif userChoice == kb.NUMBERS_CONTROL_OPTIONS[1]: # make 1000
            common.current_numcheck.Do1000()
            bot.edit_message_text(common.current_numcheck.GetText(),
                                  inline_message_id=common.current_numcheck.check_id,
                                  parse_mode="markdown")
            common.current_numcheck.CheckNotifyIfAchieved(user)
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
    user = User(q.from_user.id, q.from_user.first_name, q.from_user.username)
    log.debug("%s is trying to create numbers check" % user)
    if not hlp.IsUserAdmin(user): # non-admins cannot post votes
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
                                                 input_message_content=types.InputTextMessageContent(ICON_NUMBERS+" *Прогресс номеров*", parse_mode="markdown"),
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
    users = {}   # {User: [numbers done]}
    _500 = {
        "done": False,
        "notified": False,
        "time": None
        }
    _1000 = {
        "done": False,
        "notified": False,
        "time": None
        }
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
        self._500 = {
            "done": False,
            "notified": False,
            "time": None
            }
        self._1000 = {
            "done": False,
            "notified": False,
            "time": None
            }
        self.is_postponed = False
        log.info("New numbers check created (%d)" % count)

    def SetMessageID(self, message_id):
        self.check_id = message_id
        log.debug("Set inline message_id: %s" % self.check_id)

    def DoEndCheck(self):
        self.is_postponed = True
        common.statistics.Update(self.CollectStatistic())
        log.info("Numbers check stopped")

    def CollectStatistic(self):
        statistic = {}
        for k, v in self.users.items():
            statistic[k] = Score(stars=len(v))
        return statistic

    def Is500(self):
        return self._500["done"]

    def Do500(self):
        if self._500["done"]:
            return
        for number, value in self.numbers.items():
            if value == 3:
                self.numbers[number] = value - 1
        self._500["time"] = datetime.datetime.now()
        self._500["done"] = True

    def Is1000(self):
        return self._1000["done"]

    def Do1000(self):
        if self._1000["done"]:
            return
        now = datetime.datetime.now()
        for number in self.numbers:
            self.numbers[number] = 0
        if not self._500["done"]:
            self._500["done"] = True
            self._500["time"] = now
        self._1000["done"] = True
        self._1000["time"] = now
        self.DoEndCheck()

    def CheckNotifyIfAchieved(self, user):
        text = None
        if self._1000["done"] and not self._1000["notified"]:
            text = "%s ❗" % ICON_1000
            self._1000["notified"] = True
        elif self._500["done"] and not self._500["notified"]:
            text = "%s ❗" % ICON_500
            self._500["notified"] = True
        if text:
            common.bot.send_message(common.warchat_id, text)

    def GetHeader(self):
        return ICON_NUMBERS+" *Прогресс номеров:*\n"

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
                text += ("`%2d: `" % keys[i]) + ICON_STAR*values[i] + " `  `"*(3-values[i])
                if i < rows-1: # not last row
                    text += ("` %2d: `" % keys[i+rows]) + ICON_STAR*values[i+rows] + "\n"
                else:
                    if odd == 0:
                        text += ("` %2d: `" % keys[i+rows]) + ICON_STAR*values[i+rows] + "\n"
                    else:
                        text += "\n"

        if len(empty_nums) > 0:
            text += "\n*Пустые: *"
            for number in empty_nums[:-1]:
                text += str(number) + ", "
            text += str(empty_nums[-1]) + "\n"

        if not self._500["done"]:
            text += ("\nДо %s:       %d " % (ICON_500, stars_left[0])) + ICON_STAR + "\n"
        if not self._1000["done"]:
            text += "\n"*self._500["done"] + ("До %s: %d " % (ICON_1000, stars_left[1])) + ICON_STAR + "\n"

        if self._500["done"] or self._1000["done"]:
            text += "\n*Достигнутые цели:*\n"
        if self._500["done"]:
            text += "(%0.2d:%0.2d) %s ❗\n" % (self._500["time"].hour, self._500["time"].minute, ICON_500)
        if self._1000["done"]:
            text += "(%0.2d:%0.2d) %s ❗\n" % (self._1000["time"].hour, self._1000["time"].minute, ICON_1000)
        return text

    def CheckUser(self, user, value):
        ret = True
        try:
            number_to_check = int(value.replace(cb.NUMBERS_CALLBACK_PREFIX, ""))
        except: # user hit Cancel
            return self.UncheckUser(user) 
        log.info("%s voted for %d" % (user, number_to_check))
        oldValue = self.numbers[number_to_check]
        if oldValue == 0: # can't set number below 0
            log.error("Vote failed - number is already empty")
            return False
        # update number value
        self.numbers[number_to_check] = (oldValue - 1)
        # record user action
        done = False
        for _user in self.users:
            if _user == user: # record exist
                oldRecord = self.users[user]
                oldRecord.append(number_to_check)
                self.users[user] = oldRecord
                done = True
                break
        # user record is new
        if not done:
            self.users[user] = [number_to_check]
            user.GetString(with_link=False),
            number_to_check,
            ICON_STAR*oldValue,
            ICON_STAR*(oldValue-1) if oldValue-1 > 0 else "пустой")
            )
        self.CheckAchievements()
        log.info("Vote successful")
        return True

    # undo last number result for user if user made mistake
    def UncheckUser(self, user):
        log.debug("%s reverting his last vote" % user)
        lastNumber = None
        modified = False
        # obtain user impact
        for _user in self.users:
            if _user == user: # record exist
                lastNumber = self.users[user][-1]
                modified = True
                # revert last number record
                self.users[user] = self.users[user][:-1]
                # restore star
                self.numbers[lastNumber] = self.numbers[lastNumber] + 1
                if self.users[user] == []: # if record is empty now - delete record
                    del self.users[user]
                break
        if modified:
            log.info("Revert successful")
        else:
            log.info("Revert failed - user record not found")
        return modified

    def CheckAchievements(self):
        is_500 = True
        is_1000 = True
        for number, value in self.numbers.items():
            if value > 0:
                is_1000 = False
            if value == 3:
                is_500 = False
            if not is_500 and not is_1000:
                break # save time consume for iterating list if no condition is already met
        now = datetime.datetime.now()
        if is_500:
            if not self._500["time"]:
                self._500["time"] = now
            self.is_postponed = True
            if not self._500["done"]:
                log.debug("Reached 500")
                log.debug("Users impact:")
                log.debug(' '.join('{}: {}'.format(user, count) for user, count in self.users.items()))
        if is_1000:
            if not self._1000["time"]:
                self._1000["time"] = now
            self.is_postponed = True
            if not self._1000["done"]:
                log.debug("Reached 1000")
                log.debug("Users impact:")
                log.debug(' '.join('{}: {}'.format(user, count) for user, count in self.users.items()))
        self._500["done"] = is_500
        self._1000["done"] = is_1000
