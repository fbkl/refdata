#!/bin/env python3
import logging


def get_ik_graph_params():
    variable_unit = r"Angle[$^{\circ}$]\newline"
    return {
            'pelvis_tilt':{'name':r'Pelvis_Ant_Pst',
                'title':"Pelvic Tilt",
                'plot_it':True,
                'axes_limits':[-50,50],
                'yaxis_name':r"%s$\leftarrow$ Post Ant $\rightarrow$"%variable_unit,
                'position':[0,0],
                'offset':0,
                'scale':(1,-180/3.1415921)}, 
            'pelvis_list':{'name':r'Pelvic_Up_Dn',
                'plot_it':True,
                'axes_limits':[-50,50],
                'title':"Pelvic Obliquity",
                'yaxis_name':r"%s$\leftarrow$ Down Up $\rightarrow$"%variable_unit,
                'position':[0,1],
                'offset':0,
                'scale':(1,-180/3.1415921)}, 
            'pelvis_rotation':{'name':r'Pelvic_Int_Ext',
                'plot_it':True,
                'axes_limits':[-50,50],
                'title':"Pelvic Rotation",
                'yaxis_name':r"%s$\leftarrow$ Ext Int $\rightarrow$"%variable_unit,
                'position':[0,2],
                'offset':0,
                'scale':(1,180/3.1415921)}, 
            'hip_flexion':{'name':r'Hip_Flx_Ext',
                'plot_it':True,
                'axes_limits':[-40,50],
                'title':"Hip Flex/Ext",
                'yaxis_name':r"%s$\leftarrow$ Ext Flex $\rightarrow$"%variable_unit,
                'position':[1,0],
                'offset':0,
                'scale':(1,180/3.1415921)}, 
            'hip_adduction':{'name':r'Hip_Add_Abd',
                'plot_it':True,
                'axes_limits':[-50,50],
                'title':"Hip Add/Abd",
                'yaxis_name':r"%s$\leftarrow$ Abd add $\rightarrow$"%variable_unit,
                'position':[1,1],
                'offset':0,
                'scale':(1,180/3.1415921)}, 
            'hip_rotation':{'name':r'Hip_Int_Ext',
                'plot_it':True,
                'axes_limits':[-50,50],
                'title':"Hip Rotation",
                'yaxis_name':r"%s$\leftarrow$ Ext Int $\rightarrow$"%variable_unit,
                'position':[1,2],
                'offset':0,
                'scale':(1,180/3.1415921)}, 
            'knee_angle':{'name':r'Knee_Flx_Ext',
                'plot_it':True,
                'axes_limits':[-20,80],
                'title':"Knee Flex/Ext",
                'yaxis_name':r"%s$\leftarrow$ Ext Flex $\rightarrow$"%variable_unit,
                'position':[2,0],
                'offset':0,
                'scale':(1,-180/3.1415921)}, 
            'ankle_angle':{'name':r'Ankle_Dor_Pla',
                'plot_it':True,
                'axes_limits':[-50,50],
                'title':"Ankle Dors/Plan",
                'yaxis_name':r"%s$\leftarrow$ Plan Dors $\rightarrow$"%variable_unit,
                'position':[2,1], #'position':[3,0],
                'offset':0,
                'scale':(1,180/3.1415921)}, 
            'subtalar_angle':{'name':r'Foot_Int_Ext',
                'plot_it':False,
                'axes_limits':[-50,50],
                'title':"Foot Progression",
                'yaxis_name':r"%s$\leftarrow$ Ext Int $\rightarrow$"%variable_unit,
                'position':[2,2],
                'offset':0,
                'scale':(1,180/3.1415921)}
        }

def get_ik_graph_params13():
    conv_names13 = get_ik_graph_params()
    conv_names13['pelvis_tilt']['axis_offset'] =13
    conv_names13['hip_flexion']['axis_offset'] =13
    return conv_names13
    
def get_ik_short_graph_params():
    conv_names = get_ik_graph_params()
    short_conv_names = {key:conv_names[key] for key in ['hip_flexion','knee_angle','ankle_angle']}
    short_conv_names['hip_flexion']['position'] = [0,0]
    short_conv_names['knee_angle']['position'] = [0,1]
    short_conv_names['ankle_angle']['position'] = [0,2]
    return short_conv_names

