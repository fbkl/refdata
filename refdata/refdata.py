#!/bin/env python3
#from https://wwrichard.net/2014/09/02/do-it-yourself-normative-data-comparison-free-download/
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from mpl_toolkits.axes_grid1 import Divider, Size,  make_axes_locatable
from importlib.metadata import version
import os
import traceback
from . import graph_params
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def check_ver(package, ver_requirements):
    ver_requirements_list = ver_requirements.split('.')
    ver_list = version(package).split('.')
    major = ver_list[0]
    minor = ''
    other = ''
    if len(ver_list)>1:
        minor = ver_list[1]
    if len(ver_list)>2:
        other = ver_list[2:]
    if int(major)<int(ver_requirements_list[0]) or int(minor)<int(ver_requirements_list[1]):
        raise Exception(f"requirements for {package} not met need {ver_requirements}, have {'.'.join(ver_list)}")
        
check_ver('matplotlib', "3.8")

def check_data(data_dir):
    dirs_to_check = ["grf_data","id_data","so_data","ik_data"]
    for some_dir in dirs_to_check:
        if not os.path.exists(os.path.join(data_dir,some_dir)):
            raise Exception(f"source data {some_dir} not found. graph generation with references will fail")
    logger.info("data found okay!")

check_data(os.path.join(os.path.dirname(__file__),"../data"))

import numpy as np
import glob
from numpy import matlib 
from scipy import interpolate
from scipy import signal
from scipy.signal import argrelextrema
from scipy.interpolate import PchipInterpolator
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import os


##Setting graphing parameters
ROW_OF_FLOTS=15

def set_graph_params(
    SMALL_SIZE = 12,
    MEDIUM_SIZE = 18,
    BIGGER_SIZE = 22,
        ):

    matplotlib.rc('text', usetex = True)
    matplotlib.rc('font', **{'family' : "sans-serif"})
    #params = {'text.latex.preamble' : [r'\usepackage{siunitx}', r'\usepackage{sfmath}']}
    fontProperties = {'family':'sans-serif', 'weight': 'normal', 'size': 12}
    #plt.rcParams.update(params)

    plt.rc('text.latex', preamble=r'\usepackage{cmbright}')
    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', titlesize=MEDIUM_SIZE)     # fontsize of the axes title
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
    #plt.rcParams['figure.figsize'] = [12, 6]
    #plt.rcParams['figure.dpi'] = 400 # 200 e.g. is really fine, but slower

set_graph_params()


#plot_ref_id("ankle")

def load_reference_ik_data():
    module_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(module_dir,"..","data","ik_data", "IK_REFERENCES_PAPER.csv")
    return pd.read_csv(csv_file_path, skiprows=1)

class RefDataPrimitive:
    def __init__(self):
        self.name = ""
        self.x = None
        self._mean = None
        self._sd = None
        self._Y = None
        self.scale = (1,1)
    def __repr__(self):
        return f"RefDataPrimitive(): {self.name} "
    def __str__(self):
        return f"RefDataPrimitive():\n name: {self.name}\n x: {self.x}\n mean: {self.mean}\n sd: {self.sd}"
    @property
    def sd(self):
        if self._Y is None:
            return self._sd
        else:
            ## calculate the sd from Y
            #logger.error("not implemented yet!")
            return self._Y.std(axis=0)

    @sd.setter
    def sd(self, value):
        if self._Y is None:
            self._sd = value
        else:
            logger.error("cannot set standard deviation on a reference data type that has raw Y data already defined!")

    @property
    def mean(self):
        if self._Y is None:
            return self._mean
        else:
            ## calculate mean from Y
            #logger.error("not implemented yet!")
            return self.scale[0]*self._Y.mean(axis=0)

    @mean.setter
    def mean(self, value):
        if self._Y is None:
            self._mean = value
        else:
            logger.error("cannot set mean value on a reference data type that has raw Y data already defined!")

    @property
    def Y(self):
        return self._Y

    @Y.setter
    def Y(self,value):
        self._Y = value

    def appendYcurves(self, x, y):
        if len(x) == 0:
            raise(ValueError("x cannot be empty, actually, it maybe could be and i would infer it from the length, but alas"))
        nmaxX = np.max([len(self.x), len(x)])
        newx = np.linspace(0,100,nmaxX)
        newselfY = interpolate.pchip_interpolate(self.x , self._Y   , newx, axis=1)
        newnewY  = interpolate.pchip_interpolate(x      , y         , newx, axis=1)
        ## it seems it is correct. moving to debug
        logger.debug("now figure out if the concatenation is correct!")
        self.x = newx
        self._Y = np.concatenate((newselfY, newnewY), axis=0)
        assert(len(self.x) == self._Y.shape[1])
    def appendPrimitive(self, otherPrim):
        self.appendYcurves(otherPrim.x, otherPrim.Y)
        self.name += otherPrim.name

def repeat_x(x_, n_times):
    x = x_
    STARTS_AT_ZERO = False
    if STARTS_AT_ZERO:
        x_zero_increment = x_[1]-x_[0]
    else:
        x_zero_increment = 0
    for i in range(n_times-1):

        x = np.hstack((x, x_+np.max(x)+x_zero_increment))
    return x

