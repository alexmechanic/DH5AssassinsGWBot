#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class and methods representing guild war statistics collection
#

import os, datetime, time, copy, pickle, json
from logger import get_logger

import common
from icons import *
import helpers as hlp

log = get_logger("bot." + __name__)

class Jsonable(object):
    """
    Base class to make JSON serialize nested statistic objects
    """
    def __iter__(self):
        for attr, value in self.__dict__.iteritems():
            if isinstance(value, datetime.datetime):
                iso = value.isoformat()
                yield attr, iso
            elif(hasattr(value, '__iter__')):
                if(hasattr(value, 'pop')):
                    a = []
                    for subval in value:
                        if(hasattr(subval, '__iter__')):
                            a.append(dict(subval))
                        else:
                            a.append(subval)
                    yield attr, a
                else:
                    yield attr, dict(value)
            else:
                yield attr, value

class StatsEncoder(json.JSONEncoder):
    """
    Encoder for statistic objects for JSON
    """
    def default(self, obj):
        if isinstance(obj, User) or \
           isinstance(obj, Score) or \
           isinstance(obj, StatRecord):
            return repr(obj)
        elif isinstance(obj, Statistic):
            return obj.__dict__
        else:
            return json.JSONEncoder.default(self, obj)

def GetBestListText(best_list, key="battles"):
    """
    Support function getting the best users list in text view.
    Prefixes user records with medals, suffixes with personal count
    """
    MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = ""
    for i in range(0, len(best_list)):
        user  = best_list[i]["user"].GetData()
        score = best_list[i]["score"].GetData()
        text += MEDALS[i] + " [%s" % user["name"]
        if user["username"]:
            text += " (%s)" % user["username"]
        text += "](tg://user?id=%d) _(%d)_\n" % (user["id"], score[key])
    return text if text != "" else "_нет победителей_"


@common.bot.message_handler(commands=['statbackup'])
def command_stat_backup(m):
    """
    Backup whole current statistic into pickle and json-readable files.
    Send files to user
    """
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is requested statistics backup" % (*user,))
    try:
        if not hlp.IsInPrivateChat(m):
            common.bot.delete_message(m.chat.id, m.message_id)
            hlp.SendHelpWrongChat(m.from_user.id, "/statbackup", "создать резервную копию статистики", True)
            return
    except: # case if called from Statistic backup timeout. Could be ignored
        pass
    if not hlp.IsUserAdmin(m):
        hlp.SendHelpNonAdmin(m)
        return
    FILE_PREFIX = "GWBotStatistic"
    common.bot.send_message(m.from_user.id, "📥 Сохраняю статистику...")
    try:
        # dump pickle Statistic object
        with open(FILE_PREFIX+'.BAK', 'wb') as backup:
            pickle.dump(common.statistics, backup, pickle.HIGHEST_PROTOCOL)
            backup.close()
        # dump json Statistic object
        with open(FILE_PREFIX+'.txt', 'w') as backup_json:
            json.dump(common.statistics, backup_json, separators=(',', ': '), cls=StatsEncoder, indent=4, ensure_ascii=False)
            backup_json.close()
        # send pickle
        common.bot.send_chat_action(m.from_user.id, "upload_document")
        with open(FILE_PREFIX+'.BAK', 'rb') as backup:
            common.bot.send_document(m.from_user.id, backup, caption="Файл-объект статистики").wait()
            backup.close()
        aws_stat_backup(FILE_PREFIX+'.BAK', burst=True)
        os.remove(FILE_PREFIX+'.BAK')
        # send json
        common.bot.send_chat_action(m.from_user.id, "upload_document")
        with open(FILE_PREFIX+'.txt', 'r') as backup_json:
            common.bot.send_document(m.from_user.id, backup_json, caption="JSON-описание статистики").wait()
            backup_json.close()
        os.remove(FILE_PREFIX+'.txt')
    except Exception as err:
        log.error("Backup statistics failed: ", str(err))
        common.bot.send_message(m.from_user.id, ICON_CANCEL+" Ошибка сохранения статистики!")


