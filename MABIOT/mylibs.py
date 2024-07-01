import random
import numpy as np
import itertools
from functools import reduce
from itertools import combinations
from sympy import symbols, expand

def generateDeviceAllocationRatioOrigin(num_devices, num_allocated_device, precision):
    '''
    Generate all possible allocation ratios for a given number of devices and number of allocated devices,
    ensuring the sum of ratios for allocated devices equals 1.0.
    example: [0.0, 0.0, 0.5, 0.5, 0.0, 0.0]
    '''
    # Step 1: Generate all possible allocation ratios with sum = 1.0
    elements = np.linspace(0, 1, precision)
    ratio_combinations = [comb for comb in itertools.product(elements, repeat=num_allocated_device) if round(sum(comb), 2) == 1.0]
    
    # Step 2: Select device combinations
    device_ids = range(num_devices)
    device_combinations = list(itertools.combinations(device_ids, num_allocated_device))
    
    # Step 3: Allocate ratios to devices and format output
    allocation_list = []
    for device_comb in device_combinations:
        for ratio_comb in ratio_combinations:
            allocation = [0.0] * num_devices  # Initialize allocation for all devices with 0.0
            for device_id, ratio in zip(device_comb, ratio_comb):
                allocation[device_id] = round(ratio, 2)  # Assign ratio to specific devices
            allocation_list.append(allocation)
    
    # remove the duplicate allocation
    unique_allocation_list = []
    for item in allocation_list:
        if item not in unique_allocation_list:
            unique_allocation_list.append(item)
    
    return unique_allocation_list

def get_combinations(n, X):
    """
    calculate the number of combinations of devices for a given number of selected devices.
    :param n: the number of each type of devices. e.g [2, 3, 2]
    :param X: the number of selected devices. e.g 3
    return the number of combinations of devices for a given number of selected devices.
    """
    x = symbols('x')
    
    # create a polynomial for each type of device
    polynomials = [sum(x**k for k in range(i + 1)) for i in n]
    # calculate the product of all polynomials
    product_polynomial = expand(reduce(lambda a, b: a * b, polynomials))
    # get the coefficient of x^X
    coefficient = product_polynomial.coeff(x, X)
    return coefficient

def test_get_combinations():
    n = [2, 3, 2]
    X = 3
    configurations = get_combinations(n, X)
    print(configurations)

# generate all possible combinations of devices for a given number of selected devices
def generate_combinations(devices, num_selected_devices):   
    """
    generate all possible combinations of devices for a given number of selected devices.
    :param devices: the number of each type of devices.r.e.g [2, 3, 2]
    :param num_selected_devices: the number of selected devices. e.g 3
    """
    # transform the devices to the index of the devices
    all_devices = []
    for index, count in enumerate(devices):
        all_devices.extend([index] * count)  #  generate the index of the devices
    # print("all_devices: ", all_devices)
    all_combinations = set(combinations(all_devices, num_selected_devices))  # generate all possible combinations
    # print("all_combinations: ", all_combinations)
    formatted_combinations = []
    for combo in all_combinations:
        # create a list of 0s with the length of all_devices
        combo_list = [0] * len(all_devices)  # initialize the list with 0
        for i in combo:
            combo_list[all_devices.index(i)] = 1  # use the index of the selected devices
            all_devices[all_devices.index(i)] = None  # not allow to use the same index
        formatted_combinations.append(combo_list)
        # reset the all_devices 
        all_devices = []
        for index, count in enumerate(devices):
            all_devices.extend([index] * count)  #  
    # [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],return the index of the selected devices
    formatted_combinations = [[i for i, v in enumerate(combo) if v] for combo in formatted_combinations]
    return formatted_combinations


def generateDeviceAllocationRatio(devices, num_allocated_device, precision):
    '''
    Generate all possible allocation ratios for a given number of devices and number of allocated devices,
    ensuring the sum of ratios for allocated devices equals 1.0.
    example: [0.0, 0.0, 0.5, 0.5, 0.0, 0.0]
    '''
    # Step 1: Generate all possible allocation ratios with sum = 1.0
    elements = np.linspace(0, 1, precision)
    ratio_combinations = [comb for comb in itertools.product(elements, repeat=num_allocated_device) if round(sum(comb), 2) == 1.0]
    
    # Step 2: Select device combinations
    device_combinations = []
    for i in range(1, num_allocated_device + 1):
        device_combinations.extend(generate_combinations(devices, i))
    print("device_combinations: ", device_combinations)
    
    # Step 3: Allocate ratios to devices and format output
    allocation_list = []
    for device_comb in device_combinations:
        for ratio_comb in ratio_combinations:
            allocation = [0.0] * np.sum(devices)  # Initialize allocation for all devices with 0.0
            for device_id, ratio in zip(device_comb, ratio_comb):
                allocation[device_id] = round(ratio, 2)  # Assign ratio to specific devices
            allocation_list.append(allocation)
    
    # remove the duplicate allocation
    unique_allocation_list = []
    for item in allocation_list:
        # if sum of the allocation is 1.0
        if round(sum(item), 2) == 1.0:
            if item not in unique_allocation_list:
                unique_allocation_list.append(item)
    
    return unique_allocation_list


def main():
    devices = [2,4] 
    # devicesForOrigin = 11
    maxchoiceDevices =4
    
    actions = generateDeviceAllocationRatio(devices, maxchoiceDevices, 11)
    # actions = generateDeviceAllocationRatioOrigin(devices, maxchoiceDevices, 11)
    for i, item in enumerate(actions):
        print(i, item)
    print("origin length: ", len(actions))
    
if __name__ == "__main__":
    main()
