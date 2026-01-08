import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import signal, stats
from scipy.spatial.transform import Rotation as R
from . import my_log
import traceback

logging = my_log.logging
logger = my_log.logger

vv = my_log.vlog

logger.info("Loading metrics")

PA = "pelvis_tilt"
PB = "pelvis_list"

do_rename = False

def change_do_rename():
    global do_rename
    global PA
    global PB
    do_rename = True
    PA = "pelvis_tilt_x"
    PB = "pelvis_obliquity"

from ipywidgets import FloatSlider, FloatText, Button, HBox, VBox, Output, Layout
import ipywidgets as widgets

interactive = False

def interactive_display(ui_control):
    if interactive:
        display(ui_control)

def get_roted_from_claude_because_im_stupid(this_df, in_degrees=False, angle_cols=[PA, PB, 'pelvis_rotation']):
    
    """
    Removes initial yaw offset from pelvis angles.
    Assumes XYZ body-fixed (intrinsic) Euler angles in DEGREES.
    """
    # Get first frame angles
    angles_deg = this_df[angle_cols].values  # shape: (n_frames, 3)
    initial_angles = angles_deg[0, :]
    
    # Get the initial yaw offset (Z rotation)
    initial_yaw = initial_angles[2]
    
    # Create rotation to remove this yaw
    # We want to rotate about Z by -initial_yaw
    yaw_correction = R.from_euler('z', -initial_yaw, degrees=True)
    
    # Convert all frames to rotation objects (body-fixed XYZ = intrinsic 'xyz')
    rotations = R.from_euler('xyz', angles_deg, degrees=True)
    
    # Apply correction: R_corrected = R_yaw_correction * R_original
    corrected_rotations = yaw_correction * rotations
    
    # Convert back to Euler angles
    corrected_angles = corrected_rotations.as_euler('xyz', degrees=True)
    
    # Put back in dataframe
    df_corrected = this_df.copy()
    df_corrected[angle_cols] = corrected_angles
    
    return df_corrected


def get_roted(this_df, in_degrees=False):
    initial_rotation = this_df['pelvis_rotation'].iloc[0]
    
    # Global Y-axis correction
    R_correction = R.from_euler('Y', -initial_rotation, degrees=in_degrees)
    
    angles = []
    for i in range(len(this_df)):
        tilt = this_df[PA].iloc[i]
        obl = this_df[PB].iloc[i]
        rot = this_df['pelvis_rotation'].iloc[i]
        
        # Build rotation using EXTRINSIC ZYX
        R_current = R.from_euler('ZYX', [tilt, rot, obl], degrees=in_degrees)
        
        # Apply correction IN SPACE FRAME (left multiply)
        R_corrected = R_correction * R_current
        
        # Extract back as ZYX EXTRINSIC
        corrected = R_corrected.as_euler('ZYX', degrees=in_degrees)
        angles.append(corrected)
    
    angles = np.array(angles)
    
    this_df[PA] = angles[:,0]  # tilt
    this_df['pelvis_rotation'] = angles[:,1]  # rotation  
    this_df[PB] = angles[:,2]  # list
    
    return this_df


def get_rotedi2(this_df, in_degrees=False):
    initial_rotation = this_df['pelvis_rotation'].iloc[0]
    
    # Determine if we need +90 or -90 correction
    if abs(initial_rotation - 90) < abs(initial_rotation - (-90)):
        # Mocap is +90° off
        correction = 90
    else:
        # Mocap is -90° off
        correction = -90
    
    if in_degrees:
        correction_rad = np.radians(correction)
    else:
        correction_rad = correction
    
    this_df_copy = this_df.copy()
    
    if abs(correction_rad - np.pi/2) < 0.1:  # +90 degrees
        # Swap tilt and list, adjust signs
        this_df_copy[PA] = -this_df[PB].values  # tilt = -list
        this_df_copy[PB] = this_df[PA].values   # list = tilt
        this_df_copy['pelvis_rotation'] = this_df['pelvis_rotation'].values - correction
        
    elif abs(correction_rad + np.pi/2) < 0.1:  # -90 degrees
        # Swap tilt and list, adjust signs
        this_df_copy[PA] = this_df[PB].values   # tilt = list
        this_df_copy[PB] = -this_df[PA].values  # list = -tilt
        this_df_copy['pelvis_rotation'] = this_df['pelvis_rotation'].values - correction
    
    return this_df_copy



def get_roted1(this_df, in_degrees=False):
    initial_rotation = this_df['pelvis_rotation'].iloc[0]
   
    if np.abs(initial_rotation) < 10*np.pi/180: ## smaller than pm 10 degrees we do nothing
        logger.info(f"very small initial rotation {initial_rotation} so im not fixing it")
        return this_df
    # Global Y-axis correction (±90°)
    R_correction = R.from_euler('Y', -initial_rotation, degrees=in_degrees)
    
    angles = []
    for i in range(len(this_df)):
        tilt = this_df[PA].iloc[i]
        obl = this_df[PB].iloc[i]
        rot = this_df['pelvis_rotation'].iloc[i]
        
        # SPACE rotation sequence: Z(tilt), Y(rotation), X(list)
        R_current = R.from_euler('ZYX', [tilt, rot, obl], degrees=in_degrees)
        
        R_corrected = R_correction * R_current
        
        corrected = R_corrected.as_euler('ZYX', degrees=in_degrees)
        angles.append(corrected)
    
    angles = np.array(angles)
    
    this_df[PA] = angles[: ,0]  # tilt
    this_df['pelvis_rotation'] = angles[:,1]  # rotation
    this_df[PB] = angles[:,2]  # list
    
    return this_df


