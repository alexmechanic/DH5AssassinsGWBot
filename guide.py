#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class and methods representing /guide command
#

import datetime, re
from logger import get_logger
from telebot import types

import common
from common import bot
from common import user_guiding
from icons import *
from checks.battle import *
from checks.arsenal import *
from checks.numberscheck import *
from statistics import *
from commands import COMMANDS
import keyboards as kb
import callbacks as cb
import helpers as hlp

log = get_logger("bot." + __name__)

#
# Guide step call
# (guide keyboard action)
#
@bot.callback_query_handler(func=lambda call: call.data in kb.GUIDE_OPTIONS)
def guide_step(call):
    # print("guide_step")
    # print(call)
    message_id = call.inline_message_id
    user = [call.from_user.id, call.from_user.username, call.from_user.first_name]
    userChoice = call.data
    log.debug("User %d (%s %s) is trying step next for his guide" % (*user,))
    if user[0] not in user_guiding.keys():
        bot.send_message(user[0], "Бот был перезапущен.\nПожалуйста, начните обучение заного, используя команду /guide.")
        log.error("Bot has been restarted, need to start over")
        return
    if call.data == kb.GUIDE_OPTIONS[-1]: # finish
        bot.delete_message(user[0], user_guiding[user[0]].message_id)
        del user_guiding[user[0]]
        log.debug("Guide finish successful")
    else:
        user_guiding[user[0]].StepNext()
        log.debug("Guide next step")

#
# Guide help command
# (private bot chat)
#
@bot.message_handler(commands=['guide'])
def command_guide(m):
    global user_guiding
    # print("command_guide")
    # print(m)
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to start a guide" % (*user,))
    if not hlp.IsInPrivateChat(m):
        bot.delete_message(m.chat.id, m.message_id)
        hlp.SendHelpWrongChat(user[0], "/guide", "начать обучение", True)
        return
    if user[0] not in user_guiding.keys():
        user_guiding[user[0]] = Guide(User(user[0], user[2], user[1]))
        user_guiding[user[0]].Start()
        log.debug("Successful start")
    else:
        # FIX: can we repeat last guide message or need to start over? (test sample check message repeating)
        user_guiding[user[0]].StepNext(repeat=True)
        log.debug("Already started, repeating last step")
        # bot.send_message(m.from_user.id, "Вы уже начинали обучение раньше.\nПожалуйста, найдите выше последнее обучающее сообщение, и воспользуйтесь кнопкой под ним.")



