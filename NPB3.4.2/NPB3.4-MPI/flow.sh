#!/bin/bash
clear

# file path
files=(
   # "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/EP/ep_data.f90"
   "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/EP/ep.f90"
   # "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/EP/mylib.f90"
    # "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/EP/Makefile"
    # "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/EP/verify.f90"
    "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/LU/subdomain.f90"
    "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/common/get_active_nprocs.f90"
    "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/LU/mylib.f90"
    "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/LU/proc_grid.f90"
    "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/LU/ssor.f90"
    "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/LU/verify.f90"
    "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/LU/Makefile"
    "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/LU/lu.f90"
    "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/LU/init_comm.f90"
    "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/config/suite.def"
    # "/home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/config/make.def"
)
#first ,copy the file in /home/pi/jiangboCloud/NPB3.4.2/NPB3.4-MPI/ to /home/pi/NPB3.4.2/NPB3.4-MPI/ dir in master node
# then using copyfile.sh to copy file to all nodes in cluster

for file in "${files[@]}"; do
    descfile=$file 
    # print the file path
    srcfile="${file/jiangboNPB/jiangboCloud}"
    # echo "srcfile: $srcfile"
    cp $srcfile $descfile
done

# using copyfile.sh to copy file to all nodes in cluster
for file in "${files[@]}"; do
    echo "copy $file to all nodes in cluster"
    /home/pi/jiangboCloud/copyfile.sh $file
done
# make suite to check there is no error when building the benchmark
# input flag for make suite or not [1 or t or T or true or TRUE or True]
if [ "$1" == "1" ] || [ "$1" == "t" ] || [ "$1" == "T" ] || [ "$1" == "true" ] || [ "$1" == "TRUE" ] || [ "$1" == "True" ]; then
    echo "make suite"
    make suite
fi
/home/pi/jiangboCloud/makesuite.sh

echo "MAB IOT DATA FLOW FINISHED"