def get_roted0(this_df,in_degrees=False):
    return this_df

    logger.info("="*80)
    logger.info("rotating now")
    logger.info("="*80)
    initial_rotation = this_df['pelvis_rotation'].iloc[0]

    vv('initial_rotation')
    R_correction = R.from_euler('Y', -initial_rotation, degrees=in_degrees)
    #R_correctionA = R.from_euler('x', initial_rotation, degrees=in_degrees).inv()
    #R_correctionB = R.from_euler('y', initial_rotation, degrees=in_degrees).inv()
    #R_correctionC = R.from_euler('z', initial_rotation, degrees=in_degrees).inv()

    angles = []
    for i in range(len(this_df)):
        tilt = this_df[PA].iloc[i]
        obl = this_df[PB].iloc[i]
        rotation = this_df['pelvis_rotation'].iloc[i]

        # For SPACE (extrinsic) rotations matching your C++ code:
        # Order: Z(tilt), Y(rotation), X(list)
        R_current = R.from_euler('ZYX', [tilt, rotation, obl], degrees=in_degrees)
        #R_current = R.from_euler('zxy', [obl, rot, tilt], degrees=in_degrees)
        #R_correct = R_correction * R_current
        #R_a = R.from_euler('y', rot, degrees=in_degrees)
        #R_b = R.from_euler('x', obl, degrees=in_degrees)
        #R_c = R.from_euler('z', tilt, degrees=in_degrees)

        R_corrected = R_correction * R_current
        #R_correctB = R_correctionB * R_current
        #R_correctC = R_correctionC * R_current
        
        corrected = R_corrected.as_euler('ZYX', degrees=in_degrees)
        #correctedA = R_correctA.as_euler('zxy', degrees=in_degrees)
        #correctedB = R_correctB.as_euler('zxy', degrees=in_degrees)
        #correctedC = R_correctC.as_euler('zxy', degrees=in_degrees)
        
        if i == 0:
            logger.info("try to make sense of this")
            #print([obl, rotation, tilt])
            vv('R_current')
            #print(R_a*R_b*R_c)
            #print(R_c*R_b*R_a)
            vv('R_corrected')
            #vv('R_correctB')
            #vv('R_correctC')
            vv('corrected')
            #vv('correctedB')
            #vv('correctedC')
        angles.append(corrected)
    angles = np.array(angles)
    
    this_df[PA] = angles[: ,0]  # tilt
    this_df['pelvis_rotation'] = angles[:,1]  # rotation
    this_df[PB] = angles[:,2]  # list
    
    
    return this_df


def parse_header(this_file):
    print(f"=== {this_file} FILE ===")
    skip_rows = 0
    scale = 1
    is_ik = False
    if "tau" in this_file:
        scale = 1
        is_ik = False
    if "ik.sto" in this_file:
        is_ik = True
    with open(this_file, 'r') as f:
        for i in range(20):  # First 20 lines
            this_line = f.readline().rstrip()
            #print(f"{i}: {this_line}")
            if "endheader" in this_line:
                skip_rows = i+1
            if "inDegrees=yes" in this_line:
                scale = np.pi/180
            if "time" in this_line and "moment" in this_line:
                scale = 1
                is_ik = False
    return skip_rows, scale, is_ik

def valid(maybe_df):
    if type(maybe_df) == type(pd.DataFrame()):
        return True
    else:
        return False

from contextlib import nullcontext


