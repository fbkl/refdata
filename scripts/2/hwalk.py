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
        aMocapLump = MocapLump( gX["ik"], "", "", "", "") ## we cant parse the grf fromt the platform yet, if i have to do that i will cry. 
        myMocapLumpList.append(aMocapLump)

    print(myMocapLumpList[0])
    print(myImuLumpList[0])

    if not results_dir:
        results_dir = analyzer.graphs_and_metrics( myImuLumpList, myMocapLumpList, subject_num, weight, this_action_name, get_roted_fun= get_roted_fun )
    else:
        analyzer.graphs_and_metrics( myImuLumpList, myMocapLumpList, subject_num, weight, this_action_name, results_dir = results_dir, get_roted_fun=get_roted_fun)
    return results_dir

if True:
    ######################### TRIAL INFO ##########################################

    this_action_name = "walking"

    subject_num="EX01RE"
    subject_vicon_num = "EXS1"
    weight= 99

    ###############################################################################
    import walking1

    action_data = walking1.walking1
    results_dir = analysis_function(this_action_name, subject_num, subject_vicon_num, weight, action_data, get_roted_fun=get_roted_for_walking)


