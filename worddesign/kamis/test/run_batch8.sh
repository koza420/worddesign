#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Set the base filename for the output
output_base="$SCRIPT_DIR/results8/output_8"

# Set the input file and config
input_file="$SCRIPT_DIR/dna_word_graph_8.metis"
config="full_standard"
time_limit=24000
kernelization="full"
red_thres=5000

bash "$SCRIPT_DIR/../codex/scripts/ensure_dna_metis.sh" "$input_file"

# Function to run the command for each seed
run_command() {
    seed=$1
    output_file="${output_base}_${seed}.txt"
    log_file="${output_base}_log_${seed}.txt"
    
    # Debugging: echo the variables being passed
    echo "Running with seed ${seed}, outputting to ${output_file}, logging to ${log_file}..."
    echo "Using config: ${config}, time_limit: ${time_limit}, kernelization: ${kernelization}, red_thres: ${red_thres}"

    # Run the redumis command and redirect output and error to log file
    "$SCRIPT_DIR/../deploy/redumis" "$input_file" --config="$config" --time_limit="$time_limit" --seed="$seed" --kernelization="$kernelization" --red_thres="$red_thres" --output="$output_file" > "$log_file" 2>&1
}

# Export the variables for use in parallel execution
export output_base input_file config time_limit kernelization red_thres

export -f run_command  # Export the function for parallel execution

# Run the redumis command using GNU Parallel with 20 cores for seeds 1 to 100
seq 501 511 | parallel -j 10 run_command

echo "All runs completed."







# #!/bin/bash

# # Set the base filename for the output
# output_base="results8/output_8"

# # Set the input file and config
# input_file="dna_word_graph_8.metis"
# config="full_social"
# time_limit=50000
# kernelization="full"
# red_thres=5000

# # Run the redumis command 10 times with different seeds
# for seed in {1..100}
# do
#     output_file="${output_base}_${seed}.txt"
#     log_file="${output_base}_log_${seed}.txt"
#     echo "Running with seed ${seed}, outputting to ${output_file}, logging to ${log_file}..."
    
#     # Redirect stdout and stderr to log file
#     ../deploy/redumis $input_file --config="$config" --time_limit=$time_limit --seed=$seed --kernelization=$kernelization --red_thres=$red_thres --output="$output_file" > "$log_file" 2>&1 &
# done

# echo "All runs completed."
