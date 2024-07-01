#!/bin/bash

# define the IP address of the jetson1 and jetson2
jetson1_ip="10.10.5.144"
jetson2_ip="10.10.5.145"

# Define static IP configurations for jetson1 and jetson2's eth0 interfaces
jetson1_eth0_static="192.168.1.4"
jetson2_eth0_static="192.168.1.5"

# Define current eth0:1 IP addresses used for initial connection
jetson1_connect_node="192.168.1.252"
jetson2_connect_node="192.168.1.253"

# Node IP configurations mapping initial connection IPs to new static configurations
declare -A nodes=(
    ["$jetson1_connect_node"]="$jetson1_eth0_static 192.168.1.1"
    ["$jetson2_connect_node"]="$jetson2_eth0_static 192.168.1.1"
)

# Interface down commands for nodes, including the virtual interface eth0:1
declare -A interface_down=(
    ["jetson1"]="docker0"
    ["jetson2"]="docker0"
    ["master"]="eth1 eth2 eth3 eth4"
    ["pi1"]="eth1 eth2 eth3 eth4"
    ["pi2"]="eth1 eth2 eth3 eth4"
    ["pi3"]="eth1 eth2 eth3 eth4"
    ["pi4"]="eth1 eth2 eth3 eth4"
    ["beagleboard1"]="usb0 usb1"
    ["beagleboard2"]="usb0 usb1"
    ["beagleboard3"]="usb0 usb1"
    ["beagleboard4"]="usb0 usb1"
    ["beagleboard5"]="usb0 usb1"

)

# Function to configure network settings on a node
configure_network() {
    local node_ip="$1"
    local new_ip="$2"
    local gateway="$3"
    local current_ip
    if [[ "$node_ip" == "$jetson1_connect_node" ]]; then
        current_ip=$jetson1_ip # Assuming this is the current configuration of jetson1's eth0
    elif [[ "$node_ip" == "$jetson2_connect_node" ]]; then
        current_ip=$jetson1_ip # Assuming this is the current configuration of jetson2's eth0
    fi
    local ssh_command0="sudo ip addr del $current_ip/24 dev eth0"
    local ssh_command1="sudo ip addr add $new_ip/24 dev eth0"
    local ssh_command2="sudo ip route add default via $gateway"
    local ssh_command3="sudo ip addr del $node_ip/24 dev eth0 label eth0:1"
    echo "Configuring $node_ip with IP $new_ip and gateway $gateway"
    ssh "$node_ip" "$ssh_command0"
    ssh "$node_ip" "$ssh_command1"
    ssh "$node_ip" "$ssh_command2"
    ssh "$new_ip"  "$ssh_command3"
    echo "Network configuration complete for $node_ip successfully"
}

# Function to bring down interfaces
bring_down_interfaces() {
    local node_ip="$1"
    local interfaces="${interface_down[$node_ip]}"
    for interface in $interfaces; do
        local ssh_command="sudo ip link set dev $interface down"
        echo "Bringing down interface $interface on node with IP $node_ip"
        ssh "$node_ip" "$ssh_command" &
    done
}

# Main loop for network configuration
# for node_ip in "${!nodes[@]}"; do
#     read new_ip gateway <<< "${nodes[$node_ip]}"
#     configure_network "$node_ip" "$new_ip" "$gateway"
# done

# Main loop for bringing down interfaces
for node_ip in "${!interface_down[@]}"; do
    bring_down_interfaces "$node_ip"
done

#ssh beagleboard3 "sudo ip addr del 10.10.4.205/24 dev eth0"
#ssh beagleboard4 "sudo ip addr del 10.10.4.242/24 dev eth0"
#ssh beagleboard5 "sudo ip addr del 10.10.4.183/24 dev eth0"

# define the IP address of the jetson1 and jetson2  
declare -A ip_map=(
    ["beagleboard3"]="10.10.4.205"
    ["beagleboard4"]="10.10.4.242"
    ["beagleboard5"]="10.10.4.183"
)

# device interface
interface="eth0"

# loop through the IP addresses and check if they exist on the boards
for board in "${!ip_map[@]}"; do
    ip_addr=${ip_map[$board]}

    # using the ip addr show command to check if the IP address exists
    if ssh "$board" "ip addr show $interface | grep -q $ip_addr"; then
        echo "IP $ip_addr found on $board, deleting..."
        # if the IP address exists, delete it using the ip addr del command
        ssh "$board" "sudo ip addr del $ip_addr/24 dev $interface"
    else
        echo "IP $ip_addr not found on $board, no action required."
    fi
done


wait # Wait for all background processes to finish

echo "Network configuration complete"

# */5 * * * * /home/pi/jiangboCloud/remove_ip.sh >> /home/pi/jiangboCloud/removeIp.log 2>&1
