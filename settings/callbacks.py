#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Callbacks for inline buttons in settings
#

from icons import *

SETTINGS_CALLBACK_PREFIX = "Settings_"
SETTINGS_BACK_CALLBACK   = SETTINGS_CALLBACK_PREFIX+"back"
SETTINGS_ON_CALLBACK     = SETTINGS_CALLBACK_PREFIX+"on"
SETTINGS_OFF_CALLBACK    = SETTINGS_CALLBACK_PREFIX+"off"

SETTINGS_START_CALLBACK_PREFIX = SETTINGS_CALLBACK_PREFIX+"start_"

SETTINGS_COMMON_CALLBACK       = SETTINGS_START_CALLBACK_PREFIX+"common_"

SETTINGS_COMMON_PIN_CALLBACK = SETTINGS_COMMON_CALLBACK+"pin"


SETTINGS_CHECKS_CALLBACK       = SETTINGS_START_CALLBACK_PREFIX+"checks_"

SETTINGS_CHECKS_PRECHECK_CALLBACK = SETTINGS_CHECKS_CALLBACK+"precheck_"

SETTINGS_CHECKS_BATTLE_CALLBACK   = SETTINGS_CHECKS_CALLBACK+"battle_"

SETTINGS_CHECKS_ARSENAL_CALLBACK  = SETTINGS_CHECKS_CALLBACK+"ars_"

SETTINGS_CHECKS_ARSENAL_CRIT_THRESHOLD_CALLBACK = SETTINGS_CHECKS_ARSENAL_CALLBACK+"critical_threshold"


SETTINGS_CHECKS_NUMBERS_CALLBACK  = SETTINGS_CHECKS_CALLBACK+"numbers_"

SETTINGS_CHECKS_CRYSTALS_CALLBACK = SETTINGS_CHECKS_CALLBACK+"crystals_"

SETTINGS_CHECKS_CRYSTALS_RANGES_CALLBACK = SETTINGS_CHECKS_CRYSTALS_CALLBACK+"ranges"


SETTINGS_STATISTIC_CALLBACK    = SETTINGS_START_CALLBACK_PREFIX+"statistic_"

SETTINGS_STATISTIC_BESTLIST_CALLBACK = SETTINGS_STATISTIC_CALLBACK+"bestlist"

SETTINGS_STATISTIC_NOMINATIONS_CALLBACK = SETTINGS_STATISTIC_CALLBACK+"nominations"

SETTINGS_STATISTIC_CYCLE_TIME_CALLBACK = SETTINGS_STATISTIC_CALLBACK+"cycletime"



