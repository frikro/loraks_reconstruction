#!/usr/bin/env python3

## subject names and session names
## if there are multiple sessions for a subject, the session names should be in a list
sub_ses = [["sub_1", ["sess_1","test_ses"]]
]

## directories of subjects and sessions for input and output
input_parent = "/data/pt_02262/data/temp/Kerrin_scans/histopark/first_pipeline_2026_04_10/source/"
output_parent = "/data/pt_02262/data/temp/Kerrin_scans/histopark/first_pipeline_2026_04_10/source/"
name_storage_dir = "nii_loraks_recon"   # name of the directory in the output_parent where the reconstructed data will be stored

with_smaps = False # boolean, specifies if sensitivity maps are also reconstructed
                   # each session file MUST have a corresponding sensitivity map file (2x length of t1w_raw, pdw_raw, mtw_raw)
                   # handled so that each specified session in sub_ses is used twice
smaps_per_session = 0 # integer, number of sensitivity maps per session

## specifying names of the actual pdw, t1w, mtw, and ernst .dat files
## Each one has to be a nested list, where the sessions of each subject are specified in a separate list.
pdw_raw = [[  
              "pdw_kp_mtflash3d_v1t3_0p6_2047.dat",
              "pdw_kp_mtflash3d_v1t3_0p6_2044.dat",
           ]
]
           
t1w_raw = [[  
              "t1w_kp_mtflash3d_v1t3_0p6_2043.dat",
              "",

           ]
]

mtw_raw = [[  
              "mtw_kp_mtflash3d_v1t3_0p6_2046.dat",
              "",
     ]
]
ernst_raw = [[
              "ernst_kp_mtflash3d_v1s_0p5_sag_2049.dat",
              "",
     ]
]

b1afi_ptx_raw = None

b1afi_stx_raw = None