def get_so_graph_params():
    return {
            'glut_med1':	{'name':'Muscle_Ref_glut_med1','title':"Gluteus Med1",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[0,0],'offset':0,'scale':(1,1)},
            'glut_med2':	{'name':'Muscle_Ref_glut_med2','title':"Gluteus Med2",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[0,1],'offset':0,'scale':(1,1)},
            'glut_med3':	{'name':'Muscle_Ref_glut_med3','title':"Gluteus Med3",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[0,2],'offset':0,'scale':(1,1)},
            'glut_min1':	{'name':'Muscle_Ref_glut_min1','title':"Gluteus Min1",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[1,0],'offset':0,'scale':(1,1)},
            'glut_min2':	{'name':'Muscle_Ref_glut_min2','title':"Gluteus Min2",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[1,1],'offset':0,'scale':(1,1)},
            'glut_min3':	{'name':'Muscle_Ref_glut_min3','title':"Gluteus Min3",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[1,2],'offset':0,'scale':(1,1)},
            'semimem':	{'name':'Muscle_Ref_semimem','title':"Semimembranosus",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[2,0],'offset':0,'scale':(1,1)},
            'semiten':	{'name':'Muscle_Ref_semiten','title':"Semitendineus",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[2,1],'offset':0,'scale':(1,1)},
            'bifemlh':	{'name':'Muscle_Ref_bifemlh','title':"biceps femoris lh",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[2,2],'offset':0,'scale':(1,1)},
            'bifemsh':	{'name':'Muscle_Ref_bifemsh','title':"biceps femoris sh",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[3,0],'offset':0,'scale':(1,1)},
            'sar':		{'name':'Muscle_Ref_sar','title':"sartoreus",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[3,1],'offset':0,'scale':(1,1)},
            'add_long':	{'name':'Muscle_Ref_add_long','title':"add longus",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[3,2],'offset':0,'scale':(1,1)},
            'add_brev':	{'name':'Muscle_Ref_add_brev','title':"add brevis",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[4,0],'offset':0,'scale':(1,1)},
            'add_mag1':	{'name':'Muscle_Ref_add_mag1','title':"add mag1",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[4,1],'offset':0,'scale':(1,1)},
            'add_mag2':	{'name':'Muscle_Ref_add_mag2','title':"add mag2",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[4,2],'offset':0,'scale':(1,1)},
            'add_mag3':	{'name':'Muscle_Ref_add_mag3','title':"add mag3",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[5,0],'offset':0,'scale':(1,1)},
            'tfl':		{'name':'Muscle_Ref_tfl','title':"tfl",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[5,1],'offset':0,'scale':(1,1)},
            'pect':		{'name':'Muscle_Ref_pect','title':"pect",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[5,2],'offset':0,'scale':(1,1)},
            'grac':		{'name':'Muscle_Ref_grac','title':"gracius",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[6,0],'offset':0,'scale':(1,1)},
            'glut_max1':	{'name':'Muscle_Ref_glut_max1','title':"Gluteus Max1",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[6,1],'offset':0,'scale':(1,1)},
            'glut_max2':	{'name':'Muscle_Ref_glut_max2','title':"Gluteus Max2",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[6,2],'offset':0,'scale':(1,1)},
            'glut_max3':	{'name':'Muscle_Ref_glut_max3','title':"Gluteus Max3",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[7,0],'offset':0,'scale':(1,1)},
            'iliacus':	{'name':'Muscle_Ref_iliacus','title':"iliacus",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[7,1],'offset':0,'scale':(1,1)},
            'psoas':	{'name':'Muscle_Ref_psoas','title':"psoas",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[7,2],'offset':0,'scale':(1,1)},
            'quad_fem':	{'name':'Muscle_Ref_quad_fem','title':"quadratus femoris",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[8,0],'offset':0,'scale':(1,1)},
            'gem':		{'name':'Muscle_Ref_gem','title':"gem",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[8,1],'offset':0,'scale':(1,1)},
            'peri':		{'name':'Muscle_Ref_peri','title':"peri",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[8,2],'offset':0,'scale':(1,1)},
            'rect_fem':	{'name':'Muscle_Ref_rect_fem','title':"rect fem",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[9,0],'offset':0,'scale':(1,1)},
            'vas_med':	{'name':'Muscle_Ref_vas_med','title':"vastus med",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[9,1],'offset':0,'scale':(1,1)},
            'vas_int':	{'name':'Muscle_Ref_vas_int','title':"vastus int",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[9,2],'offset':0,'scale':(1,1)},
            'vas_lat':	{'name':'Muscle_Ref_vas_lat','title':"vastus lt",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[10,0],'offset':0,'scale':(1,1)},
            'med_gas':	{'name':'Muscle_Ref_med_gas','title':"Medial Gastrocnemius",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[10,1],'offset':0,'scale':(1,1)},
            'lat_gas':	{'name':'Muscle_Ref_lat_gas','title':"Lateral Gastrocnemius",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[10,2],'offset':0,'scale':(1,1)},
            'soleus':	{'name':'Muscle_Ref_soleus','title':"Soleus",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[11,0],'offset':0,'scale':(1,1)},
            'tib_post':	{'name':'Muscle_Ref_tib_post','title':"Tibialis Post.",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[11,1],'offset':0,'scale':(1,1)},
            'flex_dig':	{'name':'Muscle_Ref_flex_dig','title':"Flex. dig.",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[11,2],'offset':0,'scale':(1,1)},
            'flex_hal':	{'name':'Muscle_Ref_flex_hal','title':"Flex. Hal.",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[12,0],'offset':0,'scale':(1,1)},
            'tib_ant':	{'name':'Muscle_Ref_tib_ant','title':"Tibialis Ant.",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[12,1],'offset':0,'scale':(1,1)},
            'per_brev':	{'name':'Muscle_Ref_per_brev','title':"per Brev",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[12,2],'offset':0,'scale':(1,1)},
            'per_long':	{'name':'Muscle_Ref_per_long','title':"per Long",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[13,0],'offset':0,'scale':(1,1)},
            'per_tert':	{'name':'Muscle_Ref_per_tert','title':"per tert",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[13,1],'offset':0,'scale':(1,1)},
            'ext_dig':	{'name':'Muscle_Ref_ext_dig','title':"Ext. Digi.",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[13,2],'offset':0,'scale':(1,1)},
            'ext_hal':	{'name':'Muscle_Ref_ext_hal','title':"Ext. Halux",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[14,0],'offset':0,'scale':(1,1)},
            'ercspn':	{'name':'Muscle_Ref_ercspn','title':"ercspn",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[14,1],'offset':0,'scale':(1,1)},
            'intobl':	{'name':'Muscle_Ref_intobl','title':"intobl",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[14,2],'offset':0,'scale':(1,1)},
            'extobl':	{'name':'Muscle_Ref_extobl','title':"extobl",'plot_it':True,'axes_limits':[0,1.1],'yaxis_name':r"Activation",'position':[15,0],'offset':0,'scale':(1,1)}
            }