class RefData:
    def __init__(self, action_type):
        self.action_type = action_type
        self.reference_curve_dict = {}
        self.plot_2_sd = False

    def plot(self, reference_name_name= "all"):

        if reference_name_name == "all":
            reference_name_name = []
            for reference_name, _ in self.reference_curve_dict.items():
                reference_name_name.append(reference_name)

        if isinstance(reference_name_name,list):
            for reference_name in reference_name_name:
                self.plot_reference_name(reference_name)
        if isinstance(reference_name_name,str):
            self.plot_reference_name(reference_name_name)

    def get_curve_y(self, y_in, x, xnew, num_cycles,scale, inverted=False ):
        y   = np.tile(y_in,num_cycles+4)
        logger.debug(len(y))
        fy =  interpolate.interp1d(x,y)
        ynew = fy(xnew)
        Y = ynew*scale
        if inverted:
            return -Y
        return Y

    def get_curve_x(self, ik_id_so_i, x_offset, num_cycles,scale ):
        x   = repeat_x(ik_id_so_i.x,num_cycles+4)
        logger.debug(x)
        logger.debug("lenx %d"%len(x))
        xnew = np.arange(x_offset%360, 100*num_cycles+x_offset%360, 1)
        logger.debug(xnew)
        X =(xnew-x_offset)*scale
        return X,x, xnew

    def get_reference_name_curve(self, reference_name, num_cycles=4,scale=[1,1], inverted=False):
        x_offset = 0

        X_list = []
        Y_list = []
        for ik_id_so_i in self.reference_curve_dict[reference_name]:
            logger.debug(ik_id_so_i)
            X,x, xnew = self.get_curve_x(ik_id_so_i, x_offset, num_cycles,scale[0] )
            Y = self.get_curve_y(ik_id_so_i.mean, x, xnew, num_cycles,scale[1], inverted=inverted)
            X_list.append(X)
            Y_list.append(Y)

        return X_list,Y_list

    def plot_reference_name(self, reference_name, num_cycles=4,scale=[1,1], avg_line=True, inverted = False, ax = None, alpha_=0.9, remove_initial_offset=False): 
        """
        reference_name: is the name of the reference reference_name to be plotted
        num_cycles: is an integer

        """
        logger.debug("plotting reference!")
        if not ax:
            fig = plt.figure()
            ax = plt.gca()

        if not self.reference_curve_dict:
            logger.warning("reference curve dictionary not set!")
            return
        #plt.figure()
        #plt.title(reference_name)

        x_offset = 0
        suffix = ""
        if remove_initial_offset:
            suffix = "*"
            print("TRIGGERED REMOVE INITIAL OFFSET IN REFDATA")
        else:
            print("DID NOT trigger remove initial offset in RefData!!!")
        #num_cycles = num_cycles_+4
        if reference_name in self.reference_curve_dict:
            ik_id_so_i = self.reference_curve_dict[reference_name][0]
        #for ik_id_so_i in self.reference_curve_dict[reference_name]:

            X,x, xnew = self.get_curve_x(ik_id_so_i, x_offset, num_cycles,scale[0])
            logger.debug("leny %d"%len(ik_id_so_i.mean))
            Y = self.get_curve_y(ik_id_so_i.mean, x, xnew, num_cycles,scale[1])
            YP = self.get_curve_y(ik_id_so_i.mean+ik_id_so_i.sd, x, xnew, num_cycles,scale[1])
            YM = self.get_curve_y(ik_id_so_i.mean-ik_id_so_i.sd, x, xnew, num_cycles,scale[1])
            Y2P = self.get_curve_y(ik_id_so_i.mean+2*ik_id_so_i.sd, x, xnew, num_cycles,scale[1])
            Y2M = self.get_curve_y(ik_id_so_i.mean-2*ik_id_so_i.sd, x, xnew, num_cycles,scale[1])
            
            if remove_initial_offset:
                YP-=Y[0]
                YM-=Y[0]
                Y2P-=Y[0]
                Y2M-=Y[0]
                Y-=Y[0]

            if inverted:
                YP = -YP
                YM = -YM
                Y2P = -Y2P
                Y2M = -Y2M
                Y = -Y

            if avg_line:
                ax.plot(X, Y, "-", label="{} mean".format(ik_id_so_i.name)+suffix)
            if self.plot_2_sd:

                print("plotting 2sds!")
                ax.fill_between(X,Y2P, Y2M, alpha=alpha_, label= "{} 2 std ".format(ik_id_so_i.name)+suffix,  linewidth=1, color="lightgray")
                if avg_line:
                    ax.plot(X, Y2P, "-", label="{} sd+2".format(ik_id_so_i.name)+suffix)
                    ax.plot(X, Y2M, "-", label="{} sd-2".format(ik_id_so_i.name)+suffix)
            else:
                print("plotting 1sd!")
                if avg_line:
                    ax.plot(X, YP, "-", label="{} sd+1".format(ik_id_so_i.name)+suffix)
                    ax.plot(X, YM, "-", label="{} sd-1".format(ik_id_so_i.name)+suffix)
                ax.fill_between(X,YP, YM, alpha=alpha_, label= "{} 1 std ".format(ik_id_so_i.name)+suffix,  linewidth=1, color="gray")


        else:
            logging.warn("I dont have the reference %s"%reference_name)
        #plt.legend()
        #plt.show()            
    def append_curves(self,otherRefData):
        try:
            assert(set(self.reference_curve_dict.keys()) == set(self.reference_curve_dict.keys()))
        except:
            logger.error("You have different types of reference curves. If you want to add only the ones that are the same, you have to change this function to do like an intersecion and loop over that to add it. Out of scope right now")
        for reference_name in self.reference_curve_dict:

            if len(otherRefData.reference_curve_dict[reference_name])>1 or len(self.reference_curve_dict[reference_name])>1:
                logger.warning("im always rushing, so I won't support multiple different references in the same obnject right now. i cant even imagine what you are trying to do anyway. do it manually")
                raise(Exception("complicated reference dict situation here, wtf."))
            otherRefPrimitive = otherRefData.reference_curve_dict[reference_name][0]
            #self.reference_curve_dict[reference_name][0].appendYcurves(otherRefPrimitive.x, otherRefPrimitive.Y)
            self.reference_curve_dict[reference_name][0].appendPrimitive(otherRefPrimitive)
        logger.info("Extended references OK.")

def latex_friendly_column_names(name):
    name = name.replace(" ", "_")
    name = name.replace("/","_")
    return name

## newer function loading the whole xlsx file
class GaitNormativeRefData(RefData):
    def __init__(self, own_action_name="gait"):
        RefData.__init__(self,own_action_name)
    def set_from_sheet(self, sheet_name=None):
        if not sheet_name:
            raise(ValueError("need sheet_name"))
        module_dir = os.path.dirname(os.path.abspath(__file__))
        xlsx_file_path = os.path.join(module_dir,"..","data","normative-dataset-comparison.xlsx")
        
        ik_names = {}
        index_name="'Gait_percentage'"
        
        df = pd.read_excel(io=xlsx_file_path, sheet_name=sheet_name,  header=[0,1], 
                   index_col=[0,1], )
        
        unique_movement_names = list(set(df.index.get_level_values(0)))
        latex_friendly_names = [latex_friendly_column_names(name) for name in unique_movement_names]
        
        
        for movement_name, friendly_movement_name in zip(unique_movement_names,latex_friendly_names):
            
            self.reference_curve_dict.update({friendly_movement_name:[RefDataPrimitive(),RefDataPrimitive()]})
            
            for col in df.columns:
                ik_index = None
                if col[0] == 'Your data':
                    continue
                if 'one' in col[0]:
                    ik_index = 0
                if 'two' in col[0]:
                    ik_index = 1
                logger.debug(col, movement_name, ik_index)

                self.reference_curve_dict[friendly_movement_name][ik_index].name = col[0]    


                if col[1] == 'Average':
                    self.reference_curve_dict[friendly_movement_name][ik_index].mean = df[col][movement_name].values
                    self.reference_curve_dict[friendly_movement_name][ik_index].x = 100*np.array(df[col][movement_name].index)
                    logger.debug(self.reference_curve_dict[friendly_movement_name][ik_index].x)
                if col[1] == 'SD':
                    self.reference_curve_dict[friendly_movement_name][ik_index].sd = df[col][movement_name].values
                

class GaitIKRefData(GaitNormativeRefData):
    def __init__(self, action="gait"):
        GaitNormativeRefData.__init__(self, action)
        self.set_from_sheet(sheet_name=u"Joint Rotations")
    #def plot_reference_name(self, reference_name, scale=[], num_cycles = 0, avg_line=False, ax=None):
    #    pass

class GaitIDRefData(GaitNormativeRefData): ## name is not following conventions,
        def __init__(self, action="gait"):
            GaitNormativeRefData.__init__(self, action)
            self.set_from_sheet(sheet_name=u"Joint Moments")
            ## but the names on the sheet are inconsistent, so we need to change the dictionary keys
            dict_map = {'Ankle_Rotation_Moment':'Foot_Int_Ext',
                    'Hip_Extensor_Moment_':'Hip_Flx_Ext',
                    'Knee_Abductor_Moment_':'Knee_Abductor_Moment_',
                    'Hip_Abductor_Moment_':'Hip_Add_Abd',
                    'Plantarflexor_Moment_':'Ankle_Dor_Pla',
                    'Knee_Extensor_Moment_':'Knee_Flx_Ext'
                    }
            new_dict = {}
            for key, value in self.reference_curve_dict.items():
                new_dict.update({dict_map[key]:self.reference_curve_dict[key]})
            self.reference_curve_dict = new_dict



class GaitPowerRefData(GaitNormativeRefData):
        def __init__(self, action="gait"):
            GaitNormativeRefData.__init__(self, action)
            self.set_from_sheet(sheet_name=u"Joint Power")

class IdData(RefData):
    def __init__(self, action=""):
        RefData.__init__(self, action)
    #def plot_reference_name(self, reference_name, scale=[], num_cycles = 0, avg_line=False, ax=None):
    #    pass

def IdGaitData(action="gait"): ## name is not following conventions,
    logging.warn("name changed to follow conventions, use GaitIDRefData instead")
    return GaitIDRefData(action=action)

##TODO: I am not being consistent with the names here
class SoData(RefData):
    def __init__(self, action=""):
        RefData.__init__(self, action)

    def plot_reference_name(self,reference_name,scale=[1/99,1], num_cycles=1, avg_line=False, ax=None,**kwargs):
        pass

