#!/usr/bin/env python
# coding: utf-8

# # Graphs of GRF, Inverse Kinematics, Dynamics and SO from XIMU3 using ROS-OpenSIMRT 
# 
# # VICON REFERENCE DATA GENERATOR
# 
# 
# 
# ### NAME OF ACTIVITY: walking
# 
# 
# 
# # THIS IS VICON
# 
# we have only a limited number of steps here. it would be nice to have more steps, at least for IK, we can do that. for ID it would be limited. For SO, since we are comparing with EMG, then we could also have more steps
# 
# I didn't figure out how to plot the GRFs so I haven't done that yet. We are not plotting them in the paper, so I don't think it matters.
# 
# 
# 
# 
# ## ROT_STRING
# 

import os, sys
sys.path.append("/mnt/github/github/refdata")
from refdata.files import sort_files, construct_new_names, rename_trials
from refdata import refdata
import numpy as np
import matplotlib.pyplot as plt
from importlib import reload

import glob
import logging
reload(logging)
from rich.logging import RichHandler
logging.basicConfig(format='%(funcName)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', 
                    handlers=[RichHandler()],
                    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import pprint
def myprint(var):
    nicevar = pprint.pformat(globals()[var], indent=1 , width=100)
    logger.debug(f"{var}:\n{nicevar}")


def myprint2(var):
    logger.debug(f"{var}:\n{globals()[var]}")
    
refdata.plt.rcParams['figure.figsize'] = [12, 5]
refdata.ROW_OF_FLOTS = 1

######################### TRIAL INFO ##########################################

this_action_name = "walking"
##Edit next line to select at least this action!
actions_to_be_shown = [ "walking" ]
#['walk','gait','slow','fast']

weight= "not informed"
conv_names = refdata.graph_params.get_ik_graph_params()
myprint("conv_names")

skip_trials =[]

###############################################################################
def time_clips_from_frame_clips(time, trial, steps_list, fos):
    def this_clamp(some_step):
        
        stepi = int(some_step-fos)
        a = 0
        if stepi>=0 and stepi<=len(time):
            a = time[stepi]
        elif stepi>len(time):
            a = time.iat[-1]*2
        return a
    new_step_list = []
    #print(steps_list)
    for step in steps_list:
        #print(step)
        new_step_list.append([this_clamp(step[0]),this_clamp(step[1])])

    return {trial:new_step_list}



subject_dict = {
    "S1": 
    {
            "xy_frame_clippings_left": {
                "ik_walking1.mot":[[408,515],[515,627],[627,735],[736,1675]],
                "ik_walking3.mot":[[420,529],[529,636],[636,735]],
                "ik_walking5.mot":[[100,210],[736,1675]],
                },
            "xy_frame_clippings_right": {
                "ik_walking1.mot":[[460,572],[572,680],[680,790],[790,1675]],
                "ik_walking3.mot":[[475,584],[584,692],[710,735]],
                "ik_walking5.mot":[[46,158],[158,265],[736,1675]],
                },
            "frame_offsets": [
                    368,
                    386,
                    0,
                    ],
            "butchered_clipping": []
    },
    "S2": 
    {
            "xy_frame_clippings_left": {
                "ik_walking1.mot":[[25,135],[215,627]],
                "ik_walking3.mot":[[52,159],[159,269],[269,636]],
                "ik_walking5.mot":[[48,157],[736,1675]],
                },
            "xy_frame_clippings_right": {
                "ik_walking1.mot":[[79,187],[215,627]],
                "ik_walking3.mot":[[0,106],[106,212],[269,636]],
                "ik_walking5.mot":[[0,104],[104,208],[736,1675]],
                },
            "frame_offsets":[
                    0,
                    0,
                    0,
                    ],
            "butchered_clipping": []
    },
    "S3": 
    {
            "xy_frame_clippings_left": {
                "ik_walking1.mot":[[0,10000],[515,627]],
                "ik_walking2.mot":[[0,10000],[529,636]],
                "ik_walking3.mot":[[0,100000],[736,1675]],
                },
            "xy_frame_clippings_right": {
                "ik_walking1.mot":[[0,10000],[572,680]],
                "ik_walking2.mot":[[0,100000],[584,692]],
                "ik_walking3.mot":[[0,100000],[158,265]],
                },
            "frame_offsets": [
                    0,
                    0,
                    0,
                    ],
            "butchered_clipping": [[[],[0],[]],[[0],[],[0]]] ## left and right, then by the list of trials, if it is empty dont do anything, if there is something, then shift that step by half
            #"butchered_clipping": [[[],[],[0]],[[],[0],[0]]] ## left and right, then by the list of trials, if it is empty dont do anything, if there is something, then shift that step by half
    },
    "S4": 
    {
            "xy_frame_clippings_left": {
                "ik_walking5.mot":[[42,160],[515,627]],
                "ik_walking7.mot":[[24,142],[529,636]],
                "ik_walking9.mot":[[52,172],[736,1675]],
                },
            "xy_frame_clippings_right": {
                "ik_walking5.mot":[[100,218],[572,680]],
                "ik_walking7.mot":[[80,200],[584,692]],
                "ik_walking9.mot":[[112,230],[458,265]],
                },
            "frame_offsets":[
                    0,
                    0,
                    0,
                    ],
            "butchered_clipping": []
    },
    "S5": 
    {
                "xy_frame_clippings_left": {
                    "ik_walking5.mot":[[125,251],[736,1675]],
                    "ik_walking6.mot":[[7,132],[132,255],[736,1675]],
                    "ik_walking7.mot":[[0,120],[120,245],[736,1675]],
                    },
               "xy_frame_clippings_right": {
                    "ik_walking5.mot":[[62,188],[188,312],[572,680],],
                    "ik_walking6.mot":[[70,194],[194,320],[584,692],],
                    "ik_walking7.mot":[[60,182],[182,300],[400,440]],
                    },
               "frame_offsets" :[
                        0,
                        0,
                        0,
                        ],
            "butchered_clipping": []
    },
    "S6": 
    {
            "xy_frame_clippings_left": {
                "ik_walking1.mot":[[0,120],[120,235],[515,627]],
                "ik_walking2.mot":[[115,243],[529,636]],
                "ik_walking4.mot":[[0,125],[125,253],[736,1675]],
                },
            "xy_frame_clippings_right": {
                "ik_walking1.mot":[[57,177],[572,680]],
                "ik_walking2.mot":[[53,176],[176,300],[584,692]],
                "ik_walking4.mot":[[60,186],[186,313],[358,1265]],
                },
            "frame_offsets": [
                    0,
                    0,
                    0,
                    ],
            "butchered_clipping": []
    },

}


for subject_num in ["S1","S2","S3","S4","S5","S6"]:
#for subject_num in ["S3"]:

    xy_frame_clippings_left_ = subject_dict[subject_num]["xy_frame_clippings_left"]
    xy_frame_clippings_right_ = subject_dict[subject_num]["xy_frame_clippings_right"]
    frame_offsets = subject_dict[subject_num]["frame_offsets"]
    butchered_clipping = subject_dict[subject_num]["butchered_clipping"]
    xy_frame_clippings_left = {}
    xy_frame_clippings_right = {}
    xy_time_clippings_left = {}
    xy_time_clippings_right = {}

    for items, keys in xy_frame_clippings_left_.items():
        xy_frame_clippings_left.update({f"{subject_num}/{items}":keys})
    for items, keys in xy_frame_clippings_right_.items():
        xy_frame_clippings_right.update({f"{subject_num}/{items}":keys})

    ik_files=[]
    for ik_file in glob.glob(f"{subject_num}/ik_wa*.mot"):
        ik_files.append(ik_file)
    ik_files=sorted(ik_files)
    myprint("ik_files")


    action_trials= []
    for trial in ik_files:
        for action_name in actions_to_be_shown:
            if action_name in trial:
                action_trials.append(trial)

    xy_knees_ik = refdata.generate_somejoint_or_muscle_curves(action_trials,[], curve_prefix="ankle_angle",conv_names=conv_names)

    for (name, xy_tuples), fos in zip(xy_knees_ik[0].items(),frame_offsets):    
        for action_name in actions_to_be_shown:
            if action_name in name:
                print(name+r" left")        
                this_dic = time_clips_from_frame_clips(xy_tuples[0],name, xy_frame_clippings_left[name],fos)
                xy_time_clippings_left.update(this_dic)
            
    for (name, xy_tuples), fos in zip(xy_knees_ik[1].items(),frame_offsets):
        for action_name in actions_to_be_shown:
            if action_name in name:
                print(name+r" right")        
                this_dic = time_clips_from_frame_clips(xy_tuples[0],name, xy_frame_clippings_right[name],fos)
                xy_time_clippings_right.update(this_dic)

    xy_clippings_both_ik = (xy_time_clippings_left,xy_time_clippings_right)
    
    cdata = refdata.graph_params.get_ik_graph_params()
    cdata['pelvis_rotation']['axes_limits'] = [-360, 360]

    refdata.logger.setLevel(logging.ERROR)
    cdata = refdata.graph_params.get_ik_graph_params()
    if True:
        #### so the names here will be completely wrong because of the frame of reference correction and whether the person is coming or going in the lab frame. this was suuuuuper easy to fix btw.
        cdata['pelvis_tilt']['axes_limits'] = [-20, 20]
        cdata['pelvis_list']['axes_limits'] = [-20, 60]
        cdata['pelvis_rotation']['axes_limits'] = [-20, 20]
        ### vicon origin is incorrect! but this doesnt work, we need to update the generated curves
        cdata['pelvis_tilt']['name'] = 'Pelvic_Up_Dn'
        cdata['pelvis_list']['name'] = 'Pelvis_Ant_Pst'
        cdata['pelvis_tilt']['title'] = "Pelvic Obliquity"
        cdata['pelvis_list']['title'] = "Pelvic Tilt"
        cdata['pelvis_tilt']['position'] = [0,1]
        cdata['pelvis_list']['position'] = [0,0]

        ## why is it inverted?
        cdata['hip_rotation']['scale'] =(-1, 57.29578960935126)
    else:
        cdata['pelvis_tilt']['axes_limits'] = [-360, 360]
        cdata['pelvis_list']['axes_limits'] = [-360, 360]
        cdata['pelvis_rotation']['axes_limits'] = [-360, 360]
    all_ik_curves_for_this_person = refdata.generate_action_plots(action_trials, 
                    xy_clippings_both_ik, ref=None, #refdata.GaitIKRefData(),
                    skip_trials=skip_trials,
                    action=this_action_name, include_actions=actions_to_be_shown,
                    conv_names=cdata,
                    butchered_clipping=butchered_clipping)
    RR = refdata.plot_std_plots(all_ik_curves_for_this_person, plot_std=False,
                                ref=refdata.GaitIKRefData(),
                                subplot_grid = (3,3),
                                subject_identifier=f"Vicon Ref{subject_num}")

    plt.savefig(f'{subject_num}_ik_{this_action_name}3x3_tighter_stds.pdf', bbox_inches = 'tight')
    asRefData = refdata.RefData(this_action_name)
    asRefData.reference_curve_dict = RR[4]

    import pickle

    pickle.dump( asRefData, open( f"ik_ref_{this_action_name}_data_s{subject_num}.p", "wb" ) )

    _filename = f"{subject_num}_{this_action_name}_allcurves.pkl"

    subject_complete_filename = os.path.join(_filename)
    print(subject_complete_filename)
    f = open(subject_complete_filename,"wb")
    pickle.dump(all_ik_curves_for_this_person,f)
    f.close()

