#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class and methods representing guild war statistics collection
#

import datetime, time, copy
from logger import get_logger
from telebot import types

import common
from common import bot
from icons import *
import keyboards as kb
import callbacks as cb
import helpers as hlp

log = get_logger("bot." + __name__)

def GetBestListText(best_list, key="battles"):
    MEDALS = ["🥇", "🥈", "🥉"]
    text = ""
    for i in range(0, len(best_list)):
        user  = best_list[i]["user"].GetData()
        score = best_list[i]["score"].GetData()
        text += MEDALS[i] + " [%s" % user["name"]
        if user["username"]:
            text += " (%s)" % user["username"]
        text += "](tg://user?id=%d) _(%d)_\n" % (user["id"], score[key])
    return text if text != "" else "_нет победителей_"
#
# Call to show guild statistics
# (war chat command)
#
@bot.message_handler(commands=['best'])
def command_best(m):
    # print(m)
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to request guild stats" % (*user,))
    if hlp.IsInPrivateChat(m):
        hlp.SendHelpWrongChat(m.from_user.id, "/best", "получить список лучших за ВГ", False)
        return
    bot.delete_message(m.chat.id, m.message_id)
    # if not hlp.IsGWEndingTime():
    if False:
        common.is_stats_posted = False
        bot.send_message(user[0], "Получить статистику можно только в воскресенье после окончания ВГ!")
        log.error("Failed: wrong time")
        return
    
    if not common.is_stats_posted:
        if common.warchat_id:
            DELAY = 5
            stats = common.statistics["current"]
            total_stats = stats.GetTotalValues().GetData()
            # starting message
            init_stats_msg = bot.send_message(common.warchat_id,
                                              "📈 *Статистика войны гильдий:*\n\n" + \
                                              ICON_SWORDS+" *Проведено боев:* " + str(total_stats["battles"]) + "\n" + \
                                              ICON_ARS+" *Собрано боевых доспехов:* " + str(total_stats["arsenal"]) + "\n" + \
                                              ICON_STAR+" *Снято вражеских звезд:* " + str(total_stats["stars"]) + "\n",
                                              parse_mode="markdown").wait()
            bot.send_chat_action(common.warchat_id, "typing")
            time.sleep(DELAY)
            bot.send_message(common.warchat_id,
                             "🏆 *Списки лучших игроков:*",
                             parse_mode="markdown").wait()
            bot.send_chat_action(common.warchat_id, "typing")
            time.sleep(DELAY)
            # best players
            best_actives_header   = ICON_SWORDS+" *Лучший актив*:\n\n"
            best_arsenal_header   = ICON_ARS+   " *Лучшие арсенальщики*:\n\n"
            best_attackers_header = ICON_STAR+  " *Лучшие танки*:\n\n"
            WAIT_SUFFIX = "🥁..."
            # best active players
            text = GetBestListText(stats.GetBestActives(), "battles")
            best_actives_msg = bot.send_message(common.warchat_id,
                                                best_actives_header + WAIT_SUFFIX,
                                                parse_mode="markdown").wait()
            bot.send_chat_action(common.warchat_id, "typing")
            time.sleep(DELAY)
            bot.edit_message_text(best_actives_header + text,
                                  chat_id=best_actives_msg.chat.id,
                                  message_id=best_actives_msg.message_id,
                                  parse_mode="markdown")
            # best arsenal players
            text = GetBestListText(stats.GetBestArsenals(), "arsenal")
            best_arsenal_msg = bot.send_message(common.warchat_id,
                                                best_arsenal_header + WAIT_SUFFIX,
                                                parse_mode="markdown").wait()
            bot.send_chat_action(common.warchat_id, "typing")
            time.sleep(DELAY)
            bot.edit_message_text(best_arsenal_header + text,
                                  chat_id=best_arsenal_msg.chat.id,
                                  message_id=best_arsenal_msg.message_id,
                                  parse_mode="markdown")
            # best attackers
            text = GetBestListText(stats.GetBestAttackers(), "stars")
            best_attackers_msg = bot.send_message(common.warchat_id,
                                                best_attackers_header + WAIT_SUFFIX,
                                                parse_mode="markdown").wait()
            bot.send_chat_action(common.warchat_id, "typing")
            time.sleep(DELAY)
            bot.edit_message_text(best_attackers_header + text,
                                  chat_id=best_attackers_msg.chat.id,
                                  message_id=best_attackers_msg.message_id,
                                  parse_mode="markdown")
            # ending messages
            bot.send_message(common.warchat_id,
                             ICON_PRAISE+" *Поздравляем победителей!* " + ICON_PRAISE + "\n\n" + \
                             "_Лучшему игроку в любой номинации присуждается 🎖 орден, " + \
                             "который будет виден в течение всей следующей войны._",
                             parse_mode="markdown")
            common.is_stats_posted = True
            log.info("Guild stats posted!")
            # shift the stats cycle
            common.statistics["previous"] = common.statistics["current"]
            common.statistics["current"] = None
        else:
            hlp.SendHelpWrongChat(m.from_user.id, "/warchat", "запомнить военный чат", False)
            log.error("War chat_id is not set, cannot post GW stats!")
    else:
        log.error("Guild stats has been already posted!")

