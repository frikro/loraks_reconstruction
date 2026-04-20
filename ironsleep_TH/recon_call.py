#!/usr/bin/env python3

"""
This script is used to submit reconstruction jobs to a computing cluster using SLURM. 
It reads configuration variables from config.py, constructs input and output paths, and submits jobs 
for each subject and session specified in the configuration.
Functions:
    sbatch_commands: Submits jobs to the cluster for each subject and session.
    This function iterates over the subjects and sessions specified in the configuration,
    constructs the necessary input and output paths, and submits SLURM jobs for T1-weighted,
    PD-weighted, and MT-weighted raw data reconstruction.
    Raises:
        TypeError: If the subject name is not a string or if the session name is not a string or list.
"""


import os
import warnings
import json
from datetime import datetime

import config_first_pipeline_2026_04_16 as config # import the correct config file


# script defining slurm parameters and reconstruction command
script_dir = os.path.dirname(os.path.abspath(__file__))
recon_script = os.path.join(script_dir, 'recon.sh')

# configuration variables
input_parent = config.input_parent
output_parent = config.output_parent
t1w_raw = config.t1w_raw
pdw_raw = config.pdw_raw
mtw_raw = config.mtw_raw
ernst_raw = config.ernst_raw
b1afi_ptx_raw = config.b1afi_ptx_raw
b1afi_stx_raw = config.b1afi_stx_raw
sub_ses = config.sub_ses
name_storage_dir = config.name_storage_dir
with_smaps = config.with_smaps
smaps_per_session = config.smaps_per_session


## check if input_parent and output_parent exist
if not os.path.exists(input_parent):
    raise FileNotFoundError(f"Input parent directory {input_parent} does not exist")

if not os.path.exists(output_parent):
    print(f"Output parent directory {output_parent} does not exist. Creating it now.")
    os.makedirs(output_parent, exist_ok=True)

## define which data to reconstruct
t1w_recon = bool(t1w_raw)
pdw_recon = bool(pdw_raw)
mtw_recon = bool(mtw_raw)
ernst_recon = bool(ernst_raw)
b1afi_ptx_recon = bool(b1afi_ptx_raw)
b1afi_stx_recon = bool(b1afi_stx_raw)


## if with_smaps, each session is used twice to account for the accompanying sensitivity maps
if with_smaps:
    new_sub_ses = []
    for sj, ss in sub_ses:
        extended_sessions = []
        for s in ss:
            extended_sessions.extend([s] * (smaps_per_session + 1))
        new_sub_ses.append([sj, extended_sessions])
    sub_ses = new_sub_ses

# check if sub_ses, t1w, pdw, and mtw are of the same length
number_of_sessions = 0
for _, sessions in sub_ses:
    if isinstance(sessions, list):
        number_of_sessions += len(sessions)
    elif isinstance(sessions, str):
        number_of_sessions += 1
    else:
        raise TypeError(f"Sessions must be of type list or string, got {type(sessions).__name__}")

# Keep in mind: if with_smaps=True, the number of sessions is doubled
if pdw_recon and sum(len(sl) for sl in pdw_raw) != number_of_sessions:
    raise ValueError("Length of pdw_raw must be the same as the number of sessions")
if t1w_recon and sum(len(sl) for sl in t1w_raw) != number_of_sessions:
    raise ValueError("Length of t1w_raw must be the same as the number of sessions")
if mtw_recon and sum(len(sl) for sl in mtw_raw) != number_of_sessions:
    raise ValueError("Length of mtw_raw must be the same as the number of sessions")
if ernst_recon and sum(len(sl) for sl in ernst_raw) != number_of_sessions:
    raise ValueError("Length of ernst_raw must be the same as the number of sessions")