class Guide():
    userid = None
    step = 0
    message_id = None
    demonstration = None
    guideline = {
        0:  "Приветствую! Это обучение поможет освоить использование военного бота.\n" + \
            "Для старта нажмите кнопку **\"Начать\"**.",
        1:  "Первая функция бота - чек перед боем. Общий вид чека показан выше.\n" + \
            "Чек создается офицером для созыва на будущий бой.",
        2:  "Для участия в бою необходимо отметиться одной из кнопок.\n\n" + \
            "*Назначение кнопок:*\n" + \
            ICON_CHECK +" - полное участие (арсенал/номера)\n" + \
            ICON_RAGE  +" - участие во время ярости (если планируется)\n" + \
            ICON_FAST  +" - быстрый 'слив' энергии (мало времени)\n" + \
            ICON_ARS   +" - только набег на арсенал (мало времени)\n" + \
            ICON_THINK +" - нет уверенности в участии\n" + \
            ICON_CANCEL+" - передумали/не сможете участвовать\n" + \
            ICON_LATE  +" - опоздали (активна после начала боя).\n\n" + \
            "Повторный выбор любой кнопки добавляет +1 (Ваших твинков) к Вашему чеку.\n" + \
            "_Кнопки управления могут использовать только офицеры._",
        3:  "Попробуйте использовать данный чек для тренировки.\n" + \
            "Когда будете готовы продолжить, нажмите **\"Далее\"**",
        4:  "Следующая функция - чек арсенала. Общий вид чека показан выше.\n" + \
            "Чек создается офицером для указания атаковать арсенал, он же указывает время ярости.\n",
        5:  "После атаки арсенала в игре необходимо запомнить, сколько ящиков Вами было _получено_, и отметить значение соответствующей кнопкой в чеке.\n" + \
            "Вклад каждого члена гильдии показывается под шкалой арсенала.\n" + \
            "_Кнопки управления могут использовать только офицеры._",
        6:  "При достижении в общей сумме 120 и более ящиков, будет создано оповещение о ярости.",
        7:  "Попробуйте использовать данный чек для тренировки.\n" + \
            "Когда будете готовы продолжить, нажмите **\"Далее\"**.",
        8:  "Следующая функция - чек номеров. Общий вид чека показан выше.\n" + \
            "Чек создается офицером в соответствии с текущим боем в игре.\n",
        9:  "Изначально каждый номер \"закрыт\", т.е. имеет по 3 звезды.\n" + \
            "Нажатие кнопки с номером снимает с него одну звезду (в примере снята звезда с номера *5*).\n" + \
            "После атаки номера в игре, каждый участник отмечает их в данном чеке.\n" + \
            "_Кнопки управления могут использовать только офицеры._",
        10: "Если снимается последняя звезда, номер переходит в группу \"пустые\"",
        11: "Если с каждого номера была снята хотя бы одна звезда, появляется отметка "+ICON_500+" с оповещением.\n" + \
            "Если все номера оказываются пустыми, появляется отметка "+ICON_1000+" с оповещением.",
        12: "Попробуйте использовать данный чек для тренировки.\n" + \
            "Когда будете готовы продолжить, нажмите **\"Далее\"**.",
        13: ICON_PRAISE+" *Поздравляем! Вы прошли краткое обучение военному боту.*\n" + \
            "Данный бот имеет и другие функции, при возникновении вопросов по их использованию обратитесь к офицеру.\n" + \
            "Для завершения обучения нажмите, пожалуйста, кнопку **\"Завершить\"**."
    }

    def __init__(self, user):
        self.userid = user._id
        self.step = 0
        self.message_id = None
        self.demonstration = None
        log.info("New guide started by user %s" % user)

    def IsTrainingStage(self):
        if self.step in [3, 7, 12]:
            return True
        return False

    def Start(self):
        msg = bot.send_message(self.userid, self.guideline[self.step],
                               parse_mode="markdown", reply_markup=kb.KEYBOARD_GUIDE_START).wait()
        self.message_id = msg.message_id

    def StepNext(self, repeat=False):
        if not repeat:
            self.step += 1
        if self.step in [1, 4, 8]: # check start, need to re-send message to bring it bottom
            bot.delete_message(self.userid, self.message_id).wait()
        self.DemonstrateStep()
        if self.step != 13:
            reply = kb.KEYBOARD_GUIDE_NEXT
        else:
            reply = kb.KEYBOARD_GUIDE_FINISH
        if self.step in [1, 4, 8]: # check start, need to re-send message to bring it bottom
            msg = bot.send_message(self.userid, self.guideline[self.step],
                                   parse_mode="markdown", reply_markup=reply).wait()
            self.message_id = msg.message_id
        else:
            bot.edit_message_text(self.guideline[self.step], self.userid, self.message_id,
                                  parse_mode="markdown", reply_markup=reply)

    def StepFinish(self):
        bot.delete_message(self.userid, self.message_id)

    def DemonstrateStep(self):
        # sample users
        sampleUser1 = [582244665, None, "Nagibator9000"]
        sampleUser2 = [187678932, "Alex", "alex_mech"]
        if self.step in [1, 4, 8]: # check start
            if self.demonstration:
                # FIX: do we need this?
                # if isinstance(self.demonstration, Battle):
                #     self.demonstration.DoEndBattle()
                # elif isinstance(self.demonstration, Arsenal):
                #     self.demonstration.DoEndArsenal()
                # else:
                #     self.demonstration.DoEndCheck()
                bot.delete_message(self.userid, self.demonstration.check_id)
                del self.demonstration
            if self.step == 1: # battle check
                self.demonstration = Battle("09 15")
                self.demonstration.CheckUser(sampleUser1, cb.CHECK_CHECK_CALLBACK)
                reply = kb.KEYBOARD_CHECK
            elif self.step == 4: # arsenal check
                self.demonstration = Arsenal("09 15")
                reply = kb.KEYBOARD_ARS
            elif self.step == 8: # numbers check
                self.demonstration = NumbersCheck(9)
                kb.SetupNumbersKeyboard(count=9)
                reply = kb.KEYBOARD_NUMBERS
            msg = bot.send_message(self.userid, self.demonstration.GetText(),
                                   parse_mode="markdown", reply_markup=reply).wait()
            self.demonstration.SetMessageID(msg.message_id)
        elif self.step in [3, 7, 12]: # last check example step
            # undo all example changes in checks to let user try him/herself
            if isinstance(self.demonstration, Battle):
                # do not undo battle checks, let them be examples
                reply = kb.KEYBOARD_CHECK
            elif isinstance(self.demonstration, Arsenal):
                self.demonstration.Increment(sampleUser1, cb.ARS_CANCEL_CALLBACK)
                self.demonstration.Increment(sampleUser2, cb.ARS_CANCEL_CALLBACK)
                reply = kb.KEYBOARD_ARS
            else:
                # no need to undo numbers check, even thouh we cannot undo 500 (yet?)
                reply = kb.KEYBOARD_NUMBERS
                pass
            bot.edit_message_text(self.demonstration.GetText(), self.userid, self.demonstration.check_id, 
                                  parse_mode="markdown", reply_markup=reply)
        elif self.step == 2: # battle check [buttons example]
            self.demonstration.CheckUser(sampleUser2, cb.CHECK_ARS_CALLBACK)
            self.demonstration.CheckUser(sampleUser2, cb.CHECK_ARS_CALLBACK)
            bot.edit_message_text(self.demonstration.GetText(), self.userid, self.demonstration.check_id, 
                                  parse_mode="markdown", reply_markup=kb.KEYBOARD_CHECK)
        elif self.step in [5, 6, 9, 10, 11]:
            if self.step == 5: # arsenal check [buttons example]
                self.demonstration.Increment(sampleUser1, cb.ARS_36_CALLBACK, notify=False)
                reply = kb.KEYBOARD_ARS
            elif self.step == 6: # arsenal check [rage example]
                self.demonstration.Increment(sampleUser2, cb.ARS_FULL_CALLBACK, notify=False)
                reply = kb.KEYBOARD_ARS
            elif self.step == 9: # numbers check [buttons example]
                self.demonstration.CheckUser(sampleUser1, cb.NUMBERS_5_CALLBACK)
                reply = self.demonstration.keyboard
            elif self.step == 10: # numbers check [empty example]
                self.demonstration.CheckUser(sampleUser1, cb.NUMBERS_5_CALLBACK)
                self.demonstration.CheckUser(sampleUser1, cb.NUMBERS_5_CALLBACK)
                reply = self.demonstration.keyboard
            elif self.step == 11: # numbers check [500 example]
                self.demonstration.Do500()
                reply = self.demonstration.keyboard
            bot.edit_message_text(self.demonstration.GetText(), self.userid, self.demonstration.check_id, 
                      parse_mode="markdown", reply_markup=reply)
        elif self.step == 13: # finish step
            self.demonstration.DoEndCheck()
            bot.delete_message(self.userid, self.demonstration.check_id)
            del self.demonstration

