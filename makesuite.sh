#!/bin/bash
# exec the remote command to build the file
hosts=(
    "master" 
	"pi1" 
	"pi2" 
	"pi3" 
	"pi4" 
	"jetson1"
    "jetson2" 
	# "beagleboard1" 
	# "beagleboard2" 
	# "beagleboard3" 
	##"beagleboard4" 
	#"beagleboard5"
)
current_host="TODO"
total_hosts=${#hosts[@]}
current_index=1

# shutdown for all host
for host in "${hosts[@]}"; do
    if [ "$host" != "$current_host" ]; then
        #echo -n "Compileing $host ... "
	    printf "[INFO]: Compiling %-13s ... [%d/%d]  \n" "$host" "$current_index" "$total_hosts"

        if ssh "$host" 'find /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/bin/ -type f -exec sudo rm {} +'; then
        echo "[INFO]: Successfully removed files in /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/bin/."
        else
            echo -e "\n[ERROR]: Failed to remove files in /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/bin/."
        fi
        # complier command
        if ssh "$host" 'cd /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/ &&make clean > /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/output 2>&1 && make suite >> /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/output 2>&1'; then
            # echo "Compilation succeeded and output is saved to /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/output."
            # check if the binary files are generated
            bin_files=$(ssh "$host" 'ls /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/bin')
            
            if [ -z "$bin_files" ]; then
                echo -e "[ERROR]: No binary files found in /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/bin."
                echo -e "         Compilation failed,please check the output file in /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/output. \n"
                echo -e "---------------------------------Compiler error output-------------------------------------------"
                cat /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/output
                echo -e "-----------------------------------Output error end----------------------------------------------"
                exit 1
            else
                echo -e "[INFO]: Compilation succeeded and output is saved to /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/output."
                echo -n "[INFO]: Find binary "
                echo -n "$(echo $bin_files | tr '\n' ' ') "
                echo -e "in /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/bin \n"
            fi
        else
        echo -e "Compilation failed or unable to connect to $host. \n"
        fi
        ((current_index++))
    fi
done
if [ $? -eq 0 ]; then
    echo "ALL COMPILER FINISHED"
else
    echo "SOME COMPILER FAILED"
fi