def sbatch_commands():
    output_paths_raw = {}  # store paths to the raw data for each subject and session -> export as json at the end of the script

    """
    Submit jobs to the cluster
    """
    for i, (subject_name, session_name) in enumerate(sub_ses):

        if not isinstance(subject_name, str):
            raise TypeError("Subject (sub_ses[0]) must be of type string")

        if isinstance(session_name, str):
            session_name = [session_name] # convert session element to list for iteration
        
        if isinstance(session_name, list):
            for j, sess in enumerate(session_name):
                
                # specify output directory (reconstructed data)
                output_dir = os.path.join(output_parent, subject_name, sess, name_storage_dir)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                
                if any(os.path.isfile(os.path.join(output_dir, f)) for f in os.listdir(output_dir)):
                    warnings.warn(f"Output path {output_dir} is not empty. Skipping this session.")
                    continue
                
                # specify input directory (raw data)
                input_path = os.path.join(input_parent, subject_name, sess, "raw")
                session_data = {}
                
                if t1w_recon:
                    if not t1w_raw[i][j]:
                        pass # no batch job submitted
                    else:
                        t1w_input_path = os.path.join(input_path, t1w_raw[i][j])
                        if not os.path.exists(t1w_input_path):
                            raise FileNotFoundError(f'T1-weighed image {t1w_recon} not found')
                        os.system(f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {t1w_input_path} {output_dir}')
                        print(
                            f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {mtw_input_path} {output_dir}')
                        session_data['t1w'] = t1w_input_path
                
                if pdw_recon:
                    if not pdw_raw[i][j]:
                        pass # no batch job submitted
                    else:
                        pdw_input_path = os.path.join(input_path, pdw_raw[i][j])
                        if not os.path.exists(pdw_input_path):
                            raise FileNotFoundError(f'PD-weighed image {pdw_input_path} not found')
                        os.system(f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {pdw_input_path} {output_dir}')
                        print(
                            f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {mtw_input_path} {output_dir}')
                        session_data['pdw'] = pdw_input_path

                if mtw_recon:
                    if not mtw_raw[i][j]:
                        pass # no batch job submitted
                    else:
                        mtw_input_path = os.path.join(input_path, mtw_raw[i][j])
                        if not os.path.exists(mtw_input_path):
                            raise FileNotFoundError(f'MT-weighed image {mtw_input_path} not found')
                        os.system(f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {mtw_input_path} {output_dir}')
                        print(f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {mtw_input_path} {output_dir}')
                        session_data['mtw'] = mtw_input_path
                
                if ernst_recon:
                    if not ernst_raw[i][j]:
                        pass # no batch job submitted
                    else:
                        ernst_input_path = os.path.join(input_path, ernst_raw[i][j])
                        if not os.path.exists(ernst_input_path):
                            raise FileNotFoundError(f'Ernst image {ernst_input_path} not found')
                        os.system(f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {ernst_input_path} {output_dir}')
                        print(
                            f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {mtw_input_path} {output_dir}')
                        session_data['ernst'] = ernst_input_path
                
                if b1afi_ptx_recon:
                    if not b1afi_ptx_raw[i][j]:
                        pass # no batch job submitted
                    else:
                        # B1AFI maps stored in a separate directory, as they are excluded from the bidsification at the moment
                        b1afi_output_dir = os.path.join(output_dir, "AFIB1_reco")
                        if not os.path.exists(b1afi_output_dir):
                            os.makedirs(b1afi_output_dir, exist_ok=True)
                        b1afi_ptx_input_path = os.path.join(input_path, b1afi_ptx_raw[i][j])
                        if not os.path.exists(b1afi_ptx_input_path):
                            raise FileNotFoundError(f'B1 ptx image {b1afi_ptx_input_path} not found')
                        os.system(f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {b1afi_ptx_input_path} {b1afi_output_dir}')
                        print(
                            f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {mtw_input_path} {output_dir}')
                        # os.system(f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {b1afi_ptx_input_path} {output_dir}')
                        session_data['b1afi_ptx'] = b1afi_ptx_input_path
                
                if b1afi_stx_recon:
                    if not b1afi_stx_raw[i][j]:
                        pass # no batch job submitted
                    else:
                        # B1AFI maps stored in a separate directory, as they are excluded from the bidsification at the moment
                        b1afi_output_dir = os.path.join(output_dir, "AFIB1_reco") 
                        if not os.path.exists(b1afi_output_dir):
                            os.makedirs(b1afi_output_dir, exist_ok=True)
                        b1afi_stx_input_path = os.path.join(input_path, b1afi_stx_raw[i][j])
                        if not os.path.exists(b1afi_stx_input_path):
                            raise FileNotFoundError(f'B1 stx image {b1afi_stx_input_path} not found')
                        os.system(f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {b1afi_stx_input_path} {b1afi_output_dir}')
                        print(
                            f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {mtw_input_path} {output_dir}')
                        # os.system(f'sbatch -p standard,group_servers,gr_weiskopf {recon_script} {b1afi_stx_input_path} {output_dir}')
                        session_data['b1afi_stx'] = b1afi_stx_input_path

                # store paths to the raw data for each subject and session
                if subject_name not in output_paths_raw:
                    output_paths_raw[subject_name] = {}
                output_paths_raw[subject_name][sess] = session_data

        else:
            raise TypeError("Session (sub_ses[1]) must be of type string or list")

    
    # export paths that were used for reconstruction for documentation purposes
    current_time = datetime.now().strftime("%Y%m%d_%H%M")
    output_filename = f'loraks_rawData_{current_time}.json'
    with open(os.path.join(output_parent, output_filename), 'w') as json_file:
        json.dump(output_paths_raw, json_file, indent=4)



if __name__ == "__main__":
    sbatch_commands()