class SyncedTrials:
    def __init__(self, imu_files, mocap_files, lag = [] , is_ik=False, save_fig_dir="./", mode="unknown_mode", index=-1 , get_roted_fun=None):
        self.get_roted_fun = get_roted_fun
        self.mode = mode
        self.index = index
        self.save_fig_dir=save_fig_dir
        my_stack = "".join(traceback.format_stack())
        #logging.error(f"SyncedTrials savefigdir: {self.save_fig_dir}\n{my_stack}")
        self.output = nullcontext()
        self.my_files = [imu_files, mocap_files]


        self.is_ik = is_ik
        self.curve_suffix = ""
        self.master = False
        self.valid_steps_created = False
        self.min_size_ext = None

        self.step_seg_l_list = []
        self.step_seg_r_list = []
        self.valid_steps_l = []
        self.valid_steps_r = []


        self.min_size_master = None
        self.fig = None
        if type(imu_files) == type(""):
            imu_files = [imu_files]
        if type(mocap_files) == type(""):
            mocap_files = [mocap_files]


        self.scale_mocap = np.pi/180

        self.scale_imu = np.pi/180
       
        # the mocap pelvis has a different frame, we need to rename them :
        ## this isnt working but whatever
        rename_map_i = {
            "pelvis_tilt": PA,
            "pelvis_list": PB,
            "pelvis_rotation": "pelvis_rotation"
        }
        
        rename_map_m = {
            "pelvis_tilt": PA,
            "pelvis_list": PB,
            "pelvis_rotation": "pelvis_rotation"
        }


        #is_ik = False ##i'll just tell it, wth

        t_starts = []
        t_ends = []

        imu_data = [None for i in range(len(imu_files))]

        for i, this_imu_file in enumerate(imu_files):
            if not this_imu_file:
                continue
            imu_skip_rows, self.scale_imu, _ = parse_header(this_imu_file)
            # Load IMU .sto files (OpenSim format)
            imu_data[i] = pd.read_csv(this_imu_file, delimiter='\t', skiprows=imu_skip_rows)  
            if "tau" in this_imu_file: ## i assume is id
                self.curve_suffix = "_moment"
                for col in imu_data[i].columns:
                    if col == "time":
                        continue
                    imu_data[i] = imu_data[i].rename(columns={col:col+"_moment"})
            
            if do_rename:
                imu_data[i] = imu_data[i].rename(columns=rename_map_i)
            # Get the first timestamp
            t0 = imu_data[i]["time"].iloc[0]  # .iloc[0] not .index[0]

            # Subtract offset
            imu_data[i]["time"] = imu_data[i]["time"] - t0

            # NOW set it as index
            imu_data[i] = imu_data[i].set_index("time")

            t_starts.append(imu_data[i].index[0])
            t_ends.append(imu_data[i].index[-1])
            
        mocap_data = [None for i in range(len(mocap_files))]

        self.mask_mocap = None
        for i, this_mocap_file in enumerate(mocap_files):
            if not this_mocap_file:
                continue
            mocap_skip_rows, self.scale_mocap, _ = parse_header(this_mocap_file)

            # Load Vicon .mot files
            mocap_data[i] = pd.read_csv(this_mocap_file, delimiter='\t', skiprows=mocap_skip_rows)
            
            if do_rename:
                mocap_data[i] = mocap_data[i].rename(columns=rename_map_m)
            
            # i want to save the mocap data begining and end. when i dont have mocap, i dont have a reference. 
            # if i compare to padded values im messing things up
            # so after everything is done I will use this to slice the output

            self.mask_mocap = [mocap_data[i]["time"].iloc[0], mocap_data[i]["time"].iloc[-1]]
            print(f"mocap time mask (only beginning and end, if there are also nans in the middle this will fail)\n  {self.mask_mocap}")

            # mocap is already at wall time
            mocap_data[i] = mocap_data[i].set_index('time')
            
            if self.scale_mocap < 0.9 or self.scale_mocap > 1.1: ## this will mess up the translations
                logger.info("regularizing mocap data")
                mocap_data[i] *= self.scale_mocap
                self.scale_mocap = 1 
            else:
                logger.info("mocap data didnt need fixing???")

            t_starts.append(mocap_data[i].index[0])
            t_ends.append(mocap_data[i].index[-1])

        # plot them raw
        if False: # this has time as a column, so it will show epoch times as something to 10⁹... not great
            imu_data.plot()
            mocap_data.plot()
            plt.show()

  
        
        # plot them as wall timed
        if False: 
            imu_data.plot()
            mocap_data.plot()
            plt.show()


        # Create a common time base - use the overlapping period
        # Say 100 Hz exactly
        fs = 100  # Hz
        self.t_start = min(t_starts)
        self.t_end = max(t_ends)

        print(self.t_start, self.t_end)
        common_time = np.arange(self.t_start, self.t_end, 1/fs)
        if valid(imu_data[0]):
            self.imu_resampled = imu_data[0].reindex(common_time, method='nearest').interpolate(method='linear')
        else:
            self.imu_resampled = None
        if valid(mocap_data[0]):
            self.mocap_resampled = mocap_data[0].reindex(common_time, method='nearest').interpolate(method='linear')
        else:
            self.mocap_resampled = None

        if valid(imu_data[0]) and valid(mocap_data[0]):
            logger.warning("this should be done with a mapped one to one, easier said then done though")
            all_common_joints = [col for col in self.imu_resampled.columns if col in self.mocap_resampled.columns]
            # but we exclude the translations
            self.common_joints = []
            for joint in all_common_joints:
                if "_tx" == joint[-3:] or "_ty" == joint[-3:] or "_tz" == joint[-3:]:
                    pass
                else:
                    self.common_joints.append(joint)
        elif valid(imu_data[0]):
            self.common_joints = imu_data[0].columns
        elif valid(mocap_data[0]):
            self.common_joints = mocap_data[0].columns
        else:
            self.common_joints = []
    
        #common_joints

        if is_ik and self.get_roted_fun:
            logger.info(f"I am ik and will try to get_roted {repr(self.my_files)}")
            if valid(self.imu_resampled):
                logger.info("imu is valid attempting rotation")
                self.imu_resampled = self.get_roted_fun(self.imu_resampled)
            if valid(self.mocap_resampled):
                logger.info("mocap is valid attempting rotation")
                self.mocap_resampled = self.get_roted_fun(self.mocap_resampled)
        else:
            logger.info(f"I am NOT ik and will NOT try to get_roted {repr(self.my_files)}")


        ### this is the time shifting, should be a function, but i am corrupting the mocap_resampled and the mask_mocap so we cant add another slider to change it the way it is. 

        # calculating the time_offset:
        time_offset = 0
        if not lag:
            total_xcorr = 0
            time_threshold = 0.1 # seconds
            for joint in self.common_joints:
                imu_signal = self.imu_resampled[joint]*self.scale_imu
                mocap_signal = self.mocap_resampled[joint]*self.scale_mocap

                imu_sliced = imu_signal.loc[(self.mask_mocap[0]-time_threshold):(self.mask_mocap[1]+time_threshold)]
                mocap_sliced = mocap_signal.loc[(self.mask_mocap[0]-time_threshold):(self.mask_mocap[1]+time_threshold)]

                if False: # to show the actual plots of the offset data
                    fig, axs = plt.subplots(1,2, figsize=(10,2.5))
                    axs[0].plot(imu_signal)
                    axs[0].plot(mocap_signal)
                    axs[0].set_title(f"resampled only {joint}")
                    
                    axs[1].plot(imu_sliced)
                    axs[1].plot(mocap_sliced)
                    axs[1].set_title(f"sliced {joint}")
                    plt.show()
                xcorr = signal.correlate(imu_sliced, mocap_sliced, mode='full')
                total_xcorr += xcorr

            
            lag_samples = np.argmax(total_xcorr) - len(mocap_sliced) + 1
            self.time_offset = lag_samples / fs #+ 2* mask_mocap[0]

            print(lag_samples)
        else:
            self.time_offset = lag

        if self.mask_mocap:
            # we have to update the mocap mask to include the delay
            self.mask_mocap = [self.mask_mocap[0]+self.time_offset, self.mask_mocap[1]+self.time_offset]
        
        if valid(self.mocap_resampled):
            # Apply the offset to one of them (let's shift mocap to match IMU timeline)
            self.mocap_resampled.index = self.mocap_resampled.index + self.time_offset

        self.all_imu_resampled = [None for i in range(len(imu_files))]
        self.all_mocap_resampled = [None for i in range(len(mocap_files))]
        
        for i, imu_datai in enumerate(imu_data):
            if valid(imu_datai):
                self.all_imu_resampled[i] = imu_datai.reindex(common_time, method='nearest').interpolate(method='linear')
        for i, mocap_datai in enumerate(mocap_data):
            if valid(mocap_datai):
                self.all_mocap_resampled[i] = mocap_datai.reindex(common_time, method='nearest').interpolate(method='linear')
                self.all_mocap_resampled[i].index += self.time_offset

    def mask_from(self,ik_strial):
        self.mask_mocap = ik_strial.mask_mocap
        self.min_size_ext = ik_strial.min_size_master


    def generate_sided_mask(self):
        #
        for side, (valid_steps_lr, step_segs_lr) in enumerate(zip([self.valid_steps_l, self.valid_steps_r], [self.step_seg_l_list, self.step_seg_r_list] )):
            ## we may not have a single valid step, in this case we want to set the whole mask to false, but we want the mask to exist, i guess
            side_string = "_r" if side else "_l"
            self.imu_block[f"mask{side_string}"] = False
            self.mocap_block[f"mask{side_string}"] = False
            for step, is_valid in zip(step_segs_lr,valid_steps_lr):
                if is_valid:
                    self.imu_block.loc[step[0]: step[1], f"mask{side_string}"] = True
                    self.mocap_block.loc[step[0]: step[1],f"mask{side_string}"] = True
                else:
                    with self.output:
                        logger.info(f"step {repr(step)} was marked as invalid")
        with self.output:
            print("generated sided mask")

    def create_controls(self):

        sliced_once = False

        # curtesy of chapppt
        # --- slider + textbox pair 1 ---
        self.s1 = FloatSlider(value=self.mask_mocap[0], min=self.t_start, max=self.t_end, step=0.01, description="Start")
        self.t1 = FloatText(value=self.s1.value)

        # --- slider + textbox pair 2 ---
        self.s2 = FloatSlider(value=self.mask_mocap[1], min=self.t_start, max=self.t_end, step=0.01, description="Stop")
        self.t2 = FloatText(value=self.s2.value)
        
        # --- sync logic ---
        def sync_s1(change):
            self.t1.value = change["new"]
            self.mask_mocap[0] = self.t1.value + self.time_offset

        def sync_t1(change):
            self.s1.value = change["new"]
            self.mask_mocap[0] = self.s1.value+ self.time_offset

        def sync_s2(change):
            self.t2.value = change["new"]
            self.mask_mocap[1] = self.t2.value+ self.time_offset

        def sync_t2(change):
            self.s2.value = change["new"]
            self.mask_mocap[1] = self.s2.value+ self.time_offset

        self.s1.observe(sync_s1, "value")
        self.t1.observe(sync_t1, "value")

        self.s2.observe(sync_s2, "value")
        self.t2.observe(sync_t2, "value")

        # --- UI setup ---
        self.replot_button = Button(description="Reploterino")
        self.replot_button.on_click(self.rebork)

        self.output = Output()

        self.create_plot()

        self.left_checkbox_container = widgets.HBox([])
        self.right_checkbox_container = widgets.HBox([])

        left_panel = widgets.VBox([
            widgets.Label("Left Steps:"),
            self.left_checkbox_container
        ])
        
        right_panel = widgets.VBox([
            widgets.Label("Right Steps:"),
            self.right_checkbox_container
        ])
        
        panels = widgets.HBox([left_panel, right_panel])

        self.ui = widgets.Accordion(children=[
        VBox([
            HBox([self.s1, self.t1]),
            HBox([self.s2, self.t2]),
            panels,
            self.replot_button,
            self.output
        ])])

        self.ui.set_title(0,f"imu:{repr(self.my_files[0])} mocap:{repr(self.my_files[1])}")

    def create_plot(self):
    
        self.fig,self.axs = plt.subplots(len(self.common_joints),1, figsize= (10,2.5*len(self.common_joints)), constrained_layout=True)
        #self.fig.tight_layout()
        self.axs.flatten()

    def update_checkboxes(self, side):
        """Rebuild the checkbox list when steps change"""
        if side == 'left':
            steps = self.valid_steps_l
            container = self.left_checkbox_container
        else:
            steps = self.valid_steps_r
            container = self.right_checkbox_container
        
        # Clear existing checkboxes
        container.children = []
        
        # Create new checkboxes
        checkboxes = []
        for i, enabled in enumerate(steps):
            cb = widgets.Checkbox(
                value=enabled,
                description=f"{i+1}",
                indent=False
            )
            # Connect to update function
            cb.observe(lambda change, idx=i, s=side: 
                      self.on_checkbox_change(change, idx, s), 
                      names='value')
            checkboxes.append(cb)
        
        # Update container
        container.children = checkboxes
    
    def on_checkbox_change(self, change, idx, side):
        """Update the step list when checkbox changes"""
        if side == 'left':
            self.valid_steps_l[idx] = change['new']
        else:
            self.valid_steps_r[idx] = change['new']

        ##gotta update the mask after disabling the dude.
        self.generate_sided_mask()

    def rebork(self,*args):
        #plt.plot(total_xcorr) ## not sure how to interpret this anyways,,, it start with one trial with just one sample in common i think, like full whole length of time of one trial offset
        #plt.show()
        with self.output:
            self.output.clear_output()
        ## this shows the time correction, should be good.
        for joint, ax in zip( self.common_joints, self.axs):
            ax.clear()
            #logger.warning("what should i plot here, idk...")
            if valid(self.imu_resampled):
                imu_signal = self.imu_resampled[joint]*self.scale_imu
                ax.plot(self.imu_resampled.index, imu_signal, label="imu")
            if valid(self.mocap_resampled):
                mocap_signal = self.mocap_resampled[joint]*self.scale_mocap
                ax.plot(self.mocap_resampled.index, mocap_signal, label="mocap")
            ax.legend()
            ax.axvline(self.mask_mocap[0], color="g")
            ax.axvline(self.mask_mocap[1], color="g")

            ax.set_title(joint)
        valid_l = []
        valid_r = []
        suffix_length = len("_l"+self.curve_suffix )
        for lefties in self.step_seg_l_list[:-1]:
            style = ":" if lefties[0] < self.mask_mocap[0] or lefties[1] > self.mask_mocap[1] else "-"
            for joint, ax in zip( self.common_joints, self.axs):
                if "_l"+self.curve_suffix == joint[-suffix_length:]: ## i should look only at the end, if it breaks, you know why
                    ax.axvline(lefties[0],color="r", ls=style)
                    ax.axvline(lefties[1],color="r", ls=style)
            if style == "-":
                ## then we add this one
                valid_l.append(lefties)
        for righties in  self.step_seg_r_list[:-1]:
            style = ":" if righties[0] < self.mask_mocap[0] or righties[1] > self.mask_mocap[1] else "-"
            for joint, ax in zip( self.common_joints, self.axs):
                if "_r"+self.curve_suffix == joint[-suffix_length:]:
                    ax.axvline(righties[0],color="b", ls=style)
                    ax.axvline(righties[1],color="b", ls=style)
            if style == "-":
                ## then we add this one
                valid_r.append(righties)
        valid_l.append(self.step_seg_l_list[-1])
        valid_r.append(self.step_seg_r_list[-1])
        
        if not self.valid_steps_created: ## then i can create, otherwise i would be overwriting changes!
            for a_step_l in valid_l: 
                self.valid_steps_l.append(True)
            for a_step_r in valid_r: 
                self.valid_steps_r.append(True)
            self.valid_steps_l[-1] = False ## last step is not used and now i dont remember why, monkeys banana stepladder
            self.valid_steps_r[-1] = False
            self.valid_steps_created = True
            ## when and if you want to add more adls to each side then this will get tricky, but now it is easy
            self.update_checkboxes("left")
            self.update_checkboxes("right")

        if True:
            self.step_seg_l_list = valid_l
            self.step_seg_r_list = valid_r

        with self.output:
            print(valid_l)
            print(valid_r)
            interactive_display(self.fig)
            if self.save_fig_dir == "./":
                logging.error(self.save_fig_dir)
                err = traceback.format_stack()
                logging.error(f" this directory needs to be set!\n{"".join(err)}")
                logger.warning("saving sync figures in current directory")
            self.fig.savefig(f"{self.save_fig_dir}/sync{self.mode}{self.index}.png")
            if not interactive:
                plt.close(self.fig)


        # NOW trim to overlapping region
 
        if self.master:
            self.t_start = max(self.imu_resampled.index[0], self.mocap_resampled.index[0])
            self.t_end = min(self.imu_resampled.index[-1], self.mocap_resampled.index[-1])

        imu_synced = self.imu_resampled.loc[self.t_start:self.t_end]
        # now we mask to the times where mocap is available
        imu_synced = imu_synced.loc[self.mask_mocap[0]:self.mask_mocap[1]]
        
        mocap_synced = []
        if valid(self.mocap_resampled):
            mocap_synced = self.mocap_resampled.loc[self.t_start:self.t_end]
            mocap_synced = mocap_synced.loc[self.mask_mocap[0]:self.mask_mocap[1]]
        
        if self.master:
            # we then slice it to make sure they are the same length
            min_size = min(len(imu_synced),len(mocap_synced))
            self.min_size_master = min_size
        else:
            min_size = min(len(imu_synced),len(mocap_synced), self.min_size_ext)

        imu_synced = imu_synced.iloc[:min_size]
        
        self.imu_block = imu_synced
        if valid(mocap_synced):
            mocap_synced = mocap_synced.iloc[:min_size]
            self.mocap_block = mocap_synced
            # Sanity check
            with self.output:
                


                print(f"Synced length: {len(imu_synced)} == {len(mocap_synced)}")
                assert(len(imu_synced) == len(mocap_synced))
                print(f"Time range: {imu_synced.index[0]:.3f} to {imu_synced.index[-1]:.3f}")
        else:
            self.mocap_block = None
    
        with self.output:
            print(f"offset: {self.time_offset}")

        self.generate_sided_mask()

    def complicated_get_mask_side(self, joint, imu_or_mocap_as_string):
        joint = joint[:-len(self.curve_suffix)]


        imu_mask = None
        mocap_mask = None

        imu_mask_l = self.imu_block["mask_l"]    
        imu_mask_r = self.imu_block["mask_r"]    
        mocap_mask_l = self.mocap_block["mask_l"]    
        mocap_mask_r = self.mocap_block["mask_r"]    
        if   joint[-2:] == "_l":
            imu_mask = imu_mask_l
            mocap_mask = mocap_mask_l
        elif joint[-2:] == "_r":
            imu_mask = imu_mask_r
            mocap_mask = mocap_mask_r
        else:
            imu_mask = imu_mask_l & imu_mask_r ## this should be a logic and, as it will only be valid when both are valid at the same time
            mocap_mask = mocap_mask_l & mocap_mask_r ## this should be a logic and, as it will only be valid when both are valid at the same time
        
        if imu_or_mocap_as_string == "imu":
            return imu_mask
        elif imu_or_mocap_as_string == "mocap":
            return mocap_mask

        #this_imu_block  = self.imu_block.reset_index(drop=True)
    def get_imu_block(self,joint):
        imu_mask = self. complicated_get_mask_side(joint, "imu")

        if self.is_ik:
            return self.imu_block[joint]
        else:
            return self.imu_block.loc[imu_mask, joint]
    
    def get_mocap_block(self,joint):
        mocap_mask = self. complicated_get_mask_side(joint, "mocap")

        if self.is_ik:
            return self.mocap_block[joint]
        else:
            return self.mocap_block.loc[mocap_mask, joint]

    def __del__(self):
        print("why are you deleting me?")
        print(self.my_files)
        if self.fig:

            plt.close(self.fig)

