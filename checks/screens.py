#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Class representing screen nicknames parsing technique
#

import datetime, os
from icons import *
from logger import get_logger

import common
from common import bot
from .screen_parser import ocr_core
import helpers as hlp

log = get_logger("bot." + __name__)

screen_list = {} # {user_id: ScreenList}
is_editing = False

#
# Screens OCR
# (private bot chat)
#
@bot.message_handler(content_types=['photo'])
def command_screens_ocr(m):
    # print("command_screens_ocr")
    # print(m)
    # do not resrtict sending screens into war chat, but process only ones sent privately
    user = [m.from_user.id, m.from_user.username, m.from_user.first_name]
    log.info("User %d (%s %s) is trying to process guild screens" % (*user,))
    if not hlp.IsInPrivateChat(m):
        log.error("Failed: not in private chat. Ignored")
        return
    screen_params = {
        "id" :   m.photo[-1].file_id,
        "mid":   m.message_id,
        "group": m.media_group_id,
        "user":  m.from_user.id,
        }
    is_new_screens = False
    if screen_params["user"] not in screen_list:
        # if this user is new - create key for user
        log.debug("First user request, creating new user entry")
        screen_list[screen_params["user"]] = ScreenList(screen_params["group"], screen_params["user"])
        is_new_screens = True
    elif screen_params["group"] == None or \
         screen_params["group"] != screen_list[screen_params["user"]].media_group_id:
        # if user sent new screens album - create new ScreenList for this group replacing the old one
        log.debug("New screens album, creating new entry for user")
        del screen_list[screen_params["user"]]
        screen_list[screen_params["user"]] = ScreenList(screen_params["group"], screen_params["user"])
        is_new_screens = True
    if (is_new_screens):
        # send initial message for new request
        message = bot.send_message(screen_params["user"],
                                   screen_list[screen_params["user"]].GetText() + "\n_(обработка...)_",
                                   parse_mode="markdown").wait()
        # save message id
        screen_list[screen_params["user"]].SetMessageID(message.message_id)
    # download screen
    downloaded = bot.download_file(bot.get_file(screen_params["id"]).wait().file_path).wait()
    # save screen to file with name == id
    with open(screen_params["id"], 'wb') as screen_file:
        screen_file.write(downloaded)
        screen_file.close()

    # process image
    bot.edit_message_text(screen_list[screen_params["user"]].GetText() + "\n_(обработка...)_",
                          chat_id=screen_params["user"],
                          message_id=screen_list[screen_params["user"]].GetMessageID(),
                          parse_mode="markdown")
    # send typing status to user to make him wait a bit
    bot.send_chat_action(screen_params["user"], 'typing')
    # process image
    names = ocr_core(screen_params["id"])
    # delete downloaded file
    os.remove(screen_params["id"])
    # update screen list with parsed nicknames
    screen_list[screen_params["user"]].AddScreen(screen_params["mid"], names)
    # update list message for user
    bot.edit_message_text(screen_list[screen_params["user"]].GetText(),
                          chat_id=screen_params["user"],
                          message_id=screen_list[screen_params["user"]].GetMessageID(),
                          parse_mode="markdown")


class ScreenList():
    media_group_id = None
    user_id        = None
    message_id     = None
    numbers = {} # {id: [names]}, message_id is used for key

    def __init__(self, media_group_id, user):
        self.is_posted = False
        self.numbers = {}
        self.media_group_id = media_group_id
        self.user_id = user
        log.info("New screen list created: media %s, user %s", self.media_group_id, self.user_id)

    def SetMessageID(self, message_id):
        self.message_id = message_id
        log.debug("Set message_id: %s" % self.message_id)

    def GetMessageID(self):
        return self.message_id

    def AddScreen(self, _id, screen):
        self.numbers[_id] = screen
        log.debug("Add new nicks to screens:")
        log.debug(self.numbers[_id])

    def GetHeader(self):
        text = ICON_LIST+" *Номера:*\n"
        return text

    def GetText(self):
        text = self.GetHeader()
        # list numbers by order
        idx = 1
        # show nicknames sorted by actual order they've been sent (album bulk uploading guarantees that)
        for _id in sorted(list(self.numbers.keys())):
            for nick in self.numbers[_id]:
                # align numbers to make list look nice
                text +='\n`{:>2}: {}`'.format(idx, nick)
                idx += 1
        return text
