#!/usr/bin/env python3

import re
from glob import glob
import logging
from os import path

class TrialFile():
    def __init__(self, filename):
        self.time = ""
        self.double_counter = ""
        self.logger_name = ""
        self.extension = ""
        self.activity = ""
        self.set_from_name(filename)
    def set_from_name(self, complete_filename):
        filename = path.basename(complete_filename)
        r = re.match("([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2})([a-zA-Z]*)([0-9]+)(.*?)\.(.*)",
                 filename)
        if r:
            self.time = r.group(1)
            self.activity = r.group(2)
            ## this became useless because we don't have a clear separation token here
            self.double_counter= r.group(3)
            self.logger_name = r.group(4)
            self.extension = r.group(5)
    def rename_activity(self,new_activity_name):
        return self.time +new_activity_name+self.double_counter+self.logger_name+"."+self.extension
        
def get_all_times(a_glob):
    set_of_times = []
    for file in a_glob:
        logger.debug(file)
        aTF = TrialFile(file)
        if aTF.time:
            set_of_times.append(aTF.time)
        logger.debug(aTF.time)
    #return set_of_times
    return sorted(list(set(set_of_times)))

def lumpTrialFiles(a_glob):
    my_times = get_all_times(a_glob)
    logging.debug(f"my_times {my_times}")
    lumped_times = []
    for i, tims in enumerate (my_times):
        if i == 0:
            lumped_times.append([tims])
            continue
        a_time = tims.split("-")
        a_previous_time = my_times[i-1].split("-")
        if a_time[:-1] == a_previous_time[:-1] and int(a_time[-1]) == int(a_previous_time[-1])+1:
            lumped_times[-1].append(tims)
        else:
            lumped_times.append([tims])
    #return lumped_times
    lumped_files = []
    for lump in lumped_times:
        this_trial_files = []
        for time in lump:
            for file in a_glob:
                if time in file:
                    this_trial_files.append(file)
        lumped_files.append(this_trial_files)
    logging.debug(lumped_files)
    return lumped_files

def construct_grf_ik_id_so_from_lumps(lumps):
    ik_files = []
    ik_lower_files = []
    grfL_files = []
    grfR_files = []
    id_files = []
    so_files = []
    for lump in lumps:
        for file in lump:
            if "_ik_lower.sto" in file:
                ik_lower_files.append(file)
            if "ik.sto" in file:
                ik_files.append(file)
            if "grfRight.sto" in file:
                grfR_files.append(file)
            if "grfLeft.sto" in file:
                grfL_files.append(file)
            if "tau.sto" in file:
                id_files.append(file)
            if "so.sto" in file:
                so_files.append(file)
    return ik_files, grfL_files, grfR_files, id_files, so_files, ik_lower_files, lumps

def sort_files(action_list=None, directory="./" ):
    if not action_list:
        logging.warn(f"no list of actions provided. Will add all files in {directory} folder!")
        action_list = [""]
    the_glob = glob(path.join(directory,"*"))
    sifted_glob = []
    for action in action_list:
        for file in the_glob:
            if action in file:
                logging.debug(f"appending file {file}")
                sifted_glob.append(file)
    return construct_grf_ik_id_so_from_lumps(lumpTrialFiles(sifted_glob))

import shutil

def rename_trials(lumps, new_names):
    for lump,new_name in zip(lumps,new_names):
        for file in lump:
            aTF = TrialFile(file)
            new_filename= aTF.rename_activity(new_name)
            shutil.move(file,new_filename)
        
def construct_new_names(dict_of_activities_and_count):
    new_names= []
    for activity, count in dict_of_activities_and_count.items():
        for i in range(count):
            new_names.append(activity)
    return new_names
#construct_new_names({"walking":8,"squat":3,"ssss":2})      
