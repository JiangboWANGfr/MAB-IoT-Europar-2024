#!/bin/bash

# check the number of arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <FILE_PATH>"
    exit 1
fi
# the file path
file_PATH=$1

# check the file path,the file path should be a folder
if [ ! -f "$file_PATH" ]; then
    echo "[ERROR]: $file_PATH is not a file"
    exit 1
fi

#check the file path, the file path should not be /opt /usr /etc
if [ "$file_PATH" = "/opt" ] || [ "$file_PATH" = "/usr" ]|| [ "$file_PATH" = "/etc" ] || [ "$file_PATH" = "/home" ]; then
    echo "[ERROR]: $file_PATH is not allowed to be removed"
    exit 1
fi

# the ip name of the cluster
hosts=("master" "debian1" "jetson1" "jetson2" "debian2" "pi1" "pi2")

# make sure the current host to shutdown at last
current_host="TODO"

# remove the files in the folder
for host in "${hosts[@]}"; do
    if [ "$host" != "$current_host" ]; then
        printf "[INFO]: Removing $file_PATH on %-7s ... " "$host" 
        if ssh pi@$host "sudo rm -rf $file_PATH" 2>/dev/null;then
            echo -e "Done"
	else 
           echo -e "\n[WARNING]: Unable to connect to $host"
	fi
    fi
done

echo -e  "\n[INFO]: REMOVING $file_PATH FOR ALL HOSTS DONE"
