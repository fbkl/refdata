import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import signal, stats
from scipy.spatial.transform import Rotation as R
from . import my_log

logger = my_log.logger

logger.info("Loading metrics")

from ipywidgets import FloatSlider, FloatText, Button, HBox, VBox, Output, Layout

def get_roted(this_df,in_degrees=True):
    initial_rotation = this_df['pelvis_rotation'].iloc[0]

    R_correction = R.from_euler('z', initial_rotation, degrees=in_degrees).inv()

    angles = []
    for i in range(len(this_df)):
        tilt = this_df['pelvis_tilt_x'].iloc[i]
        obl = this_df['pelvis_obliquity'].iloc[i]
        rot = this_df['pelvis_rotation'].iloc[i]

        R_current = R.from_euler('zyx', [rot, obl, tilt], degrees=in_degrees)
        R_correct = R_correction * R_current
        
        corrected = R_correct.as_euler('zyx', degrees=in_degrees)
        angles.append(corrected)
    angles = np.array(angles)
    
    ## we invert pelvis_tilt manually i am doing something wrong here
    if False and angles[0,2] < 0:
        
        this_df['pelvis_tilt_x'] = -angles[:,2]
    else:
        this_df['pelvis_tilt_x'] = angles[:,2]
    
    if False and angles[0,1] < 0:
        
        this_df['pelvis_obliquity'] = -angles[:,1]
    else:
        this_df['pelvis_obliquity'] = angles[:,1] 
        
    this_df['pelvis_rotation'] = angles[:,0] 
    
    
    
    return this_df

class SyncedTrial:
    def __init__(self, this_imu_file, this_mocap_file, lag = [] ):
        self.scale_mocap = 180/np.pi

        self.scale_imu = 180/np.pi
        is_id = False
        # Inspect the files themselves
        print(this_imu_file)
        print(this_mocap_file)
        if True:
            #print("=== IMU .STO FILE ===")
            imu_skip_rows = 0
            with open(this_imu_file, 'r') as f:
                for i in range(20):  # First 20 lines
                    this_line = f.readline().rstrip()
                    #print(f"{i}: {this_line}")
                    if "endheader" in this_line:
                        imu_skip_rows = i+1
                    if "inDegrees=yes" in this_line:
                        self.scale_imu = 1
            #print("\n=== MOCAP .MOT FILE ===")
            mocap_skip_rows = 0
            with open(this_mocap_file, 'r') as f:
                for i in range(20):
                    this_line = f.readline().rstrip()
                    #print(f"{i}: {this_line}")
                    if "endheader" in this_line:
                        mocap_skip_rows = i+1
                    if "inDegrees=yes" in this_line:
                        self.scale_mocap = 1
        if "tau" in this_imu_file:
            self.scale_mocap = 1
            self.scale_imu = 1
            is_id = True
        
        # Load IMU .sto files (OpenSim format)
        imu_data = pd.read_csv(this_imu_file, delimiter='\t', skiprows=imu_skip_rows)  
        # Load Vicon .mot files
        mocap_data = pd.read_csv(this_mocap_file, delimiter='\t', skiprows=mocap_skip_rows)

        # plot them raw
        if False: # this has time as a column, so it will show epoch times as something to 10⁹... not great
            imu_data.plot()
            mocap_data.plot()
            plt.show()

        # the mocap pelvis has a different frame, we need to rename them :

        rename_map_i = {
            "pelvis_tilt": "pelvis_tilt_x",
            "pelvis_list": "pelvis_obliquity",
            "pelvis_rotation": "pelvis_rotation"
        }

        if is_id:
            for col in imu_data.columns:
                if col == "time":
                    continue
                imu_data = imu_data.rename(columns={col:col+"_moment"})
        imu_data = imu_data.rename(columns=rename_map_i)
        #imu_data = get_roted(imu_data)

        rename_map_m = {
            "pelvis_tilt": "pelvis_tilt_x",
            "pelvis_list": "pelvis_obliquity",
            "pelvis_rotation": "pelvis_rotation"
        }

        mocap_data = mocap_data.rename(columns=rename_map_m)
        #mocap_data = get_roted(mocap_data)


        # Get the first timestamp
        t0 = imu_data["time"].iloc[0]  # .iloc[0] not .index[0]

        # Subtract offset
        imu_data["time"] = imu_data["time"] - t0

        # NOW set it as index
        imu_data = imu_data.set_index("time")

        
        # i want to save the mocap data begining and end. when i dont have mocap, i dont have a reference. 
        # if i compare to padded values im messing things up
        # so after everything is done I will use this to slice the output

        self.mask_mocap = [mocap_data["time"].iloc[0], mocap_data["time"].iloc[-1]]
        print(f"mocap time mask (only beginning and end, if there are also nans in the middle this will fail)  {self.mask_mocap}")

        # mocap is already at wall time
        mocap_data = mocap_data.set_index('time')
        
        # plot them as wall timed
        if False: 
            imu_data.plot()
            mocap_data.plot()
            plt.show()


        # Create a common time base - use the overlapping period
        # Say 100 Hz exactly
        fs = 100  # Hz
        self.t_start = min(imu_data.index[0], mocap_data.index[0])
        self.t_end = max(imu_data.index[-1], mocap_data.index[-1])

        print(self.t_start, self.t_end)
        common_time = np.arange(self.t_start, self.t_end, 1/fs)
        self.imu_resampled = imu_data.reindex(common_time, method='nearest').interpolate(method='linear')
        self.mocap_resampled = mocap_data.reindex(common_time, method='nearest').interpolate(method='linear')

        all_common_joints = [col for col in self.imu_resampled.columns if col in self.mocap_resampled.columns]
        # but we exclude the translations
        self.common_joints = []
        for joint in all_common_joints:
            if "_tx" == joint[-3:] or "_ty" == joint[-3:] or "_tz" == joint[-3:]:
                pass
            else:
                self.common_joints.append(joint)
        #common_joints

        if not is_id:
            self.imu_resampled = get_roted(self.imu_resampled, in_degrees=False)
            self.mocap_resampled = get_roted(self.mocap_resampled)


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
        
        # we have to update the mocap mask to include the delay
        self.mask_mocap = [self.mask_mocap[0]+self.time_offset, self.mask_mocap[1]+self.time_offset]
        
        # Apply the offset to one of them (let's shift mocap to match IMU timeline)
        self.mocap_resampled.index = self.mocap_resampled.index + self.time_offset

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

        
        self.create_plot()

        self.ui = VBox([
            HBox([self.s1, self.t1]),
            HBox([self.s2, self.t2]),
            self.replot_button,
        ])


    def create_plot(self):
    
        self.fig,self.axs = plt.subplots(len(self.common_joints),1, figsize= (10,2.5*len(self.common_joints)), constrained_layout=True)
        #self.fig.tight_layout()
        self.axs.flatten()

    def rebork(self,*args):
        #plt.plot(total_xcorr) ## not sure how to interpret this anyways,,, it start with one trial with just one sample in common i think, like full whole length of time of one trial offset
        #plt.show()
        #with self.out:
        #    self.out.clear_output()
        ## this shows the time correction, should be good.
        for joint, ax in zip( self.common_joints, self.axs):
            ax.clear()
            imu_signal = self.imu_resampled[joint]*self.scale_imu
            mocap_signal = self.mocap_resampled[joint]*self.scale_mocap
            ax.plot(self.imu_resampled.index, imu_signal, label="imu")
            ax.plot(self.mocap_resampled.index, mocap_signal, label="mocap")
            ax.legend()
            ax.axvline(self.mask_mocap[0], color="r")
            ax.axvline(self.mask_mocap[1], color="r")
            ax.set_title(joint)
        plt.show()


        # NOW trim to overlapping region
        self.t_start = max(self.imu_resampled.index[0], self.mocap_resampled.index[0])
        self.t_end = min(self.imu_resampled.index[-1], self.mocap_resampled.index[-1])

        imu_synced = self.imu_resampled.loc[self.t_start:self.t_end]
        mocap_synced = self.mocap_resampled.loc[self.t_start:self.t_end]

        # now we mask to the times where mocap is available
        imu_synced = imu_synced.loc[self.mask_mocap[0]:self.mask_mocap[1]]
        mocap_synced = mocap_synced.loc[self.mask_mocap[0]:self.mask_mocap[1]]
        
        # we then slice it to make sure they are the same length
        min_size = min(len(imu_synced),len(mocap_synced))

        imu_synced = imu_synced.iloc[:min_size]
        mocap_synced = mocap_synced.iloc[:min_size]
    
        print(f"offset: {self.time_offset}")
        # Sanity check
        print(f"Synced length: {len(imu_synced)} == {len(mocap_synced)}")
        assert(len(imu_synced) == len(mocap_synced))
        print(f"Time range: {imu_synced.index[0]:.3f} to {imu_synced.index[-1]:.3f}")

        self.imu_block  = imu_synced.reset_index(drop=True)
        self.mocap_block = mocap_synced.reset_index(drop=True)
    def __del__(self):
        plt.close(self.fig)

