#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Common shared resources for modules 
#

import telebot, sys, os, json
from logger import get_logger

log = get_logger("bot")

# setup proxy if asked
if len(sys.argv) > 1:
    if sys.argv[1] == '1':
        telebot.apihelper.proxy = {'http':'http://73.55.76.54:8080'}

if "HEROKU" in list(os.environ.keys()):
    TOKEN = os.environ['TOKEN']
    log.info("[HEROKU] read token: '%s'" % TOKEN)
else:
    with open("TOKEN", "r") as tfile: # local run
        TOKEN = tfile.readline().strip('\n')
        log.info("[LOCAL] read token: '%s'" % TOKEN)
        tfile.close()

bot = telebot.AsyncTeleBot(TOKEN)

BOT_USERNAME = "assassinsgwbot"
ROOT_ADMIN = [] # creator
admins = {}

warchat_id       = None
current_battle   = None
current_precheck = None
current_arscheck = None
current_numcheck = None
current_snowwhite = {}
screen_message_list = []
rage_time_workaround = []

#
# Manage admins list through file at start
#
# load initial list
with open("ADMINS", "r") as f:
    admins_list = json.load(f)
    ROOT_ADMIN = admins_list[0]
    admins = admins_list[1]
    f.close()
    print("Load root admin: ", ROOT_ADMIN)
    print("Load admins list: ", admins)

# save edited list
def SaveAdminsList(newlist):
    admins = newlist
    admins_list = [ROOT_ADMIN, admins]
    with open("ADMINS", "w") as f:
        json.dump(admins_list, f)
        f.close()
    print("Saved admins list: ", admins_list)
