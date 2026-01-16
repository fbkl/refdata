#!/usr/bin/env python
# coding: utf-8


import os
import sys
sys.path.append("../refdata")
from refdata import refdata
from refdata import metrics
from refdata import my_log
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import traceback

from matplotlib.lines import Line2D
from itertools import cycle
from matplotlib.legend_handler import HandlerTuple
from refdata.metrics import header as my_print

import pickle
class HandlerMyTuple(HandlerTuple):
    
    def create_artists(self, legend, orig_handle,
                       xdescent, ydescent, width, height, fontsize, trans):
        center = 0.5 * width - 0.5 * xdescent, 0.5 * height - 0.5 * ydescent
       

        print(orig_handle)
        #p = mpatches.
        #p = mpatches.Shadow()
        #p2 = mpatches.Ellipse(xy=center, width=width + xdescent,
        #                     height=height + ydescent-10)
        #p = nh[0]
        #self.update_prop(p, orig_handle, legend)
        #p.set_transform(trans)
        if len(orig_handle)==30:
            #print(dir(orig_handle[0]))
            p = Line2D([0,10],[0,1], color=orig_handle[0].get_color(),style=orig_handle[0].get_)
            p.set_transform(trans)
            return [p]
        else:
            # docstring inherited
            handler_map = legend.get_legend_handler_map()
    
            if self._ndivide is None:
                ndivide = len(orig_handle)
            else:
                ndivide = self._ndivide
    
            if self._pad is None:
                pad = legend.borderpad * fontsize
            else:
                pad = self._pad * fontsize
    
            if ndivide > 1:
                height = (height - pad * (ndivide - 1)) / ndivide
    
            yds_cycle = cycle(ydescent - (height + pad) * np.arange(ndivide))
    
            a_list = []
            for handle1 in orig_handle:
                handler = legend.get_legend_handler(handler_map, handle1)
                _a_list = handler.create_artists(
                    legend, handle1,
                     xdescent, next(yds_cycle), width, height, fontsize, trans)
                a_list.extend(_a_list)
    
            return a_list



def ptupl(t):
    return f"{t[0]}x{t[1]}"


refdata.plt.rcParams['figure.figsize'] = [12, 5]
refdata.ROW_OF_FLOTS = 1



def make_dir(base):
    path, n = base, 1
    while os.path.exists(path):
        path = f"{base}_{n}"
        n+=1
    os.makedirs(path)
    return path

