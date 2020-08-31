#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Various support functions
#

import re, datetime, os, pickle
from random import sample
from logger import get_logger
import common
from collections import Counter
from commands import COMMANDS
from icons import *

log = get_logger("bot." + __name__)

def AWSUploadFile(filepath):
    if not os.path.isfile(filepath):
        return False
    common.aws_client.upload_file(filepath, 'cloud-cube', 'tthoivsc7apn/' + filepath)
    return True

def AWSDownloadFile(filepath):
    if not os.path.isdir('AWS_TEMP'):
        os.mkdir('AWS_TEMP')
    destpath = 'AWS_TEMP/' + filepath
    # delete old file if exists
    if os.path.isfile(destpath):
        os.remove(destpath)
    common.aws_client.download_file('cloud-cube', 'tthoivsc7apn/' + filepath, destpath)
    if os.path.isfile(destpath):
        return destpath
    return None

def CheckInlineQuery(pattern, query): # check query for primary pattern support function 
    res = re.compile(pattern).findall(query.query)
    if res != [] and len(res) == 1:
        return True
    return False

def IsCheckTimeQuery(query): # return if query contains check time and check time list
    pattern = COMMANDS["battle"] + " "
    if CheckInlineQuery(pattern, query):
        battle_query = query.query.replace(pattern, "")
        time = re.findall(r'(?:\d|[01]\d|2[0-3])\D[0-5]\d', query.query)
        if time != [] and len(time) == 1:
            return True, time[0]
    return False, None

def IsNumbersQuery(query): # return if query contains numbers check and the list of numbers
    pattern = COMMANDS["numbers"] + " "
    if CheckInlineQuery(pattern, query):
        numbers_list = query.query.replace(pattern, "")
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

def IsCrysQuery(query): # return if query contains crystals check
    pattern = COMMANDS["crystals"] + " "
    if CheckInlineQuery(pattern, query):
        range_list = query.query.replace(pattern, "")
        values = re.findall(r'\b(\d+)\b', range_list)
        if values != [] and len(values) == 2: # exactly 2 numbers
            # max >= step, step > 0
            if int(values[0]) >= int(values[1]) and int(values[1]) > 0: 
                # not too much buttons
                if int(values[0]) // int(values[1]) < 30:
                    return True, values
    return False, None

def IsArsQuery(query): # return if query contains ars check and the time of rage
    pattern = COMMANDS["arsenal"] + " "
    if CheckInlineQuery(pattern, query):
        rage_time_query = query.query.replace(pattern, "")
        rage_time = re.findall(r'(?:\d|[01]\d|2[0-3])\D[0-5]\d', rage_time_query)
        if rage_time != [] or len(rage_time) == 1:
            return True, rage_time[0]
    return False, None

def SendHelpNonAdmin(message):
    text =  "Мной могут управлять только офицеры гильдии.\n"
    text += "Обратитесь к одному из офицеров за подробностями:\n\n"
    for admin in common.admins:
        text += "[%s](tg://user?id=%s)\n" % (common.admins[admin], admin)
    common.bot.send_message(message.from_user.id, text, parse_mode="markdown")

def SendHelpNoBattle(chat_id):
    error_text =  "Текущий активный бой отсутствует.\n"
    error_text += "Начните новый бой, упомянув меня в военном чате и задав время боя.\n"
    error_text += "*Пример*: @assassinsgwbot бой 14-00"
    common.bot.send_message(chat_id, error_text, parse_mode="markdown")

def SendHelpWrongChat(toUser, command, description, needPrivate):
    if needPrivate:
        target_chat = "в личном чате"
    else:
        target_chat = "в военном чате"
    log.error("Failed: wrong chat command, need to use %s" % target_chat)
    text = "Используйте команду %s %s, чтобы %s!" % (command, target_chat, description)
    common.bot.send_message(toUser, text)

def LogEvent(message):
    common.bot.send_message(common.logchat_id, message, disable_notification=True)

def CanStartNewPrecheck():
    res = common.current_precheck == None
    if not res:
        res = common.current_precheck.is_postponed
    return res


def CanStartNewCryscheck():
    res = common.current_cryscheck == None
    if not res:
        res = common.current_cryscheck.is_postponed
    return res

def CanStartNewBattle():
    res = common.current_battle == None
    if not res:
        res = common.current_battle.is_postponed
    return res

def CanStopCurrentBattle():
    res = not CanStartNewBattle()
    if res:
        now = datetime.datetime.now()
        elapsed = now - common.current_battle.time["start"]
        res = int(elapsed.total_seconds()) >= 1*60*60 # more than 1 hour passed
    return res

def CanStartNewArs():
    res = common.current_arscheck == None
    if not res:
        res = common.current_arscheck.is_fired or common.current_arscheck.is_postponed
    return res

def CanStartNewNumbers():
    res = common.current_numcheck == None
    if not res:
        res = common.current_numcheck.is_postponed
    return res

def GetScreenMessageByMediaID(_id):
    global screen_message_list
    if common.screen_message_list:
        for screen in common.screen_message_list:
            if screen.media_group_id == _id:
                return screen
    return None

def IsUserAdmin(id):
    from statistics import User
    if isinstance(id, User):
        id = id._id
    if str(id) in common.admins or \
       str(id) == common.ROOT_ADMIN[0]:
        return True
    else:
        return False

def IsInPrivateChat(message):
    if message.chat.id == message.from_user.id:
        return True
    return False

def IsGWDurationTime():
    now = datetime.datetime.now()
    gw_time = [now.replace(day=4, hour=18, minute=0, second=1), # 18-00 (MSK) Friday
               now.replace(day=6, hour=17, minute=59, second=59), # 18-00 (MSK) Sunday
               ]
    if now >= gw_time[0] and \
       now <= gw_time[1]:
       return True
    return False

def IsGWEndingTime():
    now = datetime.datetime.now()
    avail_weekday = 6 # Sunday
    avail_time = [now.replace(hour=18, minute=0, second=0),
                  now.replace(day=now.day+1, hour=2, minute=59, second=59)
                 ]
    if now.weekday() == avail_weekday and \
       now >= avail_time[0]           and \
       now <= avail_time[1]:
       return True
    return False

def NeedCheckBackup(check):
    if not check: # guide case, ignore that
        return False
    if check.last_backup:
        elapsed = int((datetime.datetime.now() - check.last_backup).total_seconds())
        if elapsed >= common.settings.GetSetting("backup_timeout")*60:
            return True
    else:
        return True
    return False

def AWSCheckBackup(check):
    """
    Backup selected battle check into pickle file.
    Upload to AWS
    """
    log.debug("AWS Battle check (%s) backup started", type(check).__name__)
    BACKUP_NAME = "GWBotCurrent" + type(check).__name__ + ".BAK"
    with open(BACKUP_NAME, 'wb') as backup:
        pickle.dump(check, backup, pickle.HIGHEST_PROTOCOL)
        backup.close()
    if AWSUploadFile(BACKUP_NAME):
        log.debug("Battle check (%s) has been successfully uploaded to AWS cloud.", type(check).__name__)
    else:
        log.error("Battle check (%s) AWS upload failed.", type(check).__name__)

def AWSCheckRestore(className):
    """
    Restore selected battle check from pickle file (download from AWS).
    Commonly used after bot start (thanks Heroku for daily restarts)
    """
    log.debug("AWS Battle check (%s) restore started", className)
    try:
        BACKUP_NAME = "GWBotCurrent" + className + ".BAK"
        # download backup
        filepath = AWSDownloadFile(BACKUP_NAME)
        if filepath == None:
            raise Exception("Battle check (%s) AWS download failed.", className)
        log.debug("Battle check (%s) has been successfully downloaded from AWS cloud.", className)
        # unwrap and set object
        with open(filepath, 'rb') as f:
            check = pickle.load(f)
            f.close()
        if className == "Battle":
            common.current_battle = check
        elif className == "Arsenal":
            common.current_arscheck = check
        elif className == "NumbersCheck":
            common.current_numcheck = check
        log.debug("Restoring Battle check (%s) successful.", className)
        # common.bot.send_message(int(common.ROOT_ADMIN[0]), ICON_CHECK+" Чек %s восстановлен!" % className)
        print(check.__dict__)
    except Exception as err:
        log.error("Restoring Battle check (%s) failed: %s", className, str(err))

# generate Snow White praise text for user (random pool) 
def SnowGeneratePraise(user):
    text = ICON_SNOW + " "
    if user[1]:
        text += "[%s" % user[1]
    else:
        text += "[%s" % user[2]
    text += "](tg://user?id=%d), %s" % (user[0], sample(snowPraisePool, 1)[0])
    return text

snowPraisePool = [
    "тобой была проделана большая работа! 🤯",
    "мы побеждали благодаря тебе! 😉",
    "я знала, что на тебя можно положиться! 💋",
    "я горжусь тобой! 😘",
    "я была уверена, что ты не подведешь! 🛡",
    "именно так надо сражаться! 🎯",
    "ты очень классно воевал! Чувствуется профессионализм и опыт. 😎",
    "я горжусь, что ты в нашей команде! 🥰",
    "ты всё делаешь правильно! 🤗",
    "как тебе это удается? 😧",
    "твое участие - как раз то, что было нам нужно! 😋",
    "наши победы - твои победы 🧐",
    "это было незабываемо! 😍",
    "грандиозная игра! 🤩",
    "гораздо лучше, чем я ожидала! 😅",
    "ух! 😏",
    "нам очень важна твоя помощь! 😇",
    "воевать с тобой просто радость! 🥰",
    "ты нам необходим! 😎",
    "я сойду с ума, если с тобой что-нибудь случится! 😓",
    "экстра – класс! 🤙",
    "с каждым днем у тебя получается всё лучше! 🙌",
    "Уже лучше! 🤘",
    "еще лучше, чем прежде! 👍",
    "научи меня воевать так же! ⚔️",
    "нам без тебя не обойтись! ⭐️",
    "неподражаемая игра! 🏆",
    "никто не может заменить тебя! 🥇",
    "я сама не смогла бы сыграть лучше! 🎖",
    "очень эффектно! 🎸",
    "ты лучше, чем все, кого я знаю! 🤴",
    "к этому осталось добавить: «Я люблю тебя!» 💋",
    "ТЕБЕ ВЫПАЛА СЕКРЕТНАЯ ФРАЗА! 👽",
    "даже не знаю, как тебя отблагодарить за такую работу! 💪",
]
