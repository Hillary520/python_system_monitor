#!/bin/bash

# Stress test script for testing CPU utilization patterns
# This script creates varying load patterns on different CPU core combinations
# to test the system monitor's CPU tracking capabilities.

# Configuration parameters
CYCLES=5          # Number of complete wave pattern repetitions
GROUP_DURATION=3  # Duration (seconds) of stress for each core group
MAX_CORE=7        # Highest CPU core index (0-7 for 8 cores)

# Pre-validated core groups for different stress patterns
VALID_GROUPS=(
    "0,1"    "2,3"    "4,5"    "6,7"     # Adjacent core pairs
    "0,2,4,6" "1,3,5,7"                   # Even/odd cores (cross-core testing)
    "0,7"    "1,6"    "2,5"    "3,4"     # Distance-based pairs (thermal spread)
)

validate_group() {
    local group="$1"
    [[ -z "$group" ]] && return 1
    
    IFS=',' read -ra cores <<< "$group"
    (( ${#cores[@]} == 0 )) && return 1

    for core in "${cores[@]}"; do
        if ! [[ "$core" =~ ^[0-9]+$ ]] || 
           (( core < 0 || core > MAX_CORE )); then
            echo "   ❌ Invalid core: $core (valid 0-$MAX_CORE)" >&2
            return 1
        fi
    done
    return 0
}

stress_group() {
    local group="$1"
    echo "   🔥 Firing cores [${group}]"
    if taskset -c "$group" stress-ng --cpu 4 --matrix 1 --cache 2 --timeout ${GROUP_DURATION}s; then
        echo "   ✅ Stressed cores ${group} successfully"
    else
        echo "   ❗ Failed to stress cores ${group}"
    fi
}

echo "🌀 Starting Stress Wave Pattern (${CYCLES} cycles)"
for ((cycle=1; cycle<=CYCLES; cycle++)); do
    echo -e "\n🔁 Cycle ${cycle}/${CYCLES}"
    
    # Generate safe group list
    SAFE_GROUPS=()
    while read -r group; do
        if validate_group "$group"; then
            SAFE_GROUPS+=("$group")
        fi
    done < <(printf "%s\n" "${VALID_GROUPS[@]}" | shuf)
    
    # Process validated groups
    for group in "${SAFE_GROUPS[@]}"; do
        stress_group "$group" &
        sleep 1
    done
    
    wait
    echo "🆗 Cycle ${cycle} complete"
    sleep 2
done