def graphs_and_metrics( myImuLumpList, myMocapLumpList, subject_num, weight, this_action_name, results_dir = None, ext_sync = [], valid_step_list_list=[], get_roted_fun=metrics.get_roted,mocap_times=False):
    
    plt.close('all')
    
    if not results_dir:
        results_dir = make_dir("results")
    
    my_dir = os.path.join(results_dir,subject_num, this_action_name) + "/"
    os.makedirs(my_dir)
    my_log.CONTEXT = f"{subject_num} {this_action_name} {my_dir}"

    mySL = metrics.Dismissed(weight=weight, save_fig_dir=my_dir, action=this_action_name, get_roted_fun=get_roted_fun)

    mySL.mocap_times=mocap_times

    refdata.logging.info(mySL.save_fig_dir)

    mySL.set_by_two_lists_of_lumps(myImuLumpList, myMocapLumpList, ext_sync )

    
    #mySL.manual_segmentation(manual_segmentation_list_list)
    
    mySL.run_analysis("ik", auto_compute_metrics=True)

    mySL.which_steps_do_i_plot(valid_step_list_list)

    mySL.run_analysis("id", auto_compute_metrics=True)

    grfconv_names = []
    grfconv_names.append(refdata.graph_params.generate_grf_conv_names(0,weight))
    grfconv_names.append(refdata.graph_params.generate_grf_conv_names(1,weight))

    ik_conv_names = refdata.graph_params.get_ik_graph_params()
    short_ik_conv_names = refdata.graph_params.get_ik_short_graph_params()
    id_conv_names = refdata.graph_params.get_id_all_graph_params(weight)
    id_short_conv_names = refdata.graph_params.get_id_graph_params(weight)
    id_conv_names_sag = refdata.graph_params.sagittal_only(refdata.graph_params.get_id_standard_graph_params(weight))
    so_conv_names = refdata.graph_params.get_so_graph_params()
    ccc_imu = refdata.graph_params.get_so_short_graph_params(use_paper_list=True, use_rename_list=False)
    ccc_so = refdata.graph_params.get_so_short_graph_params(use_paper_list=True)

    dict_of_conv_names = {
            "grf":[ (grfconv_names, (3,3) )],
            "ik":[(ik_conv_names, (3,3)), (short_ik_conv_names, (1,3))],
            "id":[(id_conv_names, (4,3)), (id_short_conv_names, (1,3)), (id_conv_names_sag, (1,3))], 
            "so":[((so_conv_names,so_conv_names), (16,3)), ((ccc_imu, ccc_so), (2,3))]
            }

    ## untested!
    #asSORefData1 = pickle.load( open( f"RTValidation_Extra/{subject_vicon_num}/so_ref_{this_action_name}_data_s{subject_num}.p", "rb" ) )

    curves_dictionary = {}

    for mode in ["grf", "ik", "id", "so"]:
        os.makedirs(my_dir+f"/{mode}/")
        for i, (conv_name_i, fig_size) in enumerate(dict_of_conv_names[mode]):
            asRefData = [None,None]
            all_XXX_curves_for_this_person = [None, None]
            RR = [None, None]
            for j, stream in enumerate(["imu", "mocap"]):
                reference_caption = f"{stream.capitalize()} {subject_num}"
                if mode== "so"  and stream == "mocap":
                    reference_caption = f"EMG {subject_num}"
                if mode== "grf"  and stream == "mocap":
                    ## i can load the emg here for so and maybe do something for force plate idk
                    continue
                conv_name_to_use = conv_name_i
                if mode=="so":
                    conv_name_to_use = conv_name_i[j] ## hack because the names are different. if it still doesnt work, try changing the order in line 127,128
                all_XXX_curves_for_this_person[j] = mySL.gen_action_plots(mode,stream, conv_names = conv_name_to_use)

                pick__ = mode+"_"+stream+"_"+str(i)
                curves_dictionary[pick__] = all_XXX_curves_for_this_person[j]
                asRefData[j] = refdata.RefData(this_action_name)
                for std_or_not, std_str in [(False, "all"), (True, "std")]:
                    my_print(pick__+std_str)
                    RR[j] = refdata.plot_std_plots(all_XXX_curves_for_this_person[j], plot_std=std_or_not, ref=asRefData[j], subject_identifier=reference_caption, subplot_grid = fig_size,)
                    plt.savefig(my_dir+f'/{mode}/sub{subject_num}_{mode}_{stream}_{this_action_name}{ptupl(fig_size)}_tighter_{std_str}_{i}.pdf', bbox_inches = 'tight')
                    plt.close()
                    
                ## i dont think it makes a difference if it is std or all for the gencurves thing
                asRefData[j].reference_curve_dict = RR[j][4]

                curves_dictionary[mode+"_"+stream+"_"+str(i)+"_ref"] = asRefData[j]
                pickle.dump(all_XXX_curves_for_this_person[j],open(my_dir+f"/{mode}/{mode}{this_action_name}{subject_num}_{stream}{i}.p","wb"))

            my_print("Imu + Mocap")

            ## maybe i need to check something 
            _ = refdata.plot_std_plots(all_XXX_curves_for_this_person[0], plot_std=False, ref=asRefData[1], subplot_grid = fig_size,)

            my_print("Saving IMU + Mocap")
            plt.savefig(my_dir+f'{mode}/sub{subject_num}_{mode}_{this_action_name}_imu_mocap_ref_{ptupl(fig_size)}_all{i}.pdf', bbox_inches = 'tight')
            plt.close()

        
            del(all_XXX_curves_for_this_person)




    plt.rcParams['figure.figsize'] = [8, 10]
    #axcurve_list = refdata.creat_axs(curves_dictionary["ik_imu_0"], ref= refdata.GaitIKRefData(this_action_name))
    axcurve_list = refdata.creat_axs(curves_dictionary["ik_imu_0"], ref= curves_dictionary["ik_mocap_0_ref"])

    fig, ax =  refdata.create_axs_dimensions(3,3) 
    fig, ax, nl, legend, cref_dic, Z = refdata.plotAX(axcurve_list, ax, fig)

    fig.legend(nl, legend,loc='center left', bbox_to_anchor=(1, 0.5))

    #axcurve_list_id2 = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["id_imu_0"], ref=refdata.IdData(this_action_name)),3)
    axcurve_list_id2 = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["id_imu_0"], ref=curves_dictionary["id_mocap_0_ref"]),3)

    axcurve_list.extend(axcurve_list_id2)

    fig, ax =  refdata.create_axs_dimensions(8,3) 

    fig, ax, nl, legend, cref_dic,Z = refdata.plotAX(axcurve_list, ax, fig)

    #axcurve_list_so2 = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["so_imu_1"],ref=refdata.SoData(this_action_name)),6)
    axcurve_list_so2 = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["so_imu_1"],ref=curves_dictionary["so_mocap_1_ref"]),6)
    axcurve_list.extend(axcurve_list_so2)


    # In[ ]:


    fig, axs = refdata.create_axs_dimensions(8, 3, margin= 1.5, header = 1.2, subheigth = 6, subwidth= 6)

    #refdata.plt.rcParams['figure.figsize'] = [12, 4]
    #fig, ax, nl, legend, cref_dic = refdata.plotAX(axcurve_list, axs, fig)
    fig, ax, nl, legend, cref_dic, Z = refdata.plotAX(axcurve_list, axs, fig, plot_ref_curves=True)

    my_print("8x3")

    plt.savefig(my_dir+f'sub{subject_num}_ik_id_so_{this_action_name}8x3_tighter_stds.pdf', bbox_inches = 'tight')
    refdata.plt.close()
    # In[ ]:


    ### This is the version for the paper

    if False:
        axcurve_listXXXik = refdata.creat_axs(curves_dictionary["ik_imu_1"], ref= refdata.GaitIKRefData(this_action_name))

        axcurve_listXXXid = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["id_imu_1"],ref=refdata.IdData(this_action_name)),1)

        axcurve_listXXXso = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["so_imu_1"],ref=refdata.SoData(this_action_name)),2)
    
    curves_dictionary["ik_mocap_1_ref"].ref_color1 = 'silver'
    curves_dictionary["id_mocap_1_ref"].ref_color1 = 'silver'
    curves_dictionary["so_mocap_1_ref"].ref_color1 = 'darkseagreen'

    axcurve_listXXXik =                             refdata.creat_axs(curves_dictionary["ik_imu_1"], ref= curves_dictionary["ik_mocap_1_ref"])

    axcurve_listXXXid = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["id_imu_1"], ref= curves_dictionary["id_mocap_1_ref"]),1)

    axcurve_listXXXso = refdata.apply_offset_to_axs(refdata.creat_axs(curves_dictionary["so_imu_1"], ref= curves_dictionary["so_mocap_1_ref"]),2)


    axcurve_listXXXik.extend(axcurve_listXXXid)
    axcurve_listXXXik.extend(axcurve_listXXXso)

    mpl.rcParams['figure.dpi'] = 300

    fig, axs = refdata.create_axs_dimensions(4, 3, margin= 1.5, header = 1.2, subheigth = 6, subwidth= 6)
    for ax in axs.flatten():
        ax.set_axis_off()

    fig, ax, nh, nl, cref_dic, Z = refdata.plotAX(axcurve_listXXXik, axs, fig, plot_ref_curves=True)
    #fig.legend(nh[0:2], ["Left","Right"],loc='lower right', bbox_to_anchor=(0.85, 0.18))#, loc='lower right')
    #fig.legend(nh, nl,loc='lower right', bbox_to_anchor=(0.85, 0.5))#, loc='lower right')
    try:
        refdata.logging.info(nh)
        refdata.logging.info(nl)
        ld = {}
        for ai, bi, in zip(nl,nh):
            ld.update({ai:bi})
        #'EMG EX02RE 1 std ', 'Left +1 SD', 'Left -1 SD', 'Left Mean', 'Mocap EX02RE 1 std ', 'Right +1 SD', 'Right -1 SD', 'Right Mean'
        red_ = (ld['Left +1 SD'],ld['Left Mean'],ld['Left -1 SD'])
        blue_ = (ld['Right +1 SD'],ld['Right Mean'],ld['Right -1 SD'])
        for ldil, ldih in ld.items():
            if "Mocap" in ldil:
                vi_ = (ldih)
                break
        em_ = None
        for ldil, ldih in ld.items():
            if "EMG" in ldil:
                em_ = (ldih)
                break
        legend_l = fig.legend([red_,blue_,vi_,em_], [r"Left $\pm$ 1 sd", r"Right $\pm$ 1 sd", r"Vicon Ref. mean $\pm$ 1 sd", "EMG Reference"], numpoints=1, handler_map={tuple: HandlerMyTuple(ndivide=None)},loc='lower center', bbox_to_anchor=(0.8, 0.1))
        print(legend_l)
    except:
        traceback.print_exc()
        refdata.logging.error("Failed to draw nice legend. You need to set the Reference colors and names correctly for this to work!")
    #l = fig.legend([(nh[1],nh[2],nh[3]),(nh[4],nh[5],nh[6]),(nh[0], )], [r"Left $\pm$ 1 sd",r"Right $\pm$ 1 sd",r"Ref. mean $\pm$ 1 sd"], numpoints=1,
    #              handler_map={tuple: HandlerMyTuple(ndivide=None)},loc='lower right', bbox_to_anchor=(0.9, 0.2))

    plt.savefig(my_dir+f'sub{subject_num}_ik_id_so_{this_action_name}4x3_tighter_stds.pdf', bbox_inches = 'tight')

    my_print("paper_version")
    # ## This is the sagital plane with calf muscles with all. maybe goes in appendix paper

    # In[ ]:


    fig, axs = refdata.create_axs_dimensions(4, 3, margin= 1.5, header = 1.2, subheigth = 6, subwidth= 6)
    for ax in axs.flatten():
        ax.set_axis_off()

    fig, ax, nh, nl, cref_dic, Z = refdata.plotAX(axcurve_listXXXik, axs, fig, plot_ref_curves=True, plot_std=False, legend=True)
    #print(nl)
    #print(Z)
    #fig.legend(nh[0:2], ["Left","Right"],loc='lower right', bbox_to_anchor=(0.85, 0.18))#, loc='lower right')
    #fig.legend(nh, nl,loc='lower right', bbox_to_anchor=(0.85, 0.5))#, loc='lower right')
    #l = fig.legend([(nh[1],nh[2],nh[3]),(nh[4],nh[5],nh[6]),(nh[0], )], ["Left $\pm$ 1 sd","Right $\pm$ 1 sd","Ref. mean $\pm$ 1 sd"], numpoints=1,
    #              handler_map={tuple: HandlerTuple(ndivide=None)},loc='lower right', bbox_to_anchor=(0.9, 0.2))

    plt.savefig(my_dir+f'sub{subject_num}_ik_id_so_{this_action_name}4x3_tighter_all.pdf', bbox_inches = 'tight')

    my_print("all curves, sort of unformatted")
    plt.close('all')
    del(mySL)
    del(curves_dictionary)
    return results_dir
