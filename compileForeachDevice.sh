#!/bin/bash

# chech the parameter number
if [ "$#" -eq 1 ]; then
    # if there is only one parameter, use the parameter as the source file
    SOURCE_FILE=$1
    BASENAME=$(basename "$SOURCE_FILE")
    OUTPUT_FILE="${BASENAME%.c}"
elif [ "$#" -eq 2 ]; then
    # if there are two parameters, use the first parameter as the source file and the second parameter as the output file
    SOURCE_FILE=$1
    OUTPUT_FILE=$2
else
    # else, print the usage and exit
    echo "Usage: $0 <source_file> [<output_file>]"
    exit 1
fi

echo "SOURCE FILE: $SOURCE_FILE"
echo "OUTPUT_FILE: /opt/jiangboMPI/$OUTPUT_FILE"

# exec the remote command to build the file
hosts=("master" "debian1" "jetson1" "jetson2" "debian2" "pi1" "pi2")

# make sure the current host to shutdown at last
current_host="TODO"

# shutdown for all host
for host in "${hosts[@]}"; do
    if [ "$host" != "$current_host" ]; then
        #echo -n "Compileing $host ... "
	printf "Compiling %-7s ... " "$host"
	if ssh pi@$host "sudo /opt/openmpi/bin/mpicc /home/pi/jiangboCloud/$SOURCE_FILE -o /opt/jiangboMPI/$OUTPUT_FILE" 2>/dev/null;then
            echo "finished"
	else 
	    echo -e "\nWARNING: Unable to connect to $host"
	fi
    fi
done

echo "ALL COMPILER FINISHED"