def get_so_short_graph_params(use_paper_list=False, use_rename_list=True):
    so_full = get_so_graph_params()
    so_short = {}
    leg_list = {
            'med_gas':[0,0],
            'lat_gas':[0,1],
            'soleus':[1,1],
            'tib_ant':[1,0],
            'tib_post':[11,1],
            'flex_dig':[11,2],
            'flex_hal':[12,0],
            'per_brev':[12,2],
            'per_long':[13,0],
            'per_tert':[13,1],
            'ext_dig':[13,2],
            'ext_hal':[14,0],
            }
    short_list = {
            'med_gas':[0,0],
            'lat_gas':[0,1],
            'soleus':[1,1],
            'tib_ant':[1,0],
            }
    paper_list = {
            'tib_ant':[0,0],
            'med_gas':[0,1],
            'soleus':[0,2],
            'glut_max1':[1,0],
            'vas_med':[1,1]
            }

    rename_list = {}

    use_list = short_list
    if use_paper_list:
        use_list = paper_list
        if use_rename_list:
            rename_list = {'glut_max1':'glu_max'}

    for muscle, pos in use_list.items():
        this_val = so_full[muscle]
        this_val['position'] = pos
        if muscle in rename_list:
            so_short.update({rename_list[muscle]:this_val})
        else:
            so_short.update({muscle:this_val})
    return so_short

def get_so_even_smaller():
    return get_so_short_graph_params(use_paper_list=True, use_rename_list=False)