def aws_stat_backup(filename="GWBotStatistic.BAK", burst=False):
    """
    Backup whole current statistic into pickle file.
    Upload to AWS
    @param burst Do not save backup to file
    """
    log.debug("AWS Statistic backup started")
    # common.bot.send_message(int(common.ROOT_ADMIN[0]), "🌐 Сохраняю статистику (AWS)...")
    # if burst-upload requested (no additional file backup)
    if not burst:
        with open(filename, 'wb') as backup:
            pickle.dump(common.statistics, backup, pickle.HIGHEST_PROTOCOL)
            backup.close()
    # upload file
    if hlp.AWSUploadFile(filename):
        log.debug("Statistics has been successfully uploaded to AWS cloud.")
        # common.bot.send_message(int(common.ROOT_ADMIN[0]), ICON_CHECK+" Статистика успешно сохранена!")
    else:
        log.error("Statistics AWS upload failed.")
        common.bot.send_message(int(common.ROOT_ADMIN[0]), ICON_CANCEL+" Ошибка сохранения статистики!")


@common.bot.message_handler(commands=['statrestore'])
def command_stat_restore(m):
    """
    Restore whole current statistic from pickle file (command help part).
    """
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is requested statistics restore" % (*user,))
    if not hlp.IsInPrivateChat(m):
        common.bot.delete_message(m.chat.id, m.message_id)
        hlp.SendHelpWrongChat(m.from_user.id, "/statrestore", "восстановить статистику из резервной копии", True)
        return
    if not hlp.IsUserAdmin(m):
        hlp.SendHelpNonAdmin(m)
        return
    common.bot.send_message(m.from_user.id,
                            "🗄 Чтобы восстановить статистику, пришлите файл резервной копии статистики в формате _.BAK_",
                            parse_mode="markdown")


def aws_stat_restore(filename="GWBotStatistic.BAK", force=True):
    """
    Restore whole current statistic from pickle file (download from AWS).
    @param force Remove old local backup
    """
    log.debug("AWS Statistic restore started")
    # common.bot.send_message(int(common.ROOT_ADMIN[0]), "🌐 Восстанавливаю статистику (AWS)...")
    try:
        # remove old statistics backup if forced update
        if force:
            if os.path.isfile(filename):
                os.remove(filename)
        # download backup
        filepath = hlp.AWSDownloadFile(filename)
        if filepath == None:
            raise Exception("Statistics AWS download failed.")
        log.debug("Statistics has been successfully downloaded from AWS cloud.")
        # unwrap and set object
        with open(filepath, 'rb') as f:
            common.statistics = pickle.load(f)
            f.close()
        # common.bot.send_message(int(common.ROOT_ADMIN[0]), ICON_CHECK+" Статистика успешно восстановлена!")
        log.debug("Restoring statistics successful (AWS)")
    except Exception as err:
        log.error("Restoring statistics failed (AWS): %s", str(err))
        common.bot.send_message(int(common.ROOT_ADMIN[0]), ICON_CANCEL+" Ошибка восстановления статистики!")


@common.bot.message_handler(func=lambda message: os.path.splitext(message.document.file_name)[1].lower() == ".bak" if message.document else False,
                            content_types=['document'])
def file_stat_restore(m):
    """
    Restore whole current statistic from pickle file.
    """
    # print(m)
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to restore statistics" % (*user,))
    FILENAME = "stats.BAK"
    common.bot.send_message(m.from_user.id, "📤 Восстанавливаю статистику...")
    try:
        backup = common.bot.download_file(common.bot.get_file(m.document.file_id).wait().file_path).wait()
        with open(FILENAME, 'wb') as f:
            f.write(backup)
            f.close()
        with open(FILENAME, 'rb') as f:
            common.statistics = pickle.load(f)
            f.close()
        os.remove(FILENAME)
        common.bot.send_message(m.from_user.id, ICON_CHECK+" Статистика успешно восстановлена!")
        log.debug("Restoring statistics successful")
    except Exception as err:
        log.error("Restoring statistics failed: %s", str(err))
        common.bot.send_message(m.from_user.id, ICON_CANCEL+" Ошибка восстановления статистики!")

