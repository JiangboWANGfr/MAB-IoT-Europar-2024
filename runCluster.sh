# chech the parameter number
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <BINNARY_PATH>"
    exit 1
fi

# give value to the source file and ouptut file
BINARY_PATH=$1

#cluster hosts name 
hosts=("master" "debian1" "jetson1" "jetson2" "debian2" "pi1" "pi2" "pi3")

/opt/openmpi/bin/mpirun --host pi1:1,pi2:1,jetson1:1,jetson2:1 $BINARY_PATH
