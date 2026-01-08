#!/usr/bin/env python
# coding: utf-8

import os, sys
sys.path.append("../refdata")
from refdata import analyzer
from refdata.metrics import IMULump, MocapLump, get_roted, get_roted0
from importlib import reload

from refdata import my_log

results_dir = ""

get_roted_for_sts_and_squat = get_roted0

def analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=None):
    my_log.CONTEXT = f"{subject_num} {this_action_name}"

    myImuLumpList = []
    myMocapLumpList = []
    myExtSync = []

    global results_dir

    for g in action_data:
        gX = g["imu"]
        this_lump = IMULump( gX["ik"], gX["grfL"], gX["grfR"], gX["id"], gX["so"])
        myImuLumpList.append(this_lump)
        gX = g["mocap"]
        aMocapLump = MocapLump( gX["ik"], "", "", gX["id"], gX["so"]) ## we cant parse the grf fromt the platform yet, if i have to do that i will cry. 
        myMocapLumpList.append(aMocapLump)

        myExtSync.append(g["ext_sync"])

    print(myMocapLumpList[0])
    print(myImuLumpList[0])

    if not results_dir:
        results_dir = analyzer.graphs_and_metrics( myImuLumpList, myMocapLumpList, subject_num, weight, this_action_name, ext_sync = myExtSync, get_roted_fun= get_roted_fun )
    else:
        analyzer.graphs_and_metrics( myImuLumpList, myMocapLumpList, subject_num, weight, this_action_name, results_dir = results_dir, ext_sync= myExtSync, get_roted_fun=get_roted_fun)
    return results_dir

if False:
    ######################### TRIAL INFO ##########################################

    this_action_name = "walking"

    subject_num="EX01RE"
    subject_vicon_num = "EXS1"
    weight= 53

    ###############################################################################
    import walking1

    action_data = walking1.walking1
    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted)


if False:
    reload(analyzer)
    ######################### TRIAL INFO ##########################################

    this_action_name = "walking"
    
    subject_num="EX02RE"
    subject_vicon_num = "EXS2"
    weight= 72

    ###############################################################################
    import walking2

    action_data = walking2.walking2
    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted)

if False:

    reload(analyzer)
    ######################### TRIAL INFO ##########################################

    this_action_name = "squat"

    subject_num="EX01RE"
    subject_vicon_num = "EXS1"
    weight= 53

    #############################################################################
    import squat1

    action_data = squat1.squat1
    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted_for_sts_and_squat)


if True:
    reload(analyzer)
    ######################### TRIAL INFO ##########################################

    this_action_name = "squat"

    subject_num="EX02RE"
    subject_vicon_num = "EXS2"
    weight= 72

    ###############################################################################
    import squat2

    action_data = squat2.squat2
    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted_for_sts_and_squat)


if False:
    reload(analyzer)
    ######################### TRIAL INFO ##########################################

    this_action_name = "sts"

    subject_num="EX01RE"
    subject_vicon_num = "EXS1"
    weight= 53

    ###############################################################################
    import sts1
    action_data = sts1.sts1
    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted_for_sts_and_squat)


if False:

    reload(analyzer)
    ######################### TRIAL INFO ##########################################

    this_action_name = "sts"

    subject_num="EX02RE"
    subject_vicon_num = "EXS2"
    weight= 72

    ###############################################################################
    import sts2
    action_data = sts2.sts2
    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted_for_sts_and_squat)