#
# Base class representing a User object
#
class User():
    _id      = None
    name     = None
    username = None

    def __init__(self, _id, name=None, username=None):
        self._id      = _id
        self.name     = name
        self.username = username

    def __hash__(self):
        return hash((self._id))

    def __eq__(self, other):
        return (self._id) == (other._id)

    def __ne__(self, other):
        return not(self == other)

    def __repr__(self):
        return "User(%d, %s, %s)" % (self._id, self.name, self.username)

    def GetData(self):
        return {"id"      : self._id,
                "name"    : self.name,
                "username": self.username
                }

#
# Base class representing a war record object
#
class Score():
    battles = 0
    arsenal = 0
    stars   = 0

    def __init__(self, battle=0, arsenal=0, stars=0):
        self.battles = battle
        self.arsenal = arsenal
        self.stars   = stars

    def __hash__(self):
        return hash((self.battles, self.arsenal, self.stars))

    def __eq__(self, other):
        return (self.battles, self.arsenal, self.stars) == (other.battles, other.arsenal, other.stars)

    def __ne__(self, other):
        return not(self == other)

    def __repr__(self):
        return "Score(%s %d, %s %d, %s %d)" % (ICON_SWORDS, self.battles, ICON_ARS, self.arsenal, ICON_STAR, self.stars)

    def AddScore(self, score):
        if not isinstance(score, self.__class__):
            log.error("Trying to add score using another Score, but object type is wrong")
            return
        self.battles = self.battles + score.battles
        self.arsenal = self.arsenal + score.arsenal
        self.stars   = self.stars + score.stars

    def RemoveScore(self, score):
        if not isinstance(score, self.__class__):
            log.error("Trying to add score using another Score, but object type is wrong")
            return
        # invert score then add it
        score.battles = (-1)*score.battles
        score.arsenal = (-1)*score.arsenal
        score.stars   = (-1)*score.stars
        self.AddScore(score)

    def GetData(self):
        return {"battles": self.battles,
                "arsenal": self.arsenal,
                "stars"  : self.stars
                }

class Statistic():
    stats = {} # {User: Score}

    def Update(self, update):
        if not isinstance(update, dict):
            log.error("Invalid update type: %s (need dict)", type(update))
            return
        for user, score in update.items():
            if not isinstance(user, User) or not isinstance(score, Score):
                log.error("Invalid update item: %s:%s (need User: Score)", type(user), type(score))
                return
            if user not in self.stats:
                self.stats[user] = score
            else:
                self.stats[user].AddScore(score)

    def get_best_internal(self, key, count):
        stats_temp = copy.deepcopy(self.stats)
        best = []
        best_temp = {"user" : User(-1),
                     "score": Score()
                     }
        for i in range(0, count):
            # init starting best user
            best_one = copy.deepcopy(best_temp)
            # find the best user
            for user, score in stats_temp.items():
                if score.GetData()[key] > best_one["score"].GetData()[key]:
                    best_one["user"] = user
                    best_one["score"] = score
            if best_one["user"] != best_temp["user"]:
                # save it
                best.append(best_one)
                # remove from list and start over for the further places
                del stats_temp[best_one["user"]]
        return best

    def GetTotalValues(self):
        total = Score()
        for score in self.stats.values():
            total.AddScore(score)
        return total

    # get users that checked for battle the most
    def GetBestActives(self, count=3):
        return self.get_best_internal("battles", count)

    # get users that checked for battle the most
    def GetBestArsenals(self, count=3):
        return self.get_best_internal("arsenal", count)

    # get users that checked for battle the most
    def GetBestAttackers(self, count=3):
        return self.get_best_internal("stars", count)
