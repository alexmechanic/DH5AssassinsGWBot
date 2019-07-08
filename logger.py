#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Gerasimov Alexander <samik.mechanic@gmail.com>
#

import logging, logging.config
CONFIG_FILE = "logConfig"

def get_logger(logger_name):
    logging.config.fileConfig(CONFIG_FILE)
    logger = logging.getLogger(logger_name)
    return logger
