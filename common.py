#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Common shared resources for modules 
#

import telebot, sys, os, json, boto3, pickle
from logger import get_logger
import helpers as hlp

log = get_logger("bot." + __name__)

# setup proxy if asked
if len(sys.argv) > 1:
    if sys.argv[1] == '1':
        telebot.apihelper.proxy = {'http':'http://73.55.76.54:8080'}

if "HEROKU" in list(os.environ.keys()):
    TOKEN = os.environ['TOKEN']
    log.info("[HEROKU] read token: '%s'" % TOKEN)
    AWS_KEY = os.environ['CLOUDCUBE_ACCESS_KEY_ID']
    log.info("[HEROKU] read couldcube access key: '%s'" % AWS_KEY)
    AWS_SECRET = os.environ['CLOUDCUBE_SECRET_ACCESS_KEY']
    log.info("[HEROKU] read couldcube secret access key: '%s'" % AWS_SECRET)
    DEFAULT_WARCHAT_ID = int(os.environ['DEFAULT_WARCHAT'])
    log.info("[HEROKU] read default warchat_id: %d" % DEFAULT_WARCHAT_ID)
else:
    with open("TOKEN", "r") as tfile: # local run
        TOKEN = tfile.readline().strip('\n')
        log.info("[LOCAL] read token: '%s'" % TOKEN)
        tfile.close()
    with open("CLOUDCUBE_ACCESS_KEY_ID", "r") as f: # local run
        AWS_KEY = f.readline().strip('\n')
        log.info("[LOCAL] read couldcube access key: '%s'" % AWS_KEY)
        f.close()
    with open("CLOUDCUBE_SECRET_ACCESS_KEY", "r") as f: # local run
        AWS_SECRET = f.readline().strip('\n')
        log.info("[LOCAL] read couldcube secret access key: '%s'" % AWS_SECRET)
        f.close()
    with open("DEFAULT_WARCHAT", "r") as f: # local run
        DEFAULT_WARCHAT_ID = int(f.readline().strip('\n'))
        log.info("[LOCAL] read default warchat_id: %d" % DEFAULT_WARCHAT_ID)
        f.close()

bot = telebot.AsyncTeleBot(TOKEN)

aws_client = boto3.client('s3', aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET)

BOT_USERNAME = "assassinsgwbot"
ROOT_ADMIN = [] # creator
admins = {}

warchat_id        = DEFAULT_WARCHAT_ID
current_battle    = None
current_precheck  = None
current_arscheck  = None
current_numcheck  = None
current_cryscheck = None
current_snowwhite = {}
screen_message_list = []

import statistics
statistics = statistics.Statistic(cycle_time=4) # set 2 for first GW test

from settings.settings import PersistentSettings
settings = PersistentSettings()

#
# Manage admins list through file at start
#
# load initial list
with open("ADMINS", "r") as f:
    admins_list = json.load(f)
    ROOT_ADMIN = admins_list[0]
    admins = admins_list[1]
    f.close()
log.debug("Load root admin: ")
log.debug(ROOT_ADMIN)
log.debug("Load admins list: ")
log.debug(admins)

# save edited list
def SaveAdminsList(newlist):
    global ROOT_ADMIN, admins
    admins = newlist
    admins_list = [ROOT_ADMIN, admins]
    with open("ADMINS", "w") as f:
        json.dump(admins_list, f, ensure_ascii=False)
        f.close()
    log.debug("Saved admins list: ", admins_list)
    aws_admins_backup()


def aws_admins_backup(filename="GWBotAdmins.BAK", newlist=[], burst=False):
    """
    Backup current admins into pickle file.
    Upload to AWS
    @param burst Do not save backup to file
    """
    global ROOT_ADMIN, admins
    log.debug("AWS admins backup started")
    # if burst-upload requested (no additional file backup)
    if not burst:
        with open(filename, 'wb') as backup:
            admins = newlist
            admins_list = [ROOT_ADMIN, admins]
            pickle.dump(admins_list, backup, pickle.HIGHEST_PROTOCOL)
            backup.close()
    # upload file
    if hlp.AWSUploadFile(filename):
        log.debug("Admins has been successfully uploaded to AWS cloud.")
    else:
        log.error("Admins AWS upload failed.")

def aws_admins_restore(filename="GWBotAdmins.BAK", force=True):
    """
    Restore whole current admins from pickle file (download from AWS).
    @param force Remove old local backup
    """
    global ROOT_ADMIN, admins
    log.debug("AWS Admins restore started")
    try:
        # remove old admins backup if forced update
        if force:
            if os.path.isfile(filename):
                os.remove(filename)
        # download backup
        filepath = hlp.AWSDownloadFile(filename)
        if filepath == None:
            raise Exception("Admins AWS download failed.")
        log.debug("Admins has been successfully downloaded from AWS cloud.")
        # unwrap and set object
        with open(filepath, 'rb') as f:
            admins_list = pickle.load(f)
            ROOT_ADMIN = admins_list[0]
            admins = admins_list[1]
            f.close()
        log.debug("Restoring admins successful (AWS)")
    except Exception as err:
        log.error("Restoring admins failed (AWS): %s", str(err))
