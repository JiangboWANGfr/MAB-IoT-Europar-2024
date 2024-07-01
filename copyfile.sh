#!/bin/bash

# the file path
if [ "$#" -eq 1 ]; then
    # if there is only one parameter, use the parameter as the source file
    FILE_PATH=$1
    HOST_PATH="${FILE_PATH%/*}"
elif [ "$#" -eq 2 ]; then
    # if there are two parameters, use the first parameter as the source file and the second parameter as the output file
    FILE_PATH=$1
    HOST_PATH=$2
else
    # else, print the usage and exit
    echo "Usage: $0 <FILE_PATH> [<HOST_PATH>]"
    exit 1
fi

# check the file path,the file path should be a folder
if [ ! -f "$FILE_PATH" ]; then
    echo "[ERROR]: $FILE_PATH is not a file"
    exit 1
fi

#check the file path, the file path should not be /opt /usr /etc
if [ "$FILE_PATH" = "/opt" ] || [ "$FILE_PATH" = "/usr" ]|| [ "$FILE_PATH" = "/etc" ] || [ "$FILE_PATH" = "/home" ]; then
    echo "[ERROR]: $FILE_PATH is not allowed to be removed"
    exit 1
fi

# the ip name of the cluster
hosts=(
    "master" 
	"jetson1" 
	"jetson2" 
	"pi1" 
	"pi2" 
	"pi3" 
	"pi4"
	# "beagleboard1" 
	# "beagleboard2" 
	# "beagleboard3" 
	#"beagleboard4" 
	###"beagleboard5"
	)

# make sure the current host to shutdown at last
current_host="master"

# remove the files in the folder
for host in "${hosts[@]}"; do
    if [ "$host" != "$current_host" ]; then
        #printf "Copying $FILE_PATH to %-7s ... " "$host" 
        if scp $FILE_PATH $host:$HOST_PATH 1>/dev/null;then
        #    echo "[INFO]: Copying $FILE_PATH to $host ... Done "
           printf "[INFO]: Copying $FILE_PATH to %-13s ... Done\n" "$host"
	    else 
           echo -e "\n[WARNING]: $host path don't exist"
	    fi
    else # for the current host
        printf "[INFO]: Copying $FILE_PATH to %-13s ... Done\n" "$host"
    fi
done

echo -e  "[INFO]: COPYING TO ALL NODES DONE\n"