def get_so_even_smaller_old():
    return {
 'med_gas': {'name': 'Muscle_Ref_NameXXX',
  'title': 'Medial Gastrocnemius',
  'plot_it': False,
  'axes_limits': [0, 1.1],
  'yaxis_name': 'Activation',
  'position': [0, 3],
  'offset':0,
  'scale': (1, 1)},
 'lat_gas': {'name': 'Muscle_Ref_NameXXX',
  'title': 'Lateral Gastrocnemius',
  'plot_it': True,
  'axes_limits': [0, 1.1],
  'yaxis_name': 'Activation',
  'position': [0, 2],
             'offset':0,
  'scale': (1, 1)},
 'soleus': {'name': 'Muscle_Ref_NameXXX',
  'title': 'Soleus',
  'plot_it': True,
  'axes_limits': [0, 1.1],
  'yaxis_name': 'Activation',
  'position': [0, 0],
            'offset':0,
  'scale': (1, 1)},
 'tib_ant': {'name': 'Muscle_Ref_NameXXX',
  'title': 'Tibialis Ant.',
  'plot_it': True,
  'axes_limits': [0, 1.1],
  'yaxis_name': 'Activation',
  'position': [0, 1],
             'offset':0,
  'scale': (1, 1)},
}


def get_id_all_graph_params(weight):
    variable_unit = "Torque[Nm/kg]\n"
    return {
            'pelvis_tilt': {'name': 'Pelvis_Ant_Pst',
                'title': 'Pelvic Tilt',
                'plot_it': True,
                'axes_limits': [-5, 5],
                'yaxis_name': '%s$\\leftarrow$ Post Ant $\\rightarrow$'%variable_unit,
                'position': [0, 0],
                'offset':0,
                'scale': (1,1/weight)},
            'pelvis_list': {'name': 'Pelvic_Up_Dn',
                'plot_it': True,
                'axes_limits': [-5, 5],
                'title': 'Pelvic Obliquity',
                'yaxis_name': '%s$\\leftarrow$ Down Up $\\rightarrow$'%variable_unit,
                'position': [0, 1],
                'offset':0,
                'scale': (1,1/weight)},
            'pelvis_rotation': {'name': 'Pelvic_Int_Ext',
                'plot_it': True,
                'axes_limits': [-5, 5],
                'title': 'Pelvic Rotation',
                'yaxis_name': '%s$\\leftarrow$ Ext Int $\\rightarrow$'%variable_unit,
                'position': [0, 2],
                'offset':0,
                'scale': (1,1/weight)},
            'hip_flexion': {'name': 'Hip_Flx_Ext',
                'plot_it': True,
                'axes_limits': [-3, 4],
                'title': 'Hip Flex/Ext',
                'yaxis_name': '%s$\\leftarrow$ Ext Flex $\\rightarrow$'%variable_unit,
                'position': [1, 0],
                'offset':0,
                'scale': (-1,1/weight)},
            'hip_adduction': {'name': 'Hip_Add_Abd',
                'plot_it': True,
                'axes_limits': [-5, 5],
                'title': 'Hip Add/Abd',
                'yaxis_name': '%s$\\leftarrow$ Abd add $\\rightarrow$'%variable_unit,
                'position': [1, 1],
                'offset':0,
                'scale': (-1,1/weight)},
            'hip_rotation': {'name': 'Hip_Int_Ext',
                'plot_it': True,
                'axes_limits': [-5, 5],
                'title': 'Hip Rotation',
                'yaxis_name': '%s$\\leftarrow$ Ext Int $\\rightarrow$'%variable_unit,
                'position': [1, 2],
                'offset':0,
                'scale': (1,1/weight)},
            'knee_angle': {'name': 'Knee_Flx_Ext',
                'plot_it': True,
                'axes_limits': [-3, 1.5],
                'title': 'Knee Flex/Ext',
                'yaxis_name': '%s$\\leftarrow$ Ext Flex $\\rightarrow$'%variable_unit,
                'position': [2, 0],
                'offset':0,
                'scale': (-1,-1/weight)},
            'ankle_angle': {'name': 'Ankle_Dor_Pla',
                'plot_it': True,
                'axes_limits': [-3, 1],
                'title': 'Ankle Dors/Plan',
                'yaxis_name': '%s$\\leftarrow$ Plan Dors $\\rightarrow$'%variable_unit,
                'position': [2, 1],
                'offset':0,
                'scale': (-1,1/weight)},
            'subtalar_angle': {'name': 'Foot_Int_Ext',
                'plot_it': True,
                'axes_limits': [-5, 5],
                'title': 'Foot Progression',
                'yaxis_name': '%s$\\leftarrow$ Ext Int $\\rightarrow$'%variable_unit,
                'position': [2, 2],
                'offset':0,
                'scale': (1,-1/weight)},
            'mtp_angle': {'name': 'Angle_',
                'plot_it': True,
                'axes_limits': [-0.005, 0.005],
                'title': 'Toes ',
                'yaxis_name': '%s$\\leftarrow$ ??? ??? $\\rightarrow$'%variable_unit,
                'position': [3, 0],
                'offset':0,
                'scale': (1,1/weight)}
            }

