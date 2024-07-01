#!/bin/bash
clear
# file path
#!/bin/bash
clear

# Define source and target directories
src_dir="/home/pi/jiangboCloud/NPB3.4.2/NPB3.4-MPI/LU/"
dest_dir="/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/LU/"

# First, make sure the target directory exists
mkdir -p $dest_dir

# Copy all files from source directory to target directory
cp -r $src_dir* $dest_dir

# Use the copyfile.sh script to copy files from the target directory to all nodes in the cluster
for file in $dest_dir*; do
     /home/pi/jiangboCloud/copyfile.sh $file
done

# Run makesuite.sh script
#/home/pi/jiangboCloud/makesuite.sh

echo "MAB IOT DATA FLOW FINISHED"