## this is for this subject and this action everything, right?

from .refdata import generate_action_plots_meat

class Dismissed():
    """
        Container for a list of SyncedLumps

            we need this because setting up the plots without it would be sorta confsuing as hell

    """

    def __init__(self, slumpList=[], weight=None, save_fig_dir="./", action="unknown", get_roted_fun=None):
        self.slumpList = slumpList
        self.weight = weight
        self.save_fig_dir = save_fig_dir
        self.action = action
        self.get_roted_fun = get_roted_fun

    def set_by_two_lists_of_lumps(self, imuLs, mocapLs, extSyncLs):
        for i, (a, b, sync_Li) in enumerate(zip(imuLs, mocapLs, extSyncLs)):
            this_SL = SyncedLump(a,b,self.weight, save_fig_dir = self.save_fig_dir, index=i, action= self.action, get_roted_fun= self.get_roted_fun)
            if sync_Li[0] or sync_Li[1]:
                logger.warning("Using external segmentation for actions!!!")
                #logging.error(this_SL.save_fig_dir)
                this_SL.manual_split(sync_Li[0], sync_Li[1])
            self.slumpList.append(this_SL)

    ## I think i did the same thing twice
    #def manual_segmentation(self, list_of_things):
    #    for iSL, (ls, rs) in zip(self.slumpList, list_of_things):
    #        if not iSL.segmented:
    #            logger.warning("applying manual segmentation")
    #            iSL.manual_split(ls, rs)
    
    def which_steps_do_i_plot(self, list_of_things):
        for iSL, (ls, rs) in zip(self.slumpList, list_of_things):
            if not iSL.autovalid:
                logger.warning(f"setting which steps do I plot for all the trials of this action {self.action}")
                iSL.manual_set_valid_id_so(ls, rs)
    
    def gen_action_plots(self, gtype, iomtype, conv_names= None, ref=None):
        
        stll = None
        stlr = None
        curve_suffix = ""
        if gtype == "grf":
            stll = self.get_strials("grfl")
            stlr = self.get_strials("grfr")
            if not type(conv_names) == type([]) or not len(conv_names) == 2:
                logger.error("grf plotting requires different convnames for each side and you make them into a list [left, right]. that is because grf is based on the file definitions and the file definitions are weird and inconsistent, so doing this requires some flexibility here. ")
        else:
            stll = self.get_strials(gtype)
            stlr = stll
            if not type(conv_names) == type([]) or not len(conv_names) == 2:
                conv_names = [conv_names, conv_names]


        if gtype == "id":
            curve_suffix = "_moment"
       
        all_curves_for_this_person = {}


        for stli, stri in zip(stll, stlr):
            #logger.info(stli.my_files)
            #logger.info(stri.my_files)
            this_file_name= ["",""]
            if iomtype == "imu":
                stlis = stli.imu_resampled
                stris = stri.imu_resampled
                this_file_name = [stli.my_files[0],stri.my_files[0]]

            elif iomtype == "mocap":
                stlis = stli.mocap_resampled
                stris = stri.mocap_resampled
                this_file_name = [stli.my_files[1],stri.my_files[1]]

            for l_r, (data_i, which_clippings) in enumerate(zip([stlis, stris],(stli.step_seg_l_list, stri.step_seg_r_list))):
                all_curves_for_this_person.update(generate_action_plots_meat(l_r,this_file_name[l_r], data_i, data_i.index,which_clippings, all_curves_for_this_person, ref=ref, conv_names=conv_names[l_r], curve_suffix=curve_suffix, pelvis_plot_only_right_side=True, combine_sides=False))
        return all_curves_for_this_person

    def get_strials(self, gtype):
        sTrialsList = []
        if gtype== "ik":
            for sLumpi in self.slumpList:
                sTrialsList.append(sLumpi.ik)
        elif gtype== "id":
            for sLumpi in self.slumpList:
                sTrialsList.append(sLumpi.id)
        elif gtype== "so":
            for sLumpi in self.slumpList:
                sTrialsList.append(sLumpi.so)
        elif gtype== "grfl": ## this is super bad
            for sLumpi in self.slumpList:
                sTrialsList.append(sLumpi.grfl)
        elif gtype== "grfr": ## this is super bad too, like,, we need to figure this out.
            for sLumpi in self.slumpList:
                sTrialsList.append(sLumpi.grfr)
        else:
            logger.error("Unknown graph type!")

        return sTrialsList

    def run_analysis(self, gtype, lag=None, auto_compute_metrics = False):

        time_offsets = []
        sTrials = self.get_strials(gtype)
        if lag:
            time_offsets = lag 
        
        ui_list = []
        common_joints = []

        if len(sTrials) == 0:
            logger.fatal("You have no Trials to run_analysis on!!!!!!")
            return
        for sTiii in sTrials:

            if not common_joints:
                common_joints = sTiii.common_joints
            if not lag:
                time_offsets.append(sTiii.time_offset)
            else:
                print("using lag estimated from ik")
                time_offset = lag[iii]
            
            sTiii.create_controls()
            ui_list.append(sTiii.ui)
            sTiii.rebork()
            interactive_display(sTiii.ui)

        metrics_output = Output()
        skip_joints = ["lumbar", "subtalar", "mtp"]

        ## ffs
        included_joints = []
        for jjjjj, joint in enumerate(common_joints):
            is_skip = False
            for sk in skip_joints:
                if sk in joint:
                    is_skip = True
                    break
            if is_skip:
                continue
            included_joints.append(joint)
        cols = 2
        rows = int(np.ceil(len(included_joints)/cols)) 
        print("o.O"*100)
        if len(common_joints) == 0:
            logger.error("No common joints????")
        if len(included_joints) == 0:
            logger.error("No included joints????")
        logger.debug(rows)
        with metrics_output:
            metrics_output.clear_output()
            fig, ax = plt.subplots(rows,cols, figsize= (10,2.5*rows), constrained_layout= True)
            ax = ax.flatten()
            interactive_display(fig)
        def compute_metrics(*args):
            #imu_all = pd.DataFrame()
            imu_all = {}
            #mocap_all = pd.DataFrame()
            mocap_all = {}
            scale_imu=1
            scale_mocap=1
            for sTiii in sTrials:
                ##this is bad, but if i am mixing scales it is also bad
                scale_imu = sTiii.scale_imu
                scale_mocap = sTiii.scale_mocap
                for joint in included_joints:
                    if not joint in imu_all:
                        imu_all[joint] = []
                    if not joint in mocap_all:
                        mocap_all[joint] = []

                    bi = list(sTiii.get_imu_block(joint))
                    bm = list(sTiii.get_mocap_block(joint))
                    min_of_them = min([len(bi),len(bm)])
                    #print([len(bi),len(bm)])
                    bi = bi[:min_of_them]
                    bm = bm[:min_of_them]
                    imu_all[joint].extend(bi) 
                    mocap_all[joint].extend(bm) 
                #imu_all = pd.concat([imu_all, sTiii.imu_block()], ignore_index=True)
                #mocap_all = pd.concat([mocap_all, sTiii.mocap_block()], ignore_index=True)
            ##sanity check
            for joint in included_joints:
                assert(len(imu_all[joint])==len(mocap_all[joint]))

            # we plot the synced values (sanity check)
            # and compute the metrics
            with metrics_output:
                metrics_output.clear_output()
                fig, ax = plt.subplots(rows,cols, figsize= (10,2.5*rows), constrained_layout= True)
                ax = ax.flatten()
            results = {}
            for jjjjj, joint in enumerate(included_joints):
                is_skip = False
                for sk in skip_joints:
                    if sk in joint:
                        is_skip = True
                        break
                if is_skip:
                    continue
                imu_signal = np.array(imu_all[joint]) * scale_imu  # to degrees if needed
                mocap_signal = np.array(mocap_all[joint]) * scale_mocap  # to degrees if needed
                with metrics_output:
                    ax[jjjjj].clear()
                    ax[jjjjj].plot(imu_signal,label="imu"+joint)
                    ax[jjjjj].plot(mocap_signal,label="mocap"+joint)
                    #plt.legend()
                    #plt.title(joint)

                    ax[jjjjj].set_title(joint)
                    #plt.show()
                rmse = np.sqrt(np.mean((imu_signal - mocap_signal)**2))
                pearson_r, p_value = stats.pearsonr(imu_signal, mocap_signal)

                results[joint] = {'RMSE': rmse, 'Pearson_r': pearson_r}
            # Make it a nice dataframe
            results_df = pd.DataFrame(results).T
            results_df.to_csv(f"{self.save_fig_dir}/rmse_pearson.csv")
            #logging.info("d"*40)
            #print(results_df)
            #logging.info("d"*40)
            #logging.info("d"*40)
            with metrics_output:
                #logging.info("null_context_executes_fine"*40)
                interactive_display(fig)
                print(results_df)
                fig.savefig(f"{self.save_fig_dir}/allsync{gtype}.png")
                if not interactive:
                    plt.close(fig)

        comp_button = Button(description="Compute Metrics")
        comp_button.on_click(compute_metrics)
        ooo = VBox([comp_button, metrics_output])
        interactive_display(ooo)
        if auto_compute_metrics:
            compute_metrics()

        return time_offsets

