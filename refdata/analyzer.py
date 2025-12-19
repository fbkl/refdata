#!/usr/bin/env python
# coding: utf-8


import os, sys
sys.path.append("../refdata")
from refdata.files import sort_files
from refdata import refdata
from refdata.metrics import IMULump, MocapLump, SyncedLump
from refdata import metrics
import numpy as np
import matplotlib.pyplot as plt
from importlib import reload
reload(metrics)
import glob
import matplotlib as mpl
from matplotlib.legend_handler import HandlerLine2D, HandlerTuple

from refdata.my_log import vlog
def ptupl(t):
    return f"{t[0]}x{t[1]}"

import pickle

refdata.plt.rcParams['figure.figsize'] = [12, 5]
refdata.ROW_OF_FLOTS = 1



def make_dir(base):
    path, n = base, 1
    while os.path.exists(path):
        path = f"{base}_{n}"
        n+=1
    os.makedirs(path)
    return path

def graphs_and_metrics( myImuLumpList, myMocapLumpList, subject_num, weight, this_action_name, results_dir = None, ext_sync = [None,None], manual_segmentation_list_list= [], valid_step_list_list=[]):
    
    plt.close('all')
    
    if not results_dir:
        results_dir = make_dir("results")
    
    my_dir = os.path.join(results_dir,subject_num, this_action_name) + "/"
    os.makedirs(my_dir)

    mySL = metrics.Dismissed(weight=weight, save_fig_dir=my_dir, ext_sync = [None,None], action=this_action_name)

    mySL.set_by_two_lists_of_lumps(myImuLumpList, myMocapLumpList    )

    mySL.manual_segmentation(manual_segmentation_list_list)
    
    mySL.run_analysis("id")

    mySL.which_steps_do_i_plot(valid_step_list_list)


    grfconv_names = []
    grfconv_names.append(refdata.graph_params.generate_grf_conv_names(0,weight))
    grfconv_names.append(refdata.graph_params.generate_grf_conv_names(1,weight))

    ik_conv_names = refdata.graph_params.get_ik_graph_params()
    short_ik_conv_names = refdata.graph_params.get_ik_short_graph_params()
    id_conv_names = refdata.graph_params.get_id_all_graph_params(weight)
    id_short_conv_names = refdata.graph_params.get_id_graph_params(weight)
    id_conv_names_sag = refdata.graph_params.sagittal_only(refdata.graph_params.get_id_standard_graph_params(weight))
    so_conv_names = refdata.graph_params.get_so_graph_params()
    ccc = refdata.graph_params.get_so_short_graph_params(use_paper_list=True, use_rename_list=False)

    dict_of_conv_names = {
            "grf":[ (grfconv_names, (3,3) )],
            "ik":[(ik_conv_names, (3,3)), (short_ik_conv_names, (1,3))],
            "id":[(id_conv_names, (4,3)), (id_short_conv_names, (1,3)), (id_conv_names_sag, (1,3))], 
            "so":[(so_conv_names, (16,3)), (ccc, (2,3))]
            }

    ## untested!
    #asSORefData1 = pickle.load( open( f"RTValidation_Extra/{subject_vicon_num}/so_ref_{this_action_name}_data_s{subject_num}.p", "rb" ) )

    curves_dictionary = {}

    for mode in ["grf", "ik", "id", "so"]:
        print("#"*80)
        for i, (conv_name_i, fig_size) in enumerate(dict_of_conv_names[mode]):
            print("x"*80)
            asRefData = [None,None]
            all_XXX_curves_for_this_person = [None, None]
            RR = [None, None]
            for j, stream in enumerate(["imu", "mocap"]):
                print("¤"*80)
                if mode== "grf"  and stream == "mocap":
                    ## i can load the emg here for so and maybe do something for force plate idk
                    continue
                all_XXX_curves_for_this_person[j] = mySL.gen_action_plots(mode,stream, conv_names = conv_name_i)

                curves_dictionary[mode+"_"+stream+"_"+str(i)] = all_XXX_curves_for_this_person[j]
                for std_or_not, std_str in [(False, "all"), (True, "std")]:
                    print("<>"*80)
                    RR[j] = refdata.plot_std_plots(all_XXX_curves_for_this_person[j], plot_std=std_or_not, ref=None,
                               subplot_grid = fig_size,)
                    plt.savefig(my_dir+f'sub{subject_num}_{mode}_{stream}_{this_action_name}{ptupl(fig_size)}_tighter_{std_str}_{i}.pdf', bbox_inches = 'tight')

                    
                ## i dont think it makes a difference if it is std or all for the gencurves thing
                asRefData[j] = refdata.RefData(this_action_name)
                asRefData[j].reference_curve_dict = RR[j][4]

                pickle.dump(all_XXX_curves_for_this_person[j],open(my_dir+f"{mode}{this_action_name}{subject_num}_{stream}{i}.p","wb"))

            print("A"*80)

            ## maybe i need to check something 
            _ = refdata.plot_std_plots(all_XXX_curves_for_this_person[0], plot_std=False, ref=asRefData[1],
                               subplot_grid = fig_size,)

            print("B"*80)
            plt.savefig(my_dir+f'sub{subject_num}_{mode}_{this_action_name}_imu_mocap_ref_{ptupl(fig_size)}_all{i}.pdf', bbox_inches = 'tight')

        




    plt.rcParams['figure.figsize'] = [8, 10]
    axcurve_list = refdata.creat_axs(curves_dictionary["ik_imu_0"], ref= refdata.GaitIKRefData(this_action_name))

    fig, ax =  refdata.create_axs_dimensions(3,3) 
    fig, ax, nl, legend, cref_dic = refdata.plotAX(axcurve_list, ax, fig)

    fig.legend(nl, legend,loc='center left', bbox_to_anchor=(1, 0.5))

    axcurve_list_id2 = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["id_imu_0"]),3)

    axcurve_list.extend(axcurve_list_id2)

    fig, ax =  refdata.create_axs_dimensions(8,3) 

    fig, ax, nl, legend, cref_dic = refdata.plotAX(axcurve_list, ax, fig)

    axcurve_list_so2 = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["so_imu_1"]
                                                                     ,ref=refdata.SoData(this_action_name)),6)
    print("C"*80)


    # In[ ]:


    fig, axs = refdata.create_axs_dimensions(8, 3, margin= 1.5, header = 1.2, subheigth = 6, subwidth= 6)

    #refdata.plt.rcParams['figure.figsize'] = [12, 4]
    #axcurve_list.extend(axcurve_list_so2)
    fig, ax, nl, legend, cref_dic = refdata.plotAX(axcurve_list_so2, axs, fig)


    plt.savefig(my_dir+f'sub{subject_num}_ik_id_so_{this_action_name}8x3_tighter_stds.pdf', bbox_inches = 'tight')
    # In[ ]:


    ### This is the version for the paper

    axcurve_listXXXik = refdata.creat_axs(curves_dictionary["ik_imu_1"], ref= refdata.GaitIKRefData(this_action_name))

    axcurve_listXXXid = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["id_imu_1"]),1)

    axcurve_listXXXso = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["so_imu_1"],ref=refdata.SoData(this_action_name)),2)

    axcurve_listXXXik.extend(axcurve_listXXXid)
    axcurve_listXXXik.extend(axcurve_listXXXso)



    mpl.rcParams['figure.dpi'] = 300

    fig, axs = refdata.create_axs_dimensions(4, 3, margin= 1.5, header = 1.2, subheigth = 6, subwidth= 6)
    for ax in axs.flatten():
        ax.set_axis_off()

    fig, ax, nh, nl, cref_dic = refdata.plotAX(axcurve_listXXXik, axs, fig, plot_ref_curves=True)
    #fig.legend(nh[0:2], ["Left","Right"],loc='lower right', bbox_to_anchor=(0.85, 0.18))#, loc='lower right')
    #fig.legend(nh, nl,loc='lower right', bbox_to_anchor=(0.85, 0.5))#, loc='lower right')
    l = fig.legend([(nh[1],nh[2],nh[3]),(nh[4],nh[5],nh[6]),(nh[0], )], [r"Left $\pm$ 1 sd",r"Right $\pm$ 1 sd",r"Ref. mean $\pm$ 1 sd"], numpoints=1,
                  handler_map={tuple: HandlerTuple(ndivide=None)},loc='lower right', bbox_to_anchor=(0.9, 0.2))

    plt.savefig(my_dir+f'sub{subject_num}_ik_id_so_{this_action_name}4x3_tighter_stds.pdf', bbox_inches = 'tight')


    # ## This is the sagital plane with calf muscles with all. maybe goes in appendix paper

    # In[ ]:


    fig, axs = refdata.create_axs_dimensions(4, 3, margin= 1.5, header = 1.2, subheigth = 6, subwidth= 6)
    for ax in axs.flatten():
        ax.set_axis_off()

    fig, ax, nh, nl, cref_dic = refdata.plotAX(axcurve_listXXXik, axs, fig, plot_ref_curves=True, plot_std=False, legend=True)
    print(nl)
    #fig.legend(nh[0:2], ["Left","Right"],loc='lower right', bbox_to_anchor=(0.85, 0.18))#, loc='lower right')
    #fig.legend(nh, nl,loc='lower right', bbox_to_anchor=(0.85, 0.5))#, loc='lower right')
    #l = fig.legend([(nh[1],nh[2],nh[3]),(nh[4],nh[5],nh[6]),(nh[0], )], ["Left $\pm$ 1 sd","Right $\pm$ 1 sd","Ref. mean $\pm$ 1 sd"], numpoints=1,
    #              handler_map={tuple: HandlerTuple(ndivide=None)},loc='lower right', bbox_to_anchor=(0.9, 0.2))

    plt.savefig(my_dir+f'sub{subject_num}_ik_id_so_{this_action_name}4x3_tighter_all.pdf', bbox_inches = 'tight')

    plt.close('all')
    return results_dir