def detect_pelvis_rotation(clipped_curve,pelvis_rotation,l_r, pelvis_joint_name, pelvis_plot_only_right_side ):
    #coming and going offset
    offset = 90 ## or pi/2 ?
    #print(l_r)
    #side = 1
    #if l_r:
    #    side= -1

    

    for i,(clip, pelv) in enumerate(zip (clipped_curve, pelvis_rotation)): 
        average_rotation_angle_is_negative = pelv[1].mean() < 0
        zero_curve = (clipped_curve[i][0], clipped_curve[i][0]*np.nan)
        defined = False
        if pelvis_joint_name == "pelvis_tilt":
            if average_rotation_angle_is_negative:
                if l_r:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] )
                    #print(clipped_curve[i][1])
                    defined = True
                elif pelvis_plot_only_right_side:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], -clipped_curve[i][1] )
                    #print(clipped_curve[i][1])
                    defined = True
            else:
                if l_r:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], -clipped_curve[i][1] )
                    #print(clipped_curve[i][1])
                    defined = True
                elif pelvis_plot_only_right_side:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] )
                    #print(clipped_curve[i][1])
                    defined = True


        elif pelvis_joint_name == "pelvis_list":
            if average_rotation_angle_is_negative:
                if l_r:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], -clipped_curve[i][1] )
                    #print(clipped_curve[i][1])
                    defined = True
                elif pelvis_plot_only_right_side:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], -clipped_curve[i][1] )
                    #print(clipped_curve[i][1])
                    defined = True
            else:
                if l_r:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] )
                    #print(clipped_curve[i][1])
                    defined = True
                elif pelvis_plot_only_right_side:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] )
                    #print(clipped_curve[i][1])
                    defined = True
        elif pelvis_joint_name == "pelvis_rotation":
            if average_rotation_angle_is_negative:
                if l_r:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] + 90)
                    #print(clipped_curve[i][1])
                    defined = True
                elif pelvis_plot_only_right_side:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], -clipped_curve[i][1] - 90)
                    #print(clipped_curve[i][1])
                    defined = True
            else:
                if l_r:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] - 90)
                    #print(clipped_curve[i][1])
                    defined = True
                elif pelvis_plot_only_right_side:
                    #clipped_curve[i] = (clipped_curve[i][0], clipped_curve[i][1] +offset)
                    clipped_curve[i] = (clipped_curve[i][0], -clipped_curve[i][1] + 90 )
                    #print(clipped_curve[i][1])
                    defined = True
        else: 
            print(f"WTF!!!")
        if not defined:
            print("not defined!")
            if average_rotation_angle_is_negative:
                print("normal case")
            else:
                print("other case!")
            print(f"{average_rotation_angle_is_negative}, {l_r}, {pelvis_joint_name}")
            clipped_curve[i] = zero_curve

    return clipped_curve


