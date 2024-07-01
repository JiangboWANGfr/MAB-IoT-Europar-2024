#!/bin/bash 
clear
# define the hosts list
declare -a hosts=(
    "pi1:4,pi4:4"
    "pi1:4,pi2:4"
    "pi1:4,pi3:4"
    "pi2:4,pi4:4"
    "pi3:4,pi4:4"
    "beagleboard1:1,beagleboard2:1"
    "beagleboard3:1,beagleboard4:1"
    "pi1:4,jetson1:6"
    "pi2:4,jetson2:6"
    "jetson1:6,jetson2:6"
    "jetson1:6,beagleboard1:1"
    "jetson1:6,beagleboard2:1"
    "jetson1:6,beagleboard3:1"
    "jetson1:6,beagleboard4:1"
    "jetson1:6,beagleboard5:1"
    "jetson2:6,beagleboard3:1"
    "jetson2:6,beagleboard4:1"
    "jetson2:6,beagleboard5:1"
    "pi1:4,pi4:4"
)

# get the name of the hosts list
raspberry_pi_hosts=("pi1" "pi2" "pi3" "pi4")
beagleboard_hosts=("beagleboard1" "beagleboard2" "beagleboard3" "beagleboard4" "beagleboard5")
jetson_hosts=("jetson1" "jetson2")

run_test_num=${#hosts[@]}
# define the mpi run cmd
mpi_cmd_template="/opt/openmpi/bin/mpirun --host {{HOSTS}} /home/pi/NPB3.4.2/NPB3.4-MPI/bin/ep.S.x {{REPLACE_HOSTS}}"

# Loop through the hosts and exec the cmd
for i in "${!hosts[@]}"; do
    # printf ------------%14s Test $i/$run_test_num start ---------------- \n" "${hosts[i]}
    echo -e "------------------------- Test $(($i + 1))/$run_test_num start -------------------------"
    echo -e "[DUBEG]: Hosts: ${hosts[i]}"
    # change the cmd HOSTS to the real host
    # cmd=${mpi_cmd//"{{HOSTS}}"/${hosts[i]}}
    
    # Initialize replace_hosts string
    replace_hosts=""
    # Split hosts[i] into individual host:count pairs
    IFS=',' read -ra ADDR <<< "${hosts[i]}"
    for j in "${ADDR[@]}"; do
        # Split each pair by ':'
        IFS=':' read -r hostname count <<< "$j"
        count=0.5
        # if hostname is in raspberry_pi_hosts, hostname=rpi4
        if [[ " ${raspberry_pi_hosts[@]} " =~ " ${hostname} " ]]; then
            hostname="rpi4"
        fi
        # if hostname is in jetson_hosts, hostname=jetson
        if [[ " ${jetson_hosts[@]} " =~ " ${hostname} " ]]; then
            hostname="jetson"
        fi
        # if hostname is in beagleboard_hosts, hostname=beagleboard
        if [[ " ${beagleboard_hosts[@]} " =~ " ${hostname} " ]]; then
            hostname="beagleboard"
        fi
        # Append to replace_hosts string
        if [ -n "$replace_hosts" ]; then
            replace_hosts+=" "
        fi
        replace_hosts+="$hostname $count"
    done
    # printf "[DUBEG]: Replace hosts: $replace_hosts\n"
    cmd=${mpi_cmd_template//"{{HOSTS}}"/${hosts[i]}}
    cmd=${cmd//"{{REPLACE_HOSTS}}"/$replace_hosts}
    # exec the cmd
    eval "$cmd"
    echo -e "------------------------- Test $(($i + 1))/$run_test_num done --------------------------\n"
done

echo "ALL TESTS DONE"