def get_id_sagittal_graph_params(weight):
    return sagittal_only(get_id_all_graph_params(weight))

def sagittal_only(conv_names):
    sag_names = {}
    sagittal_joints_list = ["hip_flexion","knee_angle","ankle_angle"]
    position_list = [[0,0],[0,1],[0,2]] ##idk..
    for joint_name, joint_pos in zip(sagittal_joints_list, position_list):
        conv_names[joint_name]["plot_it"] = True
        conv_names[joint_name]["position"] = joint_pos
        sag_names.update({joint_name:conv_names[joint_name]})
    
    return sag_names

def get_id_standard_graph_params(weight):
    conv_names = get_id_all_graph_params(weight)
    for joint_name in conv_names.keys():
        m = conv_names[joint_name]["scale"][0]  
        n = conv_names[joint_name]["scale"][1]  
        if m*n == -1:
            conv_names[joint_name]["scale"] = (-1,1/weight)
            conv_names[joint_name]["axes_limits"]=[-conv_names[joint_name]["axes_limits"][1],-conv_names[joint_name]["axes_limits"][0]]
    return conv_names

def get_id_graph_params(weight): ## in my mind this should be the default though
    logging.warn("Deprecated: dont use, use get_id_sagittal_graph_params instead.")
    return get_id_sagittal_graph_params(weight)

def generate_grf_conv_names(left_or_right,weight, percent_of_bw=True): # 0 or 1
    ##this is a pain because it doesnt follow the convention for the rest of the stuff
    ## actually instead of left_or_right, you can change htis to be a string and then it will maybe work for the force plate stuff. though those files have both grfs in the same thing, so it will be a bit different no matter what...
    a = ["1_", ""]
    b = "ground_"
    c = ["force_p","force_v","torque_"]
    d = ["x","y","z"]
    ## do all the permutationS!
    
    #listo = []
    conv_dic = {}
    i=0

    for ci in c:
        if ci == c[0]:
            the_title = "Force Point"
            the_axes_lims = (-.6,.6) #idk
            the_yname= "Meter"
            the_scale = 1
        if ci == c[1]:    
            the_title = "Force"
            the_axes_lims = (-200,200) #idk
            if percent_of_bw:
                the_yname = "\% of Bw"
                the_scale = 1/9.81/weight
            else:#g
                the_yname= "Newton/Kg"
                the_scale = 1/weight
        if ci == c[2]:    
            the_title = "Torque"
            the_axes_lims = (-10,10) #idk
            the_yname= "Nm"
            the_scale = 1
        
        for di in d:
            this_axes_lims = the_axes_lims
            if di == d[0] and ci == c[1]:
                the_title ="Force\n(Anteroposterior shear)"
                this_axes_lims = (-0.5,1) #iAdk
            if di == d[1] and ci == c[1]:
                the_title ="Force\n(Vertical Force)"
                this_axes_lims = (0,1.5) #iAdk
            if di == d[2] and ci == c[1]:
                the_title ="Force\n(Mediolateral shear)"
                this_axes_lims = (-0.5,0.5) #iAdk
            
            namename= a[left_or_right]+b+ci+di
            #listo.append(a[left_or_right]+b+ci+di)
            conv_dic.update({namename :{'name':"the_%s"%(b+ci+di),
                "plot_it":True,
                "title": "%s %s"%(the_title,di),
                "axes_limits": this_axes_lims,
                "yaxis_name":the_yname,
                "position": [i//3,i%3],
                "offset":0,
                "scale":(1,the_scale) }}
                )
            i+=1
    
    
    return conv_dic
