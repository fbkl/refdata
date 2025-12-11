import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import signal, stats
from scipy.spatial.transform import Rotation as R


def get_roted(this_df):
    initial_rotation = this_df['pelvis_rotation'].iloc[0]

    R_correction = R.from_euler('z', initial_rotation, degrees=True).inv()

    angles = []
    for i in range(len(this_df)):
        tilt = this_df['pelvis_tilt'].iloc[i]
        obl = this_df['pelvis_list'].iloc[i]
        rot = this_df['pelvis_rotation'].iloc[i]

        R_current = R.from_euler('zyx', [rot, obl, tilt], degrees=True)
        R_correct = R_correction * R_current
        
        corrected = R_correct.as_euler('zyx', degrees=True)
        angles.append(corrected)
    angles = np.array(angles)
    
    ## we invert pelvis_tilt manually i am doing something wrong here
    if angles[0,2] < 0:
        
        this_df['pelvis_tilt'] = -angles[:,2]
    else:
        this_df['pelvis_tilt'] = angles[:,2]
    
    if angles[0,1] < 0:
        
        this_df['pelvis_list'] = -angles[:,1]
    else:
        this_df['pelvis_list'] = angles[:,1] 
        
    this_df['pelvis_rotation'] = angles[:,0]
    
    
    
    return this_df