def header(sub):
    sub = repr(sub)
    n = 81
    if (n-len(sub))%2 == 1:
        sub+="="
    a = (n - len(sub))//2 
    print("="*n)
    print("="*a + sub +"="*a)
    print("="*n)


class Lump():

    def __init__(self, head, grfl, grfr, id_, so ):
        self.ik_head = head ### this is the file that will be used to sync everythign else
        self.grfl = grfl
        self.grfr = grfr
        self.id = id_
        self.so = so
        #def set_clippings(self,clipps):
    #    self.clippings = clipps
    def __repr__(self):
        return f"I am a lump!\n{self.ik_head}\n{self.grfl}\n{self.grfr}\n{self.id}\n{self.so}\n"
class IMULump(Lump):
    def __init__(self, *args):
        super().__init__(*args)
    def __repr__(self):
        return "IMU LUMP"+super().__repr__()


class MocapLump(Lump):
    def __init__(self, *args):
        super().__init__(*args)
    def __repr__(self):
        return "MOCAP LUMP"+super().__repr__()

from .refdata import each_side_plot_meat

class SyncedLump(): ## dont get distracted. a lump is a trial 
    #with all the data from all the sources okay
    def __init__(self, imuLump, mocapLump, weight, save_fig_dir="./", index=-1, action="unknown", get_roted_fun= None):
        self.get_roted_fun = get_roted_fun
        self.segmented = False
        self.autovalid = True
        self.weight = weight
        self.index = index
        self.save_fig_dir=save_fig_dir
        #logging.error(self.save_fig_dir)
        self.ik = SyncedTrials(imuLump.ik_head, mocapLump.ik_head, is_ik=True, save_fig_dir=self.save_fig_dir, mode="ik", index=index, get_roted_fun=self.get_roted_fun) ## this will be automatically synced
        self.ik.master = True
        self.action = action
        self.lag = self.ik.time_offset
        self.grfl = SyncedTrials(imuLump.grfl, mocapLump.grfl, lag = self.lag, save_fig_dir=self.save_fig_dir, mode="grfl", index=index, get_roted_fun=self.get_roted_fun)
        self.grfr = SyncedTrials(imuLump.grfr, mocapLump.grfr, lag = self.lag, save_fig_dir=self.save_fig_dir, mode="grfr", index=index, get_roted_fun=self.get_roted_fun)
        self.id   = SyncedTrials(imuLump.id  , mocapLump.id  , lag = self.lag, save_fig_dir=self.save_fig_dir, mode="id"  , index=index, get_roted_fun=self.get_roted_fun)
        self.so   = SyncedTrials(imuLump.so  , mocapLump.so  , lag = self.lag, save_fig_dir=self.save_fig_dir, mode="so"  , index=index, get_roted_fun=self.get_roted_fun)
        if self.action in ["walking", "gait", "running"]:
            
            self.grf_split_me()
            self.update_from_splits()
            self.autovalid = False

    def manual_split(self, l_segs, r_segs):
        #logging.error(self.save_fig_dir)

        self.step_seg_l_list = l_segs
        self.step_seg_r_list = r_segs
        self.update_from_splits()
        
    def manual_set_valid_id_so(self, lvalid, rvalid):
        self.id.valid_steps_l = lvalid
        self.id.valid_steps_r = rvalid
        self.id.generate_sided_mask()
    
        self.so.valid_steps_l = lvalid
        self.so.valid_steps_r = rvalid
        self.so.generate_sided_mask()
    
    def update_from_splits(self):

        for sti  in [self.ik, self.grfl, self.grfr, self.id, self.so]:
            sti.step_seg_l_list = self.step_seg_l_list
            sti.step_seg_r_list = self.step_seg_r_list

        self.ik.create_controls() # the plot is inside a control now, so we need this.
        #self.ik.create_plot()
        self.ik.rebork()
        for sti  in [self.grfl, self.grfr, self.id, self.so]:
            sti.mask_from(self.ik)
        self.segmented = True
    def grf_split_me(self):
        zero_time = 0
        self.step_seg_l_list = each_side_plot_meat(self.grfl.imu_resampled, self.grfl.imu_resampled.index,zero_time,grf_name_prefix = "1_ground_", side="Left", weight=self.weight, do_plot=False)
        self.step_seg_r_list = each_side_plot_meat(self.grfr.imu_resampled, self.grfr.imu_resampled.index,zero_time,grf_name_prefix = "ground_", side="Right", weight=self.weight, do_plot=False)

    def rebork_all(self):
        for sti  in [self.grfl, self.grfr, self.id, self.so]:
            sti.create_controls() # the plot is inside a control now, so we need this.
            #sti.create_plot()
            sti.rebork()


