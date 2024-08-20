# Evaluation of Multi-Armed Bandit Algorithms for Efficient Resource Allocation in Edge Platforms

This repository contains the implementation of the algorithms and experiments described in the paper: "Evaluation of Multi-Armed Bandit Algorithms for Efficient Resource Allocation in Edge Platforms" by Jiangbo Wang, Stéphane Zuckerman, and Juan Angel Lorenzo del Castillo.

## Overview

As computational systems become more heterogeneous, designing high-performance and energy-efficient scheduling policies for Edge/IoT platforms is crucial. This project evaluates multi-armed bandit (MAB) strategies for efficient resource allocation in Edge platforms, such as smart cities or smart buildings, focusing on parallel performance and energy usage optimization.

The resource allocation methods proposed extend beyond simulations, involving real tasks run on actual IoT devices, demonstrating that MAB scheduling can effectively balance execution time and power consumption.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Structure](#structure)

## Installation

To run the project, ensure you have the necessary hardware and software requirements:

### Hardware Requirements

- 2 NVIDIA Jetson TX2s
- 4 Raspberry Pi 4s
- 5 BeagleBoard Blacks

### Software Requirements

- Python 3.x
- OpenMPI (Message Passing Interface)
- NAS Parallel Benchmarks (NPB) suite

### Steps

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/JiangboWANGfr/MAB-IoT-Europar-2024.git
   cd MAB-IoT-Europar-2024
   ```

2. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Setup MPI:**

   Ensure MPI is installed and configured on all devices. Refer to [MPI Installation Guide](https://www.open-mpi.org/software/ompi/v5.0/) for detailed instructions.

## Usage

### Running Experiments

1. **Configure Devices:**

   Ensure all IoT devices are connected via an Ethernet switch and properly configured to communicate with each other.

2. **Execute Benchmarks:**

   Run the MPI version of the NAS Parallel Benchmarks (NPB) suite:

   ```bash
   mpirun -host <device_name>:<number_of_processes> <npb-benchmark>.<class> device_name1 task_percentage1 device_name2 task_percentage2 device_name3 task_percentage3 device_name4 task_percentage4
   ```

   Replace `<number_of_processes>`, `<hostfile>`, `<benchmark>`, and `<class>` with appropriate values based on your experiment setup.
   For example: 
   ```bash
    /opt/openmpi/bin/mpirun -host jetson2:6,pi1:4 /home/pi/NPB3.4.2/NPB3.4-MPI/bin/ep.S.x jetson 0.1 rpi4 0.9 rpi4 0.0 jetson 0.0 
   ```

### Modifying Benchmarks

The EP (Embarrassingly Parallel) and LU benchmarks have been modified to accept parameters such as device type and allocation percentage. These benchmarks can be executed with varying parameters to observe performance and power consumption metrics.

## Structure

The repository is organized as follows:

- `NPB3.4.2/`: Contains the source code for NPB benchmark modifications.
- `/`: Scripts and configurations for running experiments.
- `MABIOT/`: Contains the source code for the MAB algorithms 
    - `Utils/`: The Utils folder contains utility scripts and functions that support the main operations of the project. These utilities include helper functions for data manipulation, file handling, logging, and other common tasks needed across the project.
    - `dataprocess/`: The dataprocess folder is dedicated to scripts and modules responsible for processing data which we get after traing.
    - `log/`: The log folder stores log files generated during the execution of the project. These logs are useful for tracking the progress of experiments, debugging issues, and understanding the behavior of the algorithms over time.
    -`model/`: Result model after training.
    -`myagent/`: The myagent folder includes the agent scripts that utilize the MAB algorithms for decision-making. These agents interact with the IoT devices, make scheduling decisions, and allocate tasks based on the learned models to optimize performance and power consumption.