def generate_action_plots(action_trials_, xy_clippings_both, skip_trials=[], ref=GaitIKRefData(),
        conv_names=None, include_actions=[], action=None, curve_suffix="", use_absolute_times=False, butchered_clipping=[], combine_sides=True, pelvis_plot_only_right_side=False):
    all_curves_for_this_person = {}

    for l_r, clips in enumerate(xy_clippings_both):
        for i_file,(file, which_clippings) in enumerate(clips.items()):
            try:
            #for i_file, file in enumerate(action_trials):
                this_action_name = ""
                logger.debug(i_file)
                logger.debug(skip_trials)
                matching_actions = [action_name for action_name in include_actions if action_name in file]
                if not matching_actions or i_file in skip_trials :
                    logger.warning("skipping file: %s"%file)
                    continue
                elif len(matching_actions) >1:
                    raise ValueError("More than one action in the specified file name!")
                else:
                    if action:
                        this_action_name= action
                    else:
                        this_action_name = matching_actions[0]
                this_trial = TrialData(file, remove_time_offset=use_absolute_times)

                data = this_trial.data

                for joint_or_muscle_name, ref_name in conv_names.items():

                    logger.debug(f"trying to find {joint_or_muscle_name}")
                    if joint_or_muscle_name+curve_suffix in data.columns:
                        joint_or_muscle_name_suffix = ["",""]
                    elif joint_or_muscle_name+"_l"+curve_suffix in data.columns and joint_or_muscle_name+"_r"+curve_suffix in data.columns:
                        joint_or_muscle_name_suffix = ["_l","_r"]
                    else:
                        logger.error(f"Could not find {joint_or_muscle_name} in source data!")
                        continue ## I think...
                    if ref_name["plot_it"]:
                        logger.debug(joint_or_muscle_name_suffix)
                        joint_or_muscle_complete_name = joint_or_muscle_name+joint_or_muscle_name_suffix[l_r]+curve_suffix
                        if not joint_or_muscle_complete_name in all_curves_for_this_person.keys():
                            all_curves_for_this_person.update({joint_or_muscle_complete_name:([],"","")})

                        side = l_r
                        if ("pelvis" in joint_or_muscle_complete_name or "lumbar" in joint_or_muscle_complete_name) and combine_sides :
                            side = -1
                            logger.debug(xy_clippings_both[1])
                        #    which_clippings = xy_clippings_both[1][file]
                        #else:
                            logger.debug(xy_clippings_both[l_r])
                        #    which_clippings = xy_clippings_both[l_r][file]

                        pelvic_tilt_flipper = 1 ## we need this because the pelvis ik is a special case,
                        

                        clipped_curves = clip_curve(
                                data["time"],
                                data[joint_or_muscle_complete_name]*ref_name["scale"][1]+ref_name["offset"],
                                time_clips = which_clippings )

                        corrected_clipped_curves = clipped_curves
                        if "pelvis"  in joint_or_muscle_complete_name:
                            logger.warning("ATTENTION: ASSUMING THAT I AM IK DATA AND ATTEMPTING FLIPS!")
                            logger.debug(joint_or_muscle_complete_name)
                            ##TODO: this will fail in other models that are not the 1992/2392/2354 etc
                            pelvis_rot_ref = conv_names["pelvis_rotation"] ## i want the signal without any changes here??
                            clipped_pelvis_rotation_raw = clip_curve(
                                data["time"],
                                data["pelvis_rotation"],
                                time_clips = which_clippings )
                            corrected_clipped_curves = detect_pelvis_rotation(clipped_curves, clipped_pelvis_rotation_raw,l_r, joint_or_muscle_complete_name, pelvis_plot_only_right_side)


                        
                        
                        xi,  curves = reshape_curves(normalize_steps(corrected_clipped_curves))

                        list_of_curves = all_curves_for_this_person[joint_or_muscle_complete_name][0]
                        #import pickle
                        #pickle.dump((xi,curves), open("/tmp/arg.p","wb"))

                        if len(butchered_clipping) > 0 and len(butchered_clipping[l_r]) >= i_file and len(butchered_clipping[l_r][i_file]) >0:
                            curves[butchered_clipping[l_r][i_file]] = np.roll(curves[butchered_clipping[l_r][i_file]], len(xi)//2,axis=1)

                        list_of_curves.append((xi,curves))
                        logger.debug(f"list of curves for {joint_or_muscle_name}: {list_of_curves}")
                        ##define side for plot:
                        #if joint_or_muscle_suffix:
                        #    side = l_r
                        #else: ## pelvis or lumbar joints
                        #    side = -1
                        all_curves_for_this_person.update({joint_or_muscle_complete_name:(list_of_curves, ref_name,side)})
                        logger.debug(f"I believe I have added {joint_or_muscle_name}")

            except:
                traceback.print_exc()
                logger.warning("failed in %s"%i_file)
                pass
    if all_curves_for_this_person == {}:
        logger.error("No curves generated! Check source data")
    return all_curves_for_this_person

def generate_gait_plots(gait_trials,xy_clippings_both, **kwargs):
    return generate_action_plots(gait_trials, xy_clippings_both, action="gait", include_actions= ["gait", "walk", "fast","slow"], **kwargs)

def remove_repeated(handles, labels):
    nh = []
    nl = []
    logger.debug(labels)
    for h, l in zip(handles, labels):
        if not l in nl:
            nl.append(l)
            nh.append(h)
    logger.debug(nl)
    try:
        nh, nl = zip(*sorted(zip(nh, nl), key=lambda x: x[1]))
    except:
        pass
    return nh, nl

def actual_plot(X,Y,ax,side, plot_std, steps_label= "{}steps 1-{}",change_x_ticks=True, use_color_cycle=True, remove_initial_offset=False):
    colorspace_range = len(Y)
    cycle_begin = 1
    if use_color_cycle:
        cycle_begin = 0.5
    cycle_end = 1
    if side == 0:
        mean_color = "red"
        std_p = "darkred"
        std_m = "firebrick"
        mean_name = "Left "
        #color_cycle = plt.cm.copper(np.linspace(0,1,len(Y)+2))
        color_cycle = plt.cm.Reds(np.linspace(cycle_begin,cycle_end,colorspace_range))
    elif side == 1:
        mean_color = "blue"
        std_p = "darkblue"
        std_m = "navy"
        mean_name = "Right "
        #color_cycle = plt.cm.cool(np.linspace(0,1,len(Y)+2))
        color_cycle = plt.cm.Blues(np.linspace(cycle_begin,cycle_end,colorspace_range))
    elif side == -1:
        mean_color = "green"
        std_p = "darkgreen"
        std_m = "seagreen"
        mean_name = ""
        logger.debug("greeen")
        #color_cycle = plt.cm.winter(np.linspace(0,1,len(Y)+2))
        color_cycle = plt.cm.Greens(np.linspace(cycle_begin,cycle_end,colorspace_range))
    else:
        raise Exception("side does not have a color defined!")
    
    if plot_std:
        logger.debug(mean_name)
        logger.debug("Mean{}".format(mean_name))
        y_mean = Y.mean(axis=0)
        this_mean_label ="{}Mean".format(mean_name) 
        if remove_initial_offset:
            y_mean -= y_mean[0] 
            this_mean_label ="{}Mean*".format(mean_name) 

        ax.plot(X,y_mean, color = mean_color, label= this_mean_label)
        ax.plot(X,y_mean+Y.std(axis=0), "-.", color = std_p, label="{}+1 SD".format(mean_name))
        ax.plot(X,y_mean-Y.std(axis=0), "-.", color = std_m, label="{}-1 SD".format(mean_name))
    else:
        ax.set_prop_cycle('color',color_cycle)
        one_label = False
        n =  len(Y)
        my_alpha = np.min([(1./n+0.4),1.])
        suffix_label = ""
        if remove_initial_offset:
            suffix_label = "*"
        for i, y in enumerate(Y):
            #ax.plot(X,y,label="step %d"%i)
            this_y = y
            if remove_initial_offset:
                this_y -= y[0]
            if not one_label and i>=n/2:
                #ax.plot(X,y,label="{}steps 1-{}".format(mean_name,n))
                ax.plot(X,this_y,label=steps_label.format(mean_name,n)+suffix_label,alpha=my_alpha)
                one_label=True
            else:
                ax.plot(X,this_y,alpha=my_alpha)
    if change_x_ticks:
        ax.set_xticks([0,.20,.40,.60,.80,1.00],labels=[0,20,40,60,80,100])

def create_axs_dimensions(nrows, ncols, margin= 2, header = 2, subheigth = 8, subwidth= 8): ## now it is in cm

    m = margin /2.54
    h = header /2.54

    a= subheigth/2.54
    b= subwidth /2.54

    width = ncols * (m + b+ m)
    height = nrows * (h +a +h)

    axarr = np.empty((nrows, ncols), dtype =object)
    
    logger.debug(f"height: {height}, width: {width}")

    fig = plt.figure(figsize=(width, height)) #, facecolor = 'lightblue')

    for i in range(nrows):
        for j in range(ncols):
            axarr[i,j] = fig.add_axes([(m+j*(2*m+b))/width,
                (height - (i+1)*(2*h+a)+h)/height,
                b/width,
                a/height])

    return fig, axarr

def plot_std_plots(all_curves_for_any_person, plot_std=True, plot_ref_curves=True, ref=GaitIKRefData(), subplot_grid=(ROW_OF_FLOTS+1,3), steps_label="{}steps 1-{}", legend=True, axs=None, fig=None, use_color_cycle=True, subject_identifier="Some_Subject_Or_Group_of_Subjects_Please_Change",curve_suffix="",replace_conv_names=None, remove_initial_offset=False):
    if ref is None:
        plot_ref_curves = False
        logger.warning("No reference curves defined, can't plot them")
    new_curves_dict = {}

    new_curves_dict_processed = {}
    if ref:
        action_type = ref.action_type
    else:
        action_type = "???"
    if type(axs) == type(None) or type(fig)==type(None):
        fig, axs = create_axs_dimensions(*subplot_grid)
        #fig, axs = plt.subplots(*subplot_grid, squeeze=False)
        
        for ax in axs.flatten():
            ax.set_axis_off()
    #else:        
    #    fig.tight_layout(pad=5.0)
    all_handles = []
    all_labels = []
    if plot_std:
        plot_save_name_suffix = "std"
    else:
        plot_save_name_suffix = "each_step"

    createRefDic = {}

    def strip_name(some_name):
        if not len(curve_suffix) ==0:
            if curve_suffix in some_name:
                some_name = some_name.split(curve_suffix)[0]
            else:
                logger.error(f"you provided a curve suffix '{curve_suffix}', but this was not found in the name definition '{some_name}'. Plots will likely be incorrect")
        suffix = some_name[-2:] 
        if suffix == "_l" or suffix == "_r":
            return some_name[:-2]
        return some_name

    def plot_all_joint_or_muscles_for_person(all_curves_for_this_person, plot_ref_curves=True):
        
        for name, list_of_curves in all_curves_for_this_person.items():

            logger.debug(f"1st loop: {name}")
            curves_combined = []
            ref_name = list_of_curves[1]
            side = list_of_curves[2]

            for curves in list_of_curves[0]:
                x = curves[0]
                for curve in curves[1]:
                    curves_combined.append((x, curve))
            
            logger.debug(ref_name)
            side_index = side
            if side == -1:
                side_index = 2
            base_name = ref_name['name']
                #logger.error("side is different from named side")
            this_vec = [None, None, None]
            
            #### arg this is more complicated than i thought
            stripped_name = strip_name(name)
            if stripped_name in new_curves_dict.keys():
                ## I need to place it in the correct place
                #logger.info("if this is triggered, then i am updating the side, right?")
                this_vec,ref_name = new_curves_dict[stripped_name]
                logger.debug(this_vec[side_index])
                logger.debug(curves_combined)
                logger.debug("I need to concatenate those, I think")
            else:
                logger.debug(f"This is not triggered now >>{name}<<, {base_name}")
                logger.debug(name)
                logger.debug(new_curves_dict.keys())
            this_vec[side_index] = curves_combined 
            new_curves_dict.update({stripped_name:(this_vec,ref_name)})
        
        logger.debug(f"end of 1st loop i created the: {new_curves_dict}")
        
        for name,(this_vec,ref_name) in new_curves_dict.items():
            logger.debug(f"2nd loop: {name}")
            for side, curves_combined in enumerate(this_vec):  
                if curves_combined:
                    x, new_curves_combined = reshape_curves(curves_combined)
                    suffix = ""
                    if side == 0:
                        suffix= "_l"
                    if side == 1:
                        suffix= "_r"
                    if side == 2:
                        side = -1

                    new_curves_dict_processed.update({f"{name}{suffix}":(x,new_curves_combined,side,ref_name)})
            
            for side, curves_combined in enumerate(this_vec):    
                if side == 2 and not curves_combined:
                    #logger.info("trying to combine sides")
                    curves_combined = None 
                    if this_vec[0] and this_vec[1]:
                        curves_combined = this_vec[0] + this_vec[1]
                        #logger.info("sides combined!")
                    if not this_vec[0]:
                        curves_combined = this_vec[1]
                    if not this_vec[1]:
                        curves_combined = this_vec[0]
                    x, new_curves_combined = reshape_curves(curves_combined)
                    new_curves_dict_processed.update({name:(x,new_curves_combined,side,ref_name)})
                    
        for name, curve_dict_curves in new_curves_dict_processed.items():
            logger.debug(f"3rd loop: {name}")
            
            X = curve_dict_curves[0]
            Y = curve_dict_curves[1]
            side = curve_dict_curves[2]
            logger.debug(f"going over side {side}")
            ref_name = curve_dict_curves[3]
            logger.debug(f"the ref_name for this set of curves is {ref_name}")

            ax = axs[ ref_name["position"][0],ref_name["position"][1]]
            ax.set_axis_on()
            if plot_ref_curves:
                if not ref:
                    logger.warning("I was asked to display references, but no reference defined!")
                else:
                    ## this is backwards, i want to get the updated axis labels from the reference
                    if replace_conv_names:
                        #print(ref_name["name"])
                        #print(ref_name)
                        ##it should be a warning, but i guess you wouldnt do this by accident
                        logger.debug("replacing graph parameters from saved and using the values from replace_conv_names provided")
                        for repl_name , repl_vals in replace_conv_names.items():
                            if repl_vals["name"] == ref_name["name"]:
                                ref_name = repl_vals
                    ## and when i update i can plot it
                    ref.plot_reference_name(ref_name["name"], scale=[1/99,ref_name["scale"][0]], 
                        num_cycles=1, avg_line=False, ax=ax, remove_initial_offset=remove_initial_offset)
            try:
                   ##Let's create a refdata instance for this guy, in case we want to use it in the future:
                if side == 2 or side == -1:
                    logger.debug("creating reference curve of combined left and right sides")
                    thisAsRef = RefDataPrimitive()
                    thisAsRef.x    = 100*X #this is how it was defined before...
                    thisAsRef.scale = ref_name["scale"]
                    #thisAsRef.mean = ref_name["scale"][0]*Y.mean(axis=0)
                    #thisAsRef.sd   = Y.std(axis=0) 
                    thisAsRef.name = subject_identifier
                    thisAsRef.Y = Y
                    createRefDic.update({ref_name["name"]:[thisAsRef]})
                if not side == 2:
                    actual_plot(X,Y,ax,side, plot_std, steps_label=steps_label,use_color_cycle=use_color_cycle, remove_initial_offset=remove_initial_offset)
            except BaseException as e:
                logger.error(f"could not plot {name}, {ref_name['name']} {e.what}")
            ax.set_title(ref_name["title"])
            ax.set(xlabel=f"\MakeUppercase {action_type} cycle [\%]", ylabel=ref_name["yaxis_name"])
            ax.set_ylim(ref_name["axes_limits"])
            handles, labels = ax.get_legend_handles_labels()
            all_handles.extend(handles)
            all_labels.extend(labels)


    if isinstance(all_curves_for_any_person, dict):
        plot_all_joint_or_muscles_for_person(all_curves_for_any_person, plot_ref_curves=plot_ref_curves)
        nh, nl = remove_repeated(all_handles, all_labels)    
        if legend:
            fig.legend(nh, nl,loc='center left', bbox_to_anchor=(1, 0.5))#, loc='lower right')
        #plt.savefig('figure_{}.pdf'.format(plot_save_name_suffix), bbox_inches='tight')
        #plt.show()
    else:
        logger.debug("all_curves_for_any_person not a dict")
    if isinstance(all_curves_for_any_person, list):
        for all_curves_for_this_person in all_curves_for_any_person:
            plot_all_joint_or_muscles_for_person(all_curves_for_this_person, plot_ref_curves=False)
        nh, nl = remove_repeated(all_handles, all_labels)        
        if legend:
            fig.legend(nh, nl,loc='center left', bbox_to_anchor=(1, 0.5))#, loc='lower right')
        #plt.savefig('figure_multiple_people_{}.pdf'.format(plot_save_name_suffix), bbox_inches='tight')
        #plt.show()
    else:
        logger.debug("all_curves_for_any_person not a list")

    #change the size of the figure to show always exactly the same way 





    return axs, fig, nh, nl, createRefDic




class TrialData:
    def __init__(self, file, remove_time_offset=True):
        logger.info("Reading Trial file: %s"%file)
        ### find the size of the header:
        header_line_count = 0
        in_degrees=False
        sepsep = '\t' ## this is actually a tsv, but not a lot of people use this name i guess
        with open(file,'r') as f:
            a_line = ''
            while not 'endheader' in a_line:
                a_line = f.readline()
                if not a_line: ## this means I have reached the end, i think
                    logger.warning("did not find endheader. will treat this like a normal csv with a single line header")
                    header_line_count = 0
                    sepsep = ','
                    remove_time_offset=False
                    break
                if "inDegrees=" in a_line and "yes" in a_line:
                    in_degrees=True
                header_line_count+=1

        self.data = pd.read_csv (file, sep = sepsep, skiprows=header_line_count)
        if remove_time_offset: #remove time ofset
            self.data["time"] = self.data["time"] - self.data["time"][0]
        for col in self.data.columns:
            if col == "time":
                continue
            else:
                if in_degrees:
                    self.data[col] =  self.data[col]/180.0*np.pi
                else:
                    self.data[col] =  self.data[col]
        ## let's create some consistency here
        logger.warning("I am making column names lowercase btw!")
        self.data.rename(columns=str.lower, inplace=True)

    def trim_time(self, start_time, end_time):
        #df = df[(df['closing_price'] >= 99) & (df['closing_price'] <= 101)]
        #data = data[(data["time"] >= time_start[i_file]) & (data["time"] <= time_end[i_file]+time_start[i_file])]
        self.data = self.data[(self.data["time"] >= start_time) & (self.data["time"] <= end_time+start_time)]
        logger.debug(data)

        #remove time offset again because we changed where it starts
        self.data.time = self.data["time"] - np.min(self.data["time"])
        self.data.set_index('time')

    def get_as_np(self, cols="all"):
        if cols == "all":
            return self.data.iloc[:,:].values
        else: 
            return self.data.loc[:,cols].values
        
        
def generate_somejoint_or_muscle_curves(some_action_trials, skip_trials, curve_prefix="knee_angle", conv_names=None,left_or_right=0, curve_suffix="",use_absolute_times=False):
    xy_joint_or_muscles = ({},{})
    for i_file, file in enumerate(some_action_trials):
        if i_file in skip_trials:
            logger.warning("skipping file: %s"%file)
            continue

        this_trial = TrialData(file, remove_time_offset=use_absolute_times)
        #this_trial.trim_time(time_start[i_file], time_end[i_file] )

        data = this_trial.data

        for joint_or_muscle_name, ref_name in conv_names.items():
            if joint_or_muscle_name in data.columns:
                joint_or_muscle_name_suffix = [""]
            else:
                joint_or_muscle_name_suffix = ["_l","_r"]

            if ref_name["plot_it"]:
                for l_r, joint_or_muscle_suffix in enumerate(joint_or_muscle_name_suffix):
                    joint_or_muscle_complete_name = joint_or_muscle_name+joint_or_muscle_suffix + curve_suffix

                    logger.info(joint_or_muscle_complete_name)
                    logger.debug(joint_or_muscle_complete_name)
                    if joint_or_muscle_complete_name==f"{curve_prefix}_r{curve_suffix}":
                        y = data[joint_or_muscle_complete_name]*ref_name["scale"][1]
                        x = data["time"]
                        xy_joint_or_muscles[1].update({file:(x,y,[])})
                    elif joint_or_muscle_complete_name==f"{curve_prefix}_l{curve_suffix}":
                        y = data[joint_or_muscle_complete_name]*ref_name["scale"][1]
                        x = data["time"]
                        xy_joint_or_muscles[0].update({file:(x,y,[])})
                    elif joint_or_muscle_complete_name==curve_prefix+curve_suffix:
                        logger.debug("FORCE PLATE?")
                        y = data[joint_or_muscle_complete_name]*ref_name["scale"][1]
                        x = data["time"]
                        xy_joint_or_muscles[left_or_right].update({file:(x,y,[])})

    return xy_joint_or_muscles


def clip_curve(time, curve_val, time_clips = [(0.1,1.13),(1.13,2.2),(2.2,3.26),(3.26,4.39),(4.39,5.55)], PLOT_IT=False, add_frame_offset=0, use_frame_clips=None):
    actions = []
    non_actions = []
    if (not time_clips and not use_frame_clips) or (time_clips and use_frame_clips):
        logger.error("I need either time_clips or use_frame_clips , but not both")
        return 
    def get_index_of_time(x):
        #time is always increasing so this is trivial:
        for i, x_i in enumerate(time):
            if x_i>x:
                return i
    logger.debug(time_clips)
    if time_clips:
        step_range =len(time_clips)-1
    if use_frame_clips:
        step_range =len(use_frame_clips)-1

    for i in range(step_range):
        if time_clips:
            li = get_index_of_time(time_clips[i][0])
            ui = get_index_of_time(time_clips[i][1])
        if use_frame_clips:
            li = use_frame_clips[i][0]-add_frame_offset
            ui = use_frame_clips[i][1]-add_frame_offset

        logger.debug(li)
        logger.debug(time.values[li])

        xi = time[li:ui] #- time.values[li]
        yi = curve_val[li:ui]
        actions.append((xi,yi))
    for i in range(step_range):
        if time_clips:
            li = get_index_of_time(time_clips[i][1])
            ui = get_index_of_time(time_clips[i+1][0])
        if use_frame_clips:
            li = use_frame_clips[i][1]-add_frame_offset
            ui = use_frame_clips[i+1][0]-add_frame_offset

        xi = time[li:ui]
        yi = curve_val[li:ui]
        non_actions.append((xi,yi))
    ## add beginning and end to non_actions:
    if time_clips:
        a = get_index_of_time(time_clips[0][0])
        b = get_index_of_time(time_clips[-1][0])
    if use_frame_clips:
        a = use_frame_clips[0][0]-add_frame_offset
        b = use_frame_clips[-1][0]-add_frame_offset

    non_actions.append((time[0:a],curve_val[0:a]))
    non_actions.append((time[b:-1],curve_val[b:-1]))
    ## test if i did it correctly
    if PLOT_IT:
        fig, ax = plt.subplots()
        for xi_yi in actions:
            xi = xi_yi[0]
            yi = xi_yi[1]
            plt.plot(xi,yi)
        for xi_yi in non_actions:
            plt.plot(xi_yi[0],xi_yi[1],'lightgray')
        ax_frames = ax.twiny()
        ax_frames.set_xlim([add_frame_offset,add_frame_offset+len(time)])
        ax_frames.set_xlabel("Frames")
        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        ax.grid(which='major', color='#CCCCCC', linestyle='--')
        ax.grid(which='minor', color='#CCCCCC', linestyle=':')
        ax.set_xlabel("Wall Time [s]")
        plt.show()
    return actions
#steps = clip_curve(x,y)

def clip_curve_test(time, curve_val, time_clips = [(0.1,1.13),(1.13,2.2),(2.2,3.26),(3.26,4.39),(4.39,5.55)], add_frame_offset=0, use_frame_clips=[]):
    return clip_curve(time, curve_val, time_clips, PLOT_IT=True, add_frame_offset=add_frame_offset, use_frame_clips=use_frame_clips) 

    
def reshape_curves(curves, PLOT_IT=False, lower_lim = None, upper_lim = None): ##they have the same x, so now it will return x, Y
    ##to be able to get the average curve they need to line up and have the same number of samples
    max_len = 0
    new_curves = []

    finding_lower = False
    finding_upper = False
    if not lower_lim:
        finding_lower = True
        lower_lim = 1e200
    if not upper_lim:
        finding_upper = True
        upper_lim = -1e200
    for curve in curves:
        logger.debug(curve)
        if max_len < get_length(curve[0]):
            max_len = get_length(curve[0])
        try:
            if finding_lower and np.min(curve[0]) < lower_lim:
                lower_lim = np.min(curve[0])
        except:
            logger.error(curve)
            lower_lim = np.min(curve) #in case i have only 1 curve
        try:
            if finding_upper and np.max(curve[0])> upper_lim:
                upper_lim = np.max(curve[0])
        except:
            logger.error(curve)            
            upper_lim = np.max(curve)
    #max len
    logger.debug(max_len)
    xi = np.linspace(lower_lim,upper_lim, num=max_len)
    for curve in curves:
        try:
            fy =  interpolate.interp1d(curve[0],curve[1])
            new_curves.append(fy(xi))
        except:
            logger.warning(len(curve[0]))
            logger.warning(len(curve[1]))
            logger.warning(curve[0])
            logger.warning(curve[1])
            raise()

    if PLOT_IT:
        for yi in new_curves:
            plt.plot(xi,yi)
        plt.show()
   
    return xi, np.array(new_curves)

#a = reshape_curves(normalize_steps(steps))
#print(a[0])

def normalize_steps(steps_, PLOT_IT=False):
    #print("here")
    #logger.info(steps_)
    if len(steps_) == 0:
        traceback.print_exc()
        logger.error("you didnt give me any data to normalize!!!!!")
    ## all steps will last 1.
    normalized_steps = []
    if steps_:
        for i, xi_yi in enumerate(steps_):
            xi = np.linspace(0, 1, num=len(xi_yi[1]))
            normalized_steps.append((xi,xi_yi[1].values))
        if PLOT_IT:
            for xi_yi in normalized_steps:
                xi = xi_yi[0]
                yi = xi_yi[1]
                plt.plot(xi,yi)
            plt.show()
    return normalized_steps
#unit test:
#normalize_steps(steps);


def get_length(something):
    if isinstance(something,list):
        return len(something)
    if isinstance(something,np.ndarray):
        return something.size
    logger.debug(something)
    raise("wtf!!!!!!!!!!!!!")

#print(get_length([1,2,3,4]))
#print(get_length(np.array([1,2,3,4])))


#reload(refdata)

class AxCurves():
    def __init__(self, position = None,curves_dic = None, reference =None, joint_or_muscle_complete_name=None ):
        self.position = position
        self.curves_dic = curves_dic
        self.reference = reference
        self.name = joint_or_muscle_complete_name
    def update(self):
        ref_name = self.curves_dic[self.name][1]
        ref_name["position"] = self.position
        self.curves_dic[self.name] = (self.curves_dic[self.name][0], ref_name, self.curves_dic[self.name][2])
        
from copy import deepcopy

def creat_axs(cccc, ref= IdGaitData()):
    ## deepcopy?
    local_cccc = deepcopy(cccc)
    axcurve_list_ = []
    for name, list_of_curves in local_cccc.items():
        some_ax = AxCurves()
        ref_name = list_of_curves[1]
        side = list_of_curves[2]
        some_ax.position = ref_name["position"]
        some_ax.curves_dic = {name:list_of_curves}
        some_ax.name = name
        some_ax.reference = ref
        some_ax.update()
        logger.debug(ref_name)
        axcurve_list_.append(some_ax)
    return axcurve_list_
        
#axcurve_list = creat_axs(all_curves_for_this_person)


def plotAX(some_Axs, ax, fig, plot_std=True, plot_ref_curves=False, legend=False, **kwargs):
    
    allnh = []
    allnl = []
    allZ = []
    for axi in ax.flatten():
        axi.set_axis_off()
    for an_Ax in some_Axs:
        _,_,nh,nl,Z = plot_std_plots(an_Ax.curves_dic, axs=ax, fig=fig, ref= an_Ax.reference, legend= False, plot_std=plot_std, plot_ref_curves=plot_ref_curves, **kwargs)
        allnh.extend(nh)
        allnl.extend(nl)
        allZ.extend(Z)
    allnh, allnl = remove_repeated(allnh, allnl) 
    if legend:
        fig.legend(allnh, allnl,loc='lower right', bbox_to_anchor=(0.85, 0.18))
    return fig, ax, allnh, allnl, allZ
       

       
        
#plotAX(axcurve_list, ax)

def apply_offset_to_axs(some_axcurve_list, vert_offset):
    new_list = []
    for i_axcu in some_axcurve_list:
        i_axcu.position = (i_axcu.position[0]+vert_offset, i_axcu.position[1])
        i_axcu.update()
        new_list.append(i_axcu)
    return new_list

from IPython.display import display, Javascript

def create_new_cell_below(content):
    display(Javascript('''
        var idx = Jupyter.notebook.get_selected_index();
        var codeCell = Jupyter.notebook.insert_cell_at_index('code', idx);
        codeCell.set_text('#GENERATED CELL!\\n%s');
        Jupyter.notebook.select(idx);
    ''' % content.replace('\n', '\\n')))

def find_steps(x, grf,weight):
    #plt.plot(x,grf)
    #plt.show()
    threshold = weight*9.8/10
    step = False
    step_seq = []
    step_start = 1e200
    step_stop = 1e200
    min_duration = 0.05
    lowering = False
    rising = False
    this_step = [None,None]
    for t, y in zip(x,grf):
        logger.debug((y, threshold))
        if not step and y>threshold:
            logger.debug(t)
            rising = True
            step_start= np.min([t,step_start])
            if t-step_start > min_duration:
                step = True
                logger.debug("is step")
                this_step[0] = step_start
        if rising and y<threshold:
            rising = False
            step_start = 1e200
        if step and y<threshold:
            logger.debug("trying to find lowering edge, %f, %f"%(t,step_stop))
            lowering = True
            step_stop = np.min([t,step_stop])
            if t-step_stop > min_duration:
                logger.debug("found lowering %s"%step_stop)
                step = False
                this_step[1] = step_stop
                step_seq.append(this_step)
                this_step = [None,None]
                step_start = 1e200
                step_stop = 1e200
        if lowering and y>threshold:
            lowering = False
            step_stop = 1e200
    if this_step[0]:
        step_seq.append(this_step) ## appending the last incomplete step because we need the start for segmentation
    return step_seq

def gen_step_ticks(some_steps, weight):
    xy = [[],[]]
    lower_curve_bound = weight*9.8/10 
    textstr = [] # x,y, stepcount
    for i, a_step in enumerate(some_steps):
        xy[0].extend([a_step[0],a_step[0],a_step[0]])
        xy[1].extend([lower_curve_bound,700,np.nan])
        xy[0].extend([a_step[1],a_step[1],a_step[1]])
        xy[1].extend([lower_curve_bound,800,np.nan])
        ##if the boundary of the steps are None this is a problem
        if not a_step[0] and not a_step[1]:
            continue
        if a_step[0]:
            lwx = a_step[0]
        if a_step[1]:
            lwx = a_step[1]
        if a_step[0] and a_step[1]:
            lwx = a_step[0]/2+a_step[1]/2
        textstr.append([lwx,lower_curve_bound, ("st.%d"%i)])
    return xy[0],xy[1],textstr

##newer better, should work for gait 
def construct_step_segmentation_vector(some_steps):
    new_step_def_list = []
    for i,ith_step in enumerate(some_steps):
        #disregard the first step
        if i < len(some_steps)-1:
            ithpone= some_steps[i+1][0]
        else:
            ithpone= None
        if i == 0:
            continue
        new_step_def_list.append((ith_step[0], ithpone))
    return new_step_def_list
from copy import copy
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

def each_side_plot(grf_, zero_time, grf_name_prefix = "1_ground_", side="Left", weight=None, plot_all=False, time_offset=0, plot_no_offset=True, nicer_plot=False, figax = None,

        figsize=(18,4)):
    
    grf = TrialData(grf_, remove_time_offset=False)

    x_grf = np.array(list(grf.data.time-zero_time))
    x_grf_offset = copy(x_grf)
    x_grf_offset+= time_offset

    steps_vec = find_steps(x_grf_offset,grf.data[f"{grf_name_prefix}force_vy"], weight)

    st_seg = construct_step_segmentation_vector(steps_vec)
    
    logger.debug(st_seg)
    all_handles = []
    all_labels = []
    
    if nicer_plot:
        fig = figax[0]
        ax1 = figax[1]
    else:
        fig, ax1 = plt.subplots(figsize=figsize)
    ax1.xaxis.set_major_locator(MultipleLocator(1))    
    ax1.xaxis.set_minor_locator(MultipleLocator(.1))    
    #plt.plot(x_ik,ik_2.data.ankle_angle_l/3.141592*180,"--", label="ankle l")
    #plt.plot(x_ik,ik_2.data.hip_flexion_l/3.141592*180,"--", label="hip x l")
    
    xsl, ysl, textstrl = gen_step_ticks(steps_vec, weight)
    
    ax1.plot(x_grf,grf.data[f"{grf_name_prefix}force_py"],'r', label="py")
    if plot_all:
        ax1.plot(x_grf,grf.data[f"{grf_name_prefix}force_px"],'g', label="px")
        ax1.plot(x_grf,grf.data[f"{grf_name_prefix}force_pz"],'b', label="pz") 
    
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    handles, labels = ax1.get_legend_handles_labels()
    all_handles.extend(handles)
    all_labels.extend(labels)
    ax1.set_ylim((-0.05,1))

    
    # plotting step ticks
    ax2.plot(xsl,ysl,'g')
    for a_text in textstrl:
        ax2.annotate(a_text[2],(a_text[0],a_text[1]))
    
    if plot_no_offset:
        ax2.plot(x_grf,grf.data[f"{grf_name_prefix}force_vy"],'darkred', label="y")
    ax2.plot(x_grf_offset,grf.data[f"{grf_name_prefix}force_vy"],'coral', label="y t_off=%f"%time_offset)
    if plot_all:
        ax2.plot(x_grf_offset,grf.data[f"{grf_name_prefix}force_vx"],'lime', label="x")
        ax2.plot(x_grf_offset,grf.data[f"{grf_name_prefix}force_vz"],'navy', label="z")
    
    handles, labels = ax2.get_legend_handles_labels()
    all_handles.extend(handles)
    all_labels.extend(labels)


    plt.title(f"grf {side}: {grf_}")
    fig.legend(all_handles, all_labels)
    if nicer_plot:
        pass
    else:
        plt.show()

    try:
        round_output = np.vectorize(lambda n: (np.round(n,2) if n else 1000))
        return round_output(st_seg).tolist()
    except:
        return []

##########################

class GRFSET:

    def  __init__(self, file):
        _df = pd.read_csv(file)
        _a = _df.set_index(list(_df.columns[0:3]))
        _B = pd.DataFrame()
        _B['all_cols'] = _a.apply(lambda row: row.values, axis=1)
        self.dataset = _B
        self.get_mean()
        self.get_std()
       
    def get_mean(self):
        self.set_mean = self.dataset.all_cols.mean()
        self.x = np.arange(len(self.set_mean))
        return self.set_mean

    def get_std(self):
        self.std_dev = np.vstack(self.dataset.all_cols).std(axis=0)
        return self.std_dev
    
    def plot(self, ax=None):
        if not ax:
            ax = plt.gca()
        ax.plot(self.x,self.set_mean, label='mean')
        ax.fill_between(self.x,self.set_mean+self.std_dev, self.set_mean-self.std_dev, facecolor='red', alpha=0.9)

class GRFWalkingRefData(RefData):
    """
            from: https://www.nature.com/articles/s41597-020-0481-z#Sec5

    """
    def __init__(self, compress = 60):
        super(GRFWalkingRefData,self).__init__( "Walking")
        self.set_myself(compress=compress)

    def set_myself(self, compress =60):
        logger.info("assuming stance phase is %f  of the total step duration"%compress)
        module_dir = os.path.dirname(os.path.abspath(__file__))

        #A = GRFSET('GRF_F_V_PRO_left.csv')
        #B = GRFSET('GRF_F_V_PRO_right.csv')
        
        #C = GRFSET('GRF_F_AP_PRO_left.csv')
        #D = GRFSET('GRF_F_AP_PRO_right.csv')
        
        #E = GRFSET('GRF_F_ML_PRO_left.csv')
        #F = GRFSET('GRF_F_ML_PRO_right.csv')
        
        
        
        for axis, movement_direction in zip(["x","y","z"], ["AP","V","ML"]):
            self.reference_curve_dict.update({"the_ground_force_v%s"%axis:[RefDataPrimitive(),RefDataPrimitive()]})
            for i, side in enumerate(["left", "right"]):
                logger.debug(i)
                ## TODO: we cant have a lib that needs to calculate the std and mean deviations each time, this doesnt change it carrying the dataset around requires like 1gb!
                set_name = os.path.join(module_dir,"..","data","grf_data", "GRF_F_%s_PRO_%s.csv"%(movement_direction,side))
                this_set = GRFSET(set_name)
                logger.debug(set_name)
                logger.debug(this_set.set_mean)
                
                self.reference_curve_dict["the_ground_force_v%s"%axis][i].name = "%s Force %s"%(movement_direction, side)
                self.reference_curve_dict["the_ground_force_v%s"%axis][i].mean = extend_y(this_set.set_mean,compress)
                self.reference_curve_dict["the_ground_force_v%s"%axis][i].sd = extend_y(this_set.std_dev,compress)
                self.reference_curve_dict["the_ground_force_v%s"%axis][i].x = compress_x(this_set.x,compress)


def compress_x(x, percent=60):
    
    x = np.array(x)
    
    num_samples = int(np.ceil(percent/100.*len(x)))
    
    compressed = np.hstack([x, np.zeros((num_samples))])

    compressed = np.linspace(0,100, num= len(compressed))
    
    return compressed

def extend_y(x, percent=60):
    
    x = np.array(x)
    
    num_samples = int(np.ceil(percent/100.*len(x)))
    
    compressed = np.hstack([x, np.zeros((num_samples))])
    
    return compressed

#compress_x([1,2,3])

import numpy as np
from scipy import interpolate
from sklearn.metrics import root_mean_squared_error


def rmse(graphs, PLOT_IT=False):
    def from_x_yyy_to_xy_xy_xy(x,y):
        a = []
        logger.debug(x)
        logger.debug("mulllll")
        logger.debug(y.shape)
        #return
        for i in range(y.shape[0]):
            X = x
            Y = y[i,:]
            assert(len(X)==len(Y))
            a.append([X,Y])
        return a


    def pick_measured_curves(axc):
        for k in axc.curves_dic.keys():
            logger.debug(k)
            pass
        #axc.curves_dic[k][0] # curves, this has the length of the number of trials, and the then each curve with their different x values
        logger.debug(len(axc.curves_dic[k][0]))
        logger.debug(axc.curves_dic[k][0][0])
        #return
        #axc.curves_dic[k][1] # reference plotting parameters
        logger.debug(axc.curves_dic[k][1])
        #axc.curves_dic[k][2] # side, 0 = left, 1, right
        a = []
        for trial in axc.curves_dic[k][0]:
            a.extend(from_x_yyy_to_xy_xy_xy(trial[0],trial[1]))
        logger.debug(len(a))
        logger.debug(len(a[0]))
        xi, yi =  reshape_curves(a)
        return xi,yi #, axc.curves_dic[k][1]['name']

    def strip_ends(some_name):
        if some_name[-2:] == "_l" or some_name[-2:] == "_r" :
            return some_name[:-2]
        return some_name
    
    def pick_ref(axc):
        for k in axc.curves_dic.keys():
            logger.debug(k)
            pass
        logger.debug(axc.curves_dic[k][1]['name'])
        this_my_ref = axc.reference.reference_curve_dict[axc.curves_dic[k][1]['name']]
        if len(this_my_ref) >1:
            raise("if you have multiple references you have to think about what you are doing")
        #return this_my_ref[0].x, this_my_ref[0].Y
        #a = []
        logger.debug(this_my_ref[0].Y.shape)
        logger.debug(this_my_ref[0].x.shape)
        #for curve in range(this_my_ref[0].Y.shape[0]):
        #     a.extend((this_my_ref[0].x,a.append(this_my_ref[0].Y[curve,:])))
        logger.debug(this_my_ref[0].Y.shape)
        logger.debug(this_my_ref[0].x.shape)

        return this_my_ref[0].x, this_my_ref[0].Y
    
    ### we create a new dictionary
    
    damnit = {}
    
    
    #first we create a dict
    tf = {}
    
    for acx in graphs:
        logger.debug("Going over graphs while trying to calculate RMSE")
        ISIK = False
        ISID = False
        ISSO = False
        for k in acx.curves_dic.keys():
            logger.debug(k)
            pass
    
        logger.debug(k)
        eends = ""
        n = acx.curves_dic[k][1]['yaxis_name']
        if "Angle" in n:
            ISIK = True
            eends = "_ik"
        elif "Torque" in n:
            ISID = True
            eends = "_id"
        elif "Activation" in n:
            ISSO = True
            eends = "_so"
        else:
            ## moved this to debug because all is well that ends well
            logger.debug(f"eends: {eends}")
            logger.debug(f"What? {n} doent have Angle Torque of Activation in its name, what should i do???")
            
        real_name = strip_ends(k)+eends
        bb = pick_ref(acx)
        
        
        aa_ = pick_measured_curves(acx) ## this can be left or right!
        if real_name in tf.keys():
            g = tf[real_name]
            aa = [g[0],g[1]]
            a = []
            for trial in aa[1]:
                #a.extend(from_x_yyy_to_xy_xy_xy(aa[0],trial))
                a.append([aa[0],trial])
            for trial in aa_[1]:
                #a.extend(from_x_yyy_to_xy_xy_xy(aa_[0],trial))
                a.append([aa_[0],trial])
            aa_ =  reshape_curves(a)
        tf.update({real_name:[aa_[0],aa_[1],bb]})
        #so we need to put them 2 together
    str_ = ""
    for real_name, (g0, g1, bb) in tf.items():
        
        if False:
            for c in bb[1]:
                plt.plot(bb[0]/100,c)
            for c in aa[1]:
                plt.plot(aa[0],c)
            plt.plot(aa[0],aa[1].mean(axis=0)) # measured
            plt.plot(bb[0]/100,bb[1].mean(axis=0)) # reference


        x, c = reshape_curves([[g0, g1.mean(axis = 0)],
                                       [bb[0]/100, bb[1].mean(axis = 0)],
                                      ])
        measured_curve_mean = c[0]
        reference_curve_mean = c[1]

        if PLOT_IT:
            plt.plot(x,measured_curve_mean,label='measured')
            plt.plot(x,reference_curve_mean,label='reference')
            plt.legend()
            logger.debug(real_name)
            plt.show()
        str_ += f"{real_name: <{20}} & {root_mean_squared_error(measured_curve_mean,reference_curve_mean): <{20}} \\\\ \n"
        
    return str_