@common.bot.message_handler(commands=['best'])
def command_best(m):
    """
    Call to show guild statistics (war chat command)
    """
    # print("command_best")
    # print(m)
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.debug("User %d (%s %s) is trying to request guild stats" % (*user,))
    if hlp.IsInPrivateChat(m):
        hlp.SendHelpWrongChat(m.from_user.id, "/best", "получить список лучших за ВГ", False)
        return
    common.bot.delete_message(m.chat.id, m.message_id)
    if not hlp.IsGWEndingTime():
        common.bot.send_message(user[0], "Получить статистику можно только в воскресенье после окончания ВГ!")
        log.error("Failed: wrong time")
        return
    
    if not common.statistics.is_posted:
        if common.warchat_id:
            DELAY = 5
            total_stats   = common.statistics.GetTotalValues().GetData()
            total_battles = common.statistics.GetBattlesCount()
            # starting message
            init_stats_msg = common.bot.send_message(common.warchat_id,
                "📈 *Статистика войны гильдий:*\n\n" + \
                ICON_SWORDS+" *Проведено боев:* " + str(total_battles) + " _(" + str(total_stats["battles"]) + " участников)_\n" + \
                ICON_ARS+" *Собрано боевых доспехов:* " + str(total_stats["arsenal"]) + "\n" + \
                ICON_STAR+" *Снято вражеских звезд:* " + str(total_stats["stars"]) + "\n",
                parse_mode="markdown").wait()
            common.bot.send_chat_action(common.warchat_id, "typing")
            time.sleep(DELAY)
            common.bot.send_message(common.warchat_id,
                                    "🏆 *Списки лучших игроков:*",
                                    parse_mode="markdown").wait()
            common.bot.send_chat_action(common.warchat_id, "typing")
            time.sleep(DELAY)
            # best players
            best_actives_header   = ICON_SWORDS+" *Лучший актив*:\n\n"
            best_arsenal_header   = ICON_ARS+   " *Лучшие арсенальщики*:\n\n"
            best_attackers_header = ICON_STAR+  " *Лучшие танки*:\n\n"
            WAIT_SUFFIX = "🥁..."
            # best active players
            text = GetBestListText(common.statistics.GetBestActives(), "battles")
            best_actives_msg = common.bot.send_message(common.warchat_id,
                                                best_actives_header + WAIT_SUFFIX,
                                                parse_mode="markdown").wait()
            common.bot.send_chat_action(common.warchat_id, "typing")
            time.sleep(DELAY)
            common.bot.edit_message_text(best_actives_header + text,
                                  chat_id=best_actives_msg.chat.id,
                                  message_id=best_actives_msg.message_id,
                                  parse_mode="markdown")
            # best arsenal players
            text = GetBestListText(common.statistics.GetBestArsenals(), "arsenal")
            best_arsenal_msg = common.bot.send_message(common.warchat_id,
                                                best_arsenal_header + WAIT_SUFFIX,
                                                parse_mode="markdown").wait()
            common.bot.send_chat_action(common.warchat_id, "typing")
            time.sleep(DELAY)
            common.bot.edit_message_text(best_arsenal_header + text,
                                  chat_id=best_arsenal_msg.chat.id,
                                  message_id=best_arsenal_msg.message_id,
                                  parse_mode="markdown")
            # best attackers
            text = GetBestListText(common.statistics.GetBestAttackers(), "stars")
            best_attackers_msg = common.bot.send_message(common.warchat_id,
                                                best_attackers_header + WAIT_SUFFIX,
                                                parse_mode="markdown").wait()
            common.bot.send_chat_action(common.warchat_id, "typing")
            time.sleep(DELAY)
            common.bot.edit_message_text(best_attackers_header + text,
                                  chat_id=best_attackers_msg.chat.id,
                                  message_id=best_attackers_msg.message_id,
                                  parse_mode="markdown")
            # ending messages
            common.bot.send_message(common.warchat_id,
                             ICON_PRAISE+" *Поздравляем победителей!* " + ICON_PRAISE + "\n\n" + \
                             "_Лучшему игроку в любой номинации присуждается 🎖 орден, " + \
                             "который будет виден на войнах в течение " + \
                             str(common.statistics.cycle_time) + " последующих войн._",
                             parse_mode="markdown")
            common.statistics.is_posted = True
            log.info("Guild stats posted!")
        else:
            hlp.SendHelpWrongChat(m.from_user.id, "/warchat", "запомнить военный чат", False)
            log.error("War chat_id is not set, cannot post GW stats!")
    else:
        common.bot.send_message(user[0], "Статистика уже была опубликована!")
        log.error("Guild stats has been already posted!")

