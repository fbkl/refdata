#!/usr/bin/env python
# coding: utf-8

import os, sys
sys.path.append("../refdata")
from refdata import analyzer
from refdata.metrics import IMULump, MocapLump, get_roted, get_roted_from_claude_because_im_stupid
from importlib import reload

from refdata import my_log

results_dir = ""

get_roted_for_walking = get_roted_from_claude_because_im_stupid

#from refdata.metrics import change_do_rename

#change_do_rename()


def analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=None):
    my_log.CONTEXT = f"{subject_num} {this_action_name}"

    myImuLumpList = []
    myMocapLumpList = []

    global results_dir

    for g in action_data:
        gX = g["imu"]
        this_lump = IMULump( gX["ik"], "", "", "", "")
        myImuLumpList.append(this_lump)
        gX = g["mocap"]
        aMocapLump = MocapLump( gX["ik"], "", "", "", "")  
        myMocapLumpList.append(aMocapLump)

    print(myMocapLumpList[0])
    print(myImuLumpList[0])

    if not results_dir:
        results_dir = analyzer.graphs_and_metrics( myImuLumpList, myMocapLumpList, subject_num, weight, this_action_name, get_roted_fun= get_roted_fun )
    else:
        analyzer.graphs_and_metrics( myImuLumpList, myMocapLumpList, subject_num, weight, this_action_name, results_dir = results_dir, get_roted_fun=get_roted_fun)
    return results_dir


this_action_name = "walking"

if True:
    ######################### TRIAL INFO ##########################################

    subject_num="01"
    subject_vicon_num = "S1"
    weight= 99

    ###############################################################################
    from walking1 import walking as action_data

    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted_for_walking)

if True:
    ######################### TRIAL INFO ##########################################

    subject_num="02"
    subject_vicon_num = "S2"
    weight= 99

    ###############################################################################
    from walking2 import walking as action_data

    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted_for_walking)

if True:
    ######################### TRIAL INFO ##########################################

    subject_num="03"
    subject_vicon_num = "S3"
    weight= 99

    ###############################################################################
    from walking3 import walking as action_data

    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted_for_walking)
if True:
    ######################### TRIAL INFO ##########################################

    subject_num="04"
    subject_vicon_num = "S4"
    weight= 99

    ###############################################################################
    from walking4 import walking as action_data

    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted_for_walking)
if True:
    ######################### TRIAL INFO ##########################################

    subject_num="07"
    subject_vicon_num = "S5"
    weight= 99

    ###############################################################################
    from walking5 import walking as action_data

    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted_for_walking)

if True:
    ######################### TRIAL INFO ##########################################

    subject_num="08"
    subject_vicon_num = "S6"
    weight= 99

    ###############################################################################
    from walking6 import walking as action_data

    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted_for_walking)



