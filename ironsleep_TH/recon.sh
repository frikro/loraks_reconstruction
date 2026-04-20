#!/bin/bash

#
#SBATCH -c 16					# 16 cores for fast reco
#SBATCH --mem 1000G				# 0.5 mm fully sampled is around 220G, need maybe double
#SBATCH --time 1440				# 10 echoes at 2 hours per echo but some nodes take 3 hours per echo
#SBATCH -o /data/u_krohn_software/git/loraks_reconstruction/%j.out	# redirect the output
#SBATCH --mail-user=friedrich.krohn@gmx.net
#SBATCH --mail-type=ALL
# Real values for (16 cores, 500G request) are 213G RAM 8.5hrs time 27G file (PDw/T1w), 121G 6.5hrs 10G (MTw)

rawdata=$1
outdir=$2

echo "rawdata: $rawdata"
echo "outdir: $outdir"

# Use adjRank config if rawdata filename contains "smap" or "sens"
if [[ "$rawdata" == *"smap"* ]] || [[ "$rawdata" == *"sens"* ]]; then
    config="/data/u_krohn_software/git/loraks_reconstruction/ironsleep_TH/loraksConfig_adjRank.json"
    echo "Detected 'smap' or 'sens' in filename, using adjRank config"
else
    config="/data/u_krohn_software/git/loraks_reconstruction/ironsleep_TH/loraksConfig.json"
fi

start=$(date +%s)

MATLAB -v 24.2 matlab -batch "cd /data/u_krohn_software/git/image-reconstruction/; reconstruction('$rawdata','$outdir','$config');exit"

end=$(date +%s)
duration=$((end - start))
echo "Duration: $((duration / 60)) minutes"
