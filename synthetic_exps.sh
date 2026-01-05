#!/usr/bin/env bash

echo "started"
for random_seed in {1..20}; do
    for experiment_type in "GG" "NG" "GN" "NN"; do
        for map_number in {1..3}; do
            for num_r_units in 72 86 58; do
                for block_size in 2 3 4 5; do
                    echo "Running with num_r_units=$num_r_units, map_number=$map_number, block_size=$block_size, experiment_type=$experiment_type, and random_seed=$random_seed"
                    sbatch --job-name="syn-exps" \
                        --nodes=1 \
                        --ntasks=1 \
                        --partition=duchin \
                        --cpus-per-task=2 \
                        --mem=2G \
                        --time=2-00:00:00 \
                        --error="syn_exps_${num_r_units}_${map_number}_${block_size}_${experiment_type}_${random_seed}.log" \
                        --output="syn_output_${num_r_units}_${map_number}_${block_size}_${experiment_type}_${random_seed}.out" \
                        --wrap="PATHONHASHSEED=0 python3 /share/duchin/raina/final_exp_files/syn_exp_cli.py --num-r-units $num_r_units --map-number $map_number --block-size $block_size --experiment-type $experiment_type --random-seed $random_seed --total-steps 10"
                done
            done
        done
    done
done