def run_analysis(imu_ik_trials, vicon_ik_trials, lag=None):

    time_offsets = []
    sTrials = []
    if lag:
        time_offsets = lag 
    
    ui_list = []
    common_joints = []

    for this_imu_file, this_mocap_file in zip(imu_ik_trials,vicon_ik_trials):

        sTiii = SyncedTrial(this_imu_file, this_mocap_file)

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
        display(sTiii.ui)
        sTrials.append(sTiii)
        break

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
    with metrics_output:
        fig, ax = plt.subplots(rows,cols, figsize= (10,2.5*rows), constrained_layout= True)
        ax = ax.flatten()
    def compute_metrics(*args):
        with metrics_output:
            metrics_output.clear_output()
        imu_all = pd.DataFrame()
        mocap_all = pd.DataFrame()
        scale_imu=1
        scale_mocap=1
        for sTiii in sTrials:

            ##this is bad, but if i am mixing scales it is also bad
            scale_imu = sTiii.scale_imu
            scale_mocap = sTiii.scale_mocap
            imu_all = pd.concat([imu_all, sTiii.imu_block], ignore_index=True)
            mocap_all = pd.concat([mocap_all, sTiii.mocap_block], ignore_index=True)


        # we plot the synced values (sanity check)
        # and compute the metrics
        results = {}
        for jjjjj, joint in enumerate(included_joints):
            is_skip = False
            for sk in skip_joints:
                if sk in joint:
                    is_skip = True
                    break
            if is_skip:
                continue
            imu_signal = imu_all[joint].values * scale_imu  # to degrees if needed
            mocap_signal = mocap_all[joint].values * scale_mocap  # to degrees if needed
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
        print(results_df)

    comp_button = Button(description="Compute Metrics")
    comp_button.on_click(compute_metrics)
    ooo = VBox([comp_button, metrics_output])
    display(ooo)
    return time_offsets

def header(sub):
    n = 81
    if (n-len(sub))%2 == 1:
        sub+="="
    a = (n - len(sub))//2 
    print("="*n)
    print("="*a + sub +"="*a)
    print("="*n)
