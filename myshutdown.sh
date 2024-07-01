#!/bin/bash

# check the number of arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <DEVICE_IP_NAME>"
    exit 1
fi

# the file path
DEVICE_IP_NAME=$1
# the ip name of the cluster
hosts=("jetson1" "jetson2"  "pi1" "pi2" "pi3" "pi4" "beagleboard1" "beagleboard2" "beagleboard3" "beagleboard4" "beagleboard5")  

# make sure the current host to shutdown at last
current_host=$DEVICE_IP_NAME
# shutdown for all host
for host in "${hosts[@]}"; do
    if [ "$host" != "$current_host" ]; then
        echo "[INFO]: Checking SSH connection to $host"
        # using batch mode to check the ssh connection
        if ssh -o BatchMode=yes -o ConnectTimeout=1 "$host" 'echo SSH connection to $HOSTNAME succeeded'; then
            echo "[INFO]: Shutting down $host"
            ssh "$host" 'sudo shutdown -h now' &
        else
            echo "[WARNING]: Cannot establish SSH connection to $host. Skipping shutdown command."
        fi
    fi
done

wait
# shutdown current device
# echo "[INFO]: Shutting down $current_host"
# sudo shutdown -h now