#
# Base class representing a User object
#
class User(Jsonable):
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
        text = "User(%d, %s" % (self._id, self.name)
        if self.username:
            text += ", %s)" % self.username
        else:
            text += ")"
        return text

    def GetData(self):
        return {"id"      : self._id,
                "name"    : self.name,
                "username": self.username
                }


#
# Base class representing a war record object
#
class Score(Jsonable):
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

    def __sub__(self, other):
        diff = [self.battles - other.battles,
                self.arsenal - other.arsenal,
                self.stars   - other.stars]
        self.battles = diff[0] if diff[0] > 0 else 0
        self.arsenal = diff[1] if diff[1] > 0 else 0 
        self.stars   = diff[2] if diff[2] > 0 else 0
        return self

    def __repr__(self):
        return "Score(B: %d, A: %d, S: %d)" % (self.battles, self.arsenal, self.stars)

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

class StatRecord(Jsonable):
    date = None # datetime
    stats = {}  # {User: Score}
    battles_count = 0

    def __init__(self):
        self.date = datetime.datetime.now()
        self.stats = {}
        self.battles_count = 0

    def __sub__(self, other):
        self.battles_count -= other.battles_count
        for user1, score1 in self.stats.items():
            for user2, score2 in other.stats.items():
                if user1 == user2:
                    self.stats[user1] = self.stats[user1] - other.stats[user2]
        return self

    def __repr__(self):
        text = []
        for user, score in self.stats.items():
            text.append(repr(user) + ": " + repr(score))
        return "StatRecord[%s][B: %d](%s)" % (self.date, self.battles_count, ", ".join(text))

    def AddStat(self, user, record):
        if user not in self.stats:
            self.stats[user] = record
        else:
            self.stats[user].AddScore(record)

    def AddBattle(self):
        self.battles_count += 1

    def GetBattlesCount(self):
        return self.battles_count

    def GetDate(self):
        return self.date

    def GetStat(self):
        return self.stats

    def GetRawData(self):
        return [(user.GetData(), score.GetData()) for user, score in self.stats.items()]

    def GetBest(self, key, count):
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
                new_score = score.GetData()[key]
                if new_score >= best_one["score"].GetData()[key] and \
                   new_score != 0:
                    best_one["user"] = user
                    best_one["score"] = score
            if best_one["user"] != best_temp["user"]:
                # save it
                best.append(best_one)
                # remove from list and start over for the further places
                del stats_temp[best_one["user"]]
        return best

class Statistic(Jsonable):
    statistics  = [] # [StatRecord] of size cycle_time. lowest index is the newer stat
    nominated   = [] # [User]
    cycle_time  = 4  # in weeks
    is_posted = False
    backup_timeout = 2 # backup statistic every 3 records (send to the root admin)
    update_counter = 0 # counter of updates for backup'ing

    def __init__(self, cycle_time):
        self.cycle_time     = cycle_time
        self.statistics     = [StatRecord() for i in range(0, cycle_time)]
        self.nominated      = []
        self.is_posted      = False
        self.backup_timeout = 2
        self.update_counter = 0

    def Update(self, update):
        print("UPDATE: ", update)
        print("NONUPDATED STATS:")
        print(self.statistics)
        is_battle_update = False
        if isinstance(update, StatRecord): # unpack StatRecord to dict type
            update = update.GetStat()
        elif not isinstance(update, dict): # default update type
            log.error("Invalid update type: %s (dict or StatRecord expected)", type(update))
            return
        for user, score in update.items():
            if not isinstance(user, User) or not isinstance(score, Score):
                log.error("Invalid update item: %s:%s (need User: Score)", type(user), type(score))
                return
            self.statistics[0].AddStat(user, score)
            if score.GetData()["battles"] > 0:
                is_battle_update = True
        if is_battle_update:
            self.statistics[0].AddBattle()
        print("UPDATED STATS:")
        print(self.statistics)

    def GetTotalValues(self):
        total = Score()
        for score in self.statistics[0].GetStat().values():
            total.AddScore(score)
        return total

    def GetBattlesCount(self):
        return self.statistics[0].GetBattlesCount()

    def GetNominatedPrefix(self, user):
        # workaround User object creation if argument is simple list
        if not isinstance(user, User):
            user = User(*user,)
        if user in self.nominated:
            return "🎖 "
        return ""

    def AddNomination(self, best_record):
        if len(best_record) == 0:
            return
        if best_record[0]["user"] not in self.nominated:
            self.nominated.append(best_record[0]["user"])

    def RemoveNominations(self, stat):
        if not stat: # at the very start older stats do not exist yet
            return
        for user in stat.GetStat().keys():
            if user in self.nominated:
                self.nominated.remove(user)

    # get users that checked for battle the most
    def GetBestActives(self, count=3):
        result = self.statistics[0].GetBest("battles", count)
        self.AddNomination(result)
        return result

    # get users that checked for battle the most
    def GetBestArsenals(self, count=3):
        result = self.statistics[0].GetBest("arsenal", count)
        self.AddNomination(result)
        return result

    # get users that checked for battle the most
    def GetBestAttackers(self, count=3):
        result = self.statistics[0].GetBest("stars", count)
        self.AddNomination(result)
        return result

    def BackupIfNeed(self, msg):
        # new AWS backup
        aws_stat_backup()
        # old local backup cycle
        # if self.update_counter < self.backup_timeout:
        #     self.update_counter += 1
        # else:
        #     # pre-mutations of message to imitate root admin backup request
        #     msg.from_user.id = int(common.ROOT_ADMIN[0])
        #     msg.from_user.name = common.ROOT_ADMIN[1]
        #     command_stat_backup(msg)
        #     self.update_counter = 0


    def CycleIfNeed(self):
        """
        Statistics cyclying funcion.
        Executes cycling if checked from Friday to Sunday (next GW detected) and making sure it is not the same GW.
        """
        now = datetime.datetime.now()
        # TODO: check if 3 days threshold is enough to detect new GW (mind testing!)
        diff = now - self.statistics[0].GetDate()
        if diff.days >= 3 :# and hlp.IsGWDurationTime():
            self.do_cycle_internal()

    def do_cycle_internal(self):
        print("before cycle:")
        print(self.statistics)        
        # shift the stats records to the right
        self.statistics = self.statistics[-1:] + self.statistics[:-1]
        # eliminate oldest nominated users
        self.RemoveNominations(self.statistics[0])
        # destroy the oldest (now first)
        print("before destroy old StatRecord:")
        print(self.statistics)
        self.statistics[0] = StatRecord()
        print("after re-init newest:")
        print(self.statistics)
        self.is_posted = False