def run_analysis(imu_ik_trials, vicon_ik_trials, lag=None):


    imu_all = pd.DataFrame()
    mocap_all = pd.DataFrame()
    time_offsets = []
    if lag:
        time_offsets = lag 
    
    for iii, (this_imu_file, this_mocap_file) in enumerate(zip(imu_ik_trials,vicon_ik_trials)):
        scale_mocap = 180/np.pi

        scale_imu = 180/np.pi
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
                        scale_imu = 1
            #print("\n=== MOCAP .MOT FILE ===")
            mocap_skip_rows = 0
            with open(this_mocap_file, 'r') as f:
                for i in range(20):
                    this_line = f.readline().rstrip()
                    #print(f"{i}: {this_line}")
                    if "endheader" in this_line:
                        mocap_skip_rows = i+1
                    if "inDegrees=yes" in this_line:
                        scale_mocap = 1
        if "tau" in this_imu_file:
            scale_mocap = 1
            scale_imu = 1
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
            "pelvis_rotation": "pelvis_rot"
        }

        if is_id:
            for col in imu_data.columns:
                if col == "time":
                    continue
                imu_data = imu_data.rename(columns={col:col+"_moment"})
        #imu_data = imu_data.rename(columns=rename_map_i)
        #imu_data = get_roted(imu_data)

        rename_map_m = {
            "pelvis_tilt": "pelvis_obliquity",
            "pelvis_list": "pelvis_tilt_x",
            "pelvis_rotation": "pelvis_rot"
        }

        #mocap_data = mocap_data.rename(columns=rename_map_m)
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

        mask_mocap = [mocap_data["time"].iloc[0], mocap_data["time"].iloc[-1]]
        print(f"mocap time mask (only beginning and end, if there are also nans in the middle this will fail)  {mask_mocap}")

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
        t_start = min(imu_data.index[0], mocap_data.index[0])
        t_end = max(imu_data.index[-1], mocap_data.index[-1])

        print(t_start, t_end)
        common_time = np.arange(t_start, t_end, 1/fs)
        imu_resampled = imu_data.reindex(common_time, method='nearest').interpolate(method='linear')
        mocap_resampled = mocap_data.reindex(common_time, method='nearest').interpolate(method='linear')

        all_common_joints = [col for col in imu_resampled.columns if col in mocap_resampled.columns]
        # but we exclude the translations
        common_joints = []
        for joint in all_common_joints:
            if "_tx" == joint[-3:] or "_ty" == joint[-3:] or "_tz" == joint[-3:]:
                pass
            else:
                common_joints.append(joint)
        #common_joints

        if not is_id:
            imu_resampled = get_roted(imu_resampled)
            mocap_resampled = get_roted(mocap_resampled)

        # calculating the time_offset:
        time_offset = 0
        if not lag:
            total_xcorr = 0
            time_threshold = 0.1 # seconds
            for joint in common_joints:
                imu_signal = imu_resampled[joint]*scale_imu
                mocap_signal = mocap_resampled[joint]*scale_mocap

                imu_sliced = imu_signal.loc[(mask_mocap[0]-time_threshold):(mask_mocap[1]+time_threshold)]
                mocap_sliced = mocap_signal.loc[(mask_mocap[0]-time_threshold):(mask_mocap[1]+time_threshold)]

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
            time_offset = lag_samples / fs #+ 2* mask_mocap[0]

            print(lag_samples)
            print(time_offset)
            time_offsets.append(time_offset)
        else:
            print("using lag estimated from ik")
            time_offset = lag[iii]
        
        # we have to update the mocap mask to include the delay
        mask_mocap = [mask_mocap[0]+time_offset, mask_mocap[1]+time_offset]

        if True:
            #plt.plot(total_xcorr) ## not sure how to interpret this anyways,,, it start with one trial with just one sample in common i think, like full whole length of time of one trial offset
            #plt.show()
            ## this shows the time correction, should be good.
            for joint in common_joints:
                imu_signal = imu_resampled[joint]*scale_imu
                mocap_signal = mocap_resampled[joint]*scale_mocap
                fig,ax = plt.subplots(1,1, figsize= (10,2.5))
                ax.plot(imu_resampled.index, imu_signal)
                ax.plot(mocap_resampled.index+time_offset, mocap_signal)
                ax.set_title(joint)
                plt.show()

        # Apply the offset to one of them (let's shift mocap to match IMU timeline)
        mocap_resampled.index = mocap_resampled.index + time_offset

        # NOW trim to overlapping region
        t_start = max(imu_resampled.index[0], mocap_resampled.index[0])
        t_end = min(imu_resampled.index[-1], mocap_resampled.index[-1])

        imu_synced = imu_resampled.loc[t_start:t_end]
        mocap_synced = mocap_resampled.loc[t_start:t_end]

        # now we mask to the times where mocap is available
        imu_synced = imu_synced.loc[mask_mocap[0]:mask_mocap[1]]
        mocap_synced = mocap_synced.loc[mask_mocap[0]:mask_mocap[1]]
        
        # we then slice it to make sure they are the same length
        min_size = min(len(imu_synced),len(mocap_synced))

        imu_synced = imu_synced.iloc[:min_size]
        mocap_synced = mocap_synced.iloc[:min_size]
        


        #if not is_id:
        #    imu_synced = get_roted(imu_synced)
        #    mocap_synced = get_roted(mocap_synced)

        # Sanity check

        print(f"Synced length: {len(imu_synced)} == {len(mocap_synced)}")
        assert(len(imu_synced) == len(mocap_synced))
        print(f"Time range: {imu_synced.index[0]:.3f} to {imu_synced.index[-1]:.3f}")

        imu_block  = imu_synced.reset_index(drop=True)
        mocap_block = mocap_synced.reset_index(drop=True)

        imu_all = pd.concat([imu_all, imu_block], ignore_index=True)
        mocap_all = pd.concat([mocap_all, mocap_block], ignore_index=True)


    # we plot the synced values (sanity check)
    # and compute the metrics
    results = {}
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
    fig, ax = plt.subplots(rows,cols, figsize= (10,2.5*rows))
    ax = ax.flatten()
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
        ax[jjjjj].plot(imu_signal,label="imu"+joint)
        ax[jjjjj].plot(mocap_signal,label="mocap"+joint)
        #plt.legend()
        #plt.title(joint)
        ax[jjjjj].set_title(joint)
        #plt.show()
        rmse = np.sqrt(np.mean((imu_signal - mocap_signal)**2))
        pearson_r, p_value = stats.pearsonr(imu_signal, mocap_signal)

        results[joint] = {'RMSE': rmse, 'Pearson_r': pearson_r}
    plt.show()
    # Make it a nice dataframe
    results_df = pd.DataFrame(results).T
    print(results_df)
    return time_offsets

def header(sub):
    n = 81
    if (n-len(sub))%2 == 1:
        sub+="="
    a = (n - len(sub))//2 
    print("="*n)
    print("="*a + sub +"="*a)
    print("="*n)
