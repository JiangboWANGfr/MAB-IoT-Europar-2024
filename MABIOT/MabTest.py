import argparse
import numpy as np
import os
import re
import logging
import yaml
import time
import queue
import numpy as np
import logging
import subprocess
import random
import pickle
from tqdm import trange
from datetime import datetime
from myagent.ucb.ucb1 import UCB1
from myagent.ucb.ucb2 import UCB2
from myagent.exp3.exp3 import EXP3
import Utils.customlogger as customlogger
import concurrent
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Lock,Condition
from mylibs import generateDeviceAllocationRatio
from concurrent.futures import as_completed

# TEST TEST
def setupGlobalLogger(cfg):
    '''
    Set up the global logger
    cfg: the configuration file :config.yml
    '''
    logpath = cfg.get('logPath')  # get the log path from the config file
    # each run,create a new log file
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    logfilename = os.path.join(logpath, f'agent_{timestamp}.log')
    os.makedirs(logpath, exist_ok=True) # create the log path if it does not exist
    global mablogging  # set the logging as global variable
    mablogging = customlogger.setupCustomLogger('agent', filename=logfilename, level=logging.DEBUG)


def randomPolicyFixedValues(devicesNumbers, allocatedIoTNodenumEachTask):
    '''
    Randomly select the allocatedIoTNodenumEachTask nodes from the devicesNumbers nodes
    Randomly select fixed_values for task allocation ensuring their sum is 1
    Allocate the task to the selected nodes
    devicesNumbers: the total number of IoT cluster nodes
    allocatedIoTNodenumEachTask: the number of nodes allocated for each task
    '''
    # Ensure the sum of the task allocations is 1
    # Define fixed values for task allocation
    fixed_values = np.arange(0, 1.1, 0.1)
    # Randomly select the allocatedIoTNodenumEachTask nodes from the devicesNumbers nodes
    selectedNodes = np.random.choice(range(devicesNumbers), allocatedIoTNodenumEachTask, replace=False)
    # Randomly select fixed_values for task allocation ensuring their sum is 1
    selectedValues = np.random.choice(fixed_values, 1, replace=False)
    selectedValues = np.append(np.round(selectedValues, 1),np.round( 1 - selectedValues, 1))
    # Allocate the task to the selected nodes
    taskAllocation = dict(zip(selectedNodes, selectedValues))
    
    return taskAllocation


class TaskManager:
    def __init__(self, cfg,totalTaskNum):
        '''
        cfg: the configuration file :config.yml
        totalTaskNum: the total number of tasks
        taskQueue: the queue for the tasks
        taskStatus: the status of the tasks
        '''
        self.cfg = cfg
        self.taskQueue = []
        self.taskkCompletionCallbacks = {
            "type1": self.onType1Completed,
            "type2": self.onType2Completed
        }
        self.execution_time = None
        self.firstTimeToRunReserveTask = True   
        self.shutdownFlag = False
        self.resultqueue = queue.Queue()
        self.totalTaskNum = totalTaskNum
        self.taskStatus = {f"type{i}": 0 for i in range(totalTaskNum)}  # 0: not started, 1: processing, 2: completed   
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.futures = []
        self.taskID = 0
        self.iotDeviceManager = IoTDeviceManager(cfg)  
        self.action = generateDeviceAllocationRatio(cfg.get('devicesNumbers'), cfg.get('allocatedIoTNodenumEachTask'),11)
    
    def executeTaskInterface(self, taskType, selectedNodes):
        '''
        there are multiple tasks ned to be executed, so we use the thread pool to execute the tasks
        taskType: the task type
        '''
        if selectedNodes is None:
            mablogging.warning("selectedNodes is None")
            return
        else:
            if taskType in self.taskkCompletionCallbacks:
                self.updateTaskStatus(taskType, 0)
                try:
                    future = self.executor.submit(self.task_wrapper, taskType , selectedNodes)
                    future.add_done_callback(self.taskkCompletionCallbacks[taskType])
                    self.futures.append(future)
                    # try:
                    #     result = future.result(timeout=2)
                    # except concurrent.futures.TimeoutError:
                    #     print("Task has timed out and will be cancelled")
                    #     cancelled = future.cancel()  
                    #     if cancelled:
                    #         print("Task was successfully cancelled before it started running.")
                    #     else:
                    #         print("Task could not be cancelled since it was already running.")
                            
                except Exception as e:
                    mablogging.error(f"Error: test {e}")
                    
    def task_wrapper(self, taskType, selectedNodes):
        '''
        task wrapper: execute the task based on the task type
        '''
        taskTypeId = self.getTaskTypeId(taskType)
        if taskTypeId == 1:
            mablogging.info(f"Task{taskTypeId} started,with selectedNodes: {selectedNodes}")
        if taskType == "type1":
            return self.mainTask(taskTypeId, selectedNodes)
        elif taskType == "type2":
            return self.ReserveTask(taskTypeId, selectedNodes)

    def mainTask(self, taskTypeId, selectedNodes):
        '''
        main task: this is the task that we care about, we need to get the execution time and the power consumption
        for the MAB algorithm
        '''
        returnResult = self.executeTask(taskTypeId, selectedNodes)
        return returnResult
    
    def ReserveTask(self, taskTypeId, selectedNodes):
        '''
        Reserve task: this is the task that we do not care about, we just need execute it to reserve the nodes,
        so that the nodes are not available for the main task
        '''
        returnResult = self.executeTask(taskTypeId, selectedNodes)
  
    def mainTask1(self, taskType, selectedNodes):
        '''
        main task: this is the task that we care about, we need to get the execution time and the power consumption
        for the MAB algorithm
        '''
        execution_time = 0.01
        returnResult = self.fakeexecuteTask(taskType, selectedNodes, execution_time)
        return returnResult
    
    def ReserveTask1(self, taskType, selectedNodes):
        '''
        Reserve task: this is the task that we do not care about, we just need execute it to reserve the nodes,
        so that the nodes are not available for the main task
        '''
        execution_time = 0.05
        returnResult = self.fakeexecuteTask(taskType, selectedNodes, execution_time)
        return returnResult   
    
    def startReserveTask(self, selectedNodes,actionSpaceNum,step):
        '''
        start the reserve task: we cann't start the reserve task at the first time, because we need to 
                                wait the MAB algorithm to init, that means the first actionSpaceNum steps
                                we do not need to run the reserve task
        actionSpaceNum: the number of the action space
        step: the current step
        '''
        if step > actionSpaceNum and self.firstTimeToRunReserveTask:
            for i in range(self.cfg.get('taskParameter')):
                if i == 0:
                    type2SelectedNodes = {i: 1.0}
                else:
                    type2SelectedNodes.update({i: 0.0})
            # print(f"seletedNodestype2: {seletedNodestype2}")
            print("type2 first time to run, with selectedNodes: ",type2SelectedNodes)
            self.iotDeviceManager.waitForNodesToBeAvailable(2,type2SelectedNodes)
            self.executeTaskInterface("type2", type2SelectedNodes)
            self.firstTimeToRunReserveTask = False
                
    def sotpReserveTask(self,step):
        '''
        stop the reserve task: we need to stop the reserve task after the main task is done
        step: the current step
        '''
        if step >=self.cfg.get('steps')-1:
            for future in self.futures:
                if future.running():
                    future.cancel()
            self.shutdownFlag = True
            self.executor.shutdown(wait=True)
            
    def fakeexecuteTask(self,tasktypeId, selectedNodes,execution_time):
        '''
        Execute the real task
        command: the command to execute the task
        selectedNodes: the selected nodes for the task, a dictionary, key is the node id, value is the allocation Ratio
                       for example {1: 0.5, 2: 0.5}
        taskType: the task type
        '''
        # print(f"Task {taskType} ,with selectedNodes: {selectedNodes} started")
        command = self.getExecutionCommand(selectedNodes, tasktypeId)
        time.sleep(execution_time)  
        self.updateTaskStatus(tasktypeId, 2)
        self.iotDeviceManager.updateDeviceStatus(tasktypeId,selectedNodes,2)
        returnResult = {
            "stdout": "Task completed",
            "stderr": "N/A",
            "executionTime": execution_time
            }
        return returnResult
        
    def executeTask(self,tasktypeId, selectedNodes):
        '''
        Execute the real task
        command: the command to execute the task
        selectedNodes: the selected nodes for the task, a dictionary, key is the node id, value is the allocation Ratio
                       for example {1: 0.5, 2: 0.5}
        tasktypeId: the task type
        '''
        self.iotDeviceManager.updateDeviceStatus(tasktypeId,selectedNodes,1)
        command = self.getExecutionCommand(selectedNodes, tasktypeId)
        shreshouldTime = 30
        start_time = time.time()
        try:
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=shreshouldTime)
        except subprocess.TimeoutExpired:
            # create result with return code 1
            result = subprocess.CompletedProcess(command, 1, "Timeout", "Timeout")
            mablogging.error(f"Task{tasktypeId} has timed out and will be cancelled")        
        end_time = time.time()
        # print(f"Task {tasktypeId} STDOUT:\n{result.stdout}")
        if result != None:
            if tasktypeId == 1:
                # mablogging.info(f"Task{tasktypeId} STDOUT:\n{result.stdout}")
                patterns = {
                'CPUTime': r"CPU Time\s+=\s+([\d\.]+)",
                'TotalPowerConsumption': r"Total PowerConsumption:\s*([\d\.]+)", #
                'TotalPowerConsumptionreward': r"Power consumption\(1\/p\):\s*([\d\.]+)", 
                }
                # print("patterns: ",patterns["CPUTime"])
                match = re.search(patterns["CPUTime"], result.stdout)
                if match:
                    executionTime = float(match.group(1))
                    mablogging.info(f"Task{tasktypeId} task completed, execution time  within python:: {end_time-start_time}")
                else:
                    executionTime = end_time - start_time
                mablogging.info(f"Task{tasktypeId} task completed, execution time {executionTime}")
            if tasktypeId == 2:
                executionTime = end_time - start_time
                mablogging.debug(f"Task{tasktypeId} task completed, execution time within python: {executionTime}")
        else:
            executionTime = end_time - start_time
            mablogging.debug(f"Task{tasktypeId} task completed, execution time within python: {executionTime}")
        # update the device status after the task is done
        self.updateTaskStatus(tasktypeId, 2)
        self.iotDeviceManager.updateDeviceStatus(tasktypeId,selectedNodes,2)
        if result.returncode != 0:
            # print(f"Task {tasktypeId} failed with return code: {result.returncode}")
            mablogging.error(f"Task {tasktypeId} failed with return code: {result.returncode}")
        executionResult = {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "executionTime": executionTime
            }
        return executionResult      
    
    def getTaskTypeId(self,taskType):
        '''
        get the task type id
        '''
        taskTypeIds = {
            "type1": 1,
            "type2": 2
        }
        return taskTypeIds[taskType]
        
    def onType1Completed(self, future: Future):
        '''
        the callback function for the type1 task( the main task)
        '''
        executionResult = future.result()
        execution_time = executionResult.get("executionTime")
        # print(f"Type1 task completed, execution time: {execution_time}")
        # mablogging.info(f"Type1 task completed, execution time: {execution_time}")
        self.resultqueue.put(executionResult)

    def onType2Completed(self, future: Future):
        '''
        the callback function for the type2 task( the reserve task)
        '''
        # executionResult = future.result()
        # execution_time = executionResult.get("executionTime")
        # print("Type2 task completed with execution time: ", execution_time)
        # mablogging.info("Type2 task completed with execution time: %s", execution_time)
        #random generate the selected nodes and the allocation ratio
        type2SelectedNodes = random.choice(self.action)
        type2SelectedNodes =  {index: value for index, value in enumerate(type2SelectedNodes) if value != 0}
        taskParameter = self.cfg.get('taskParameter')
        if len(type2SelectedNodes) < taskParameter:
            for _ in range(taskParameter-len(type2SelectedNodes)):
                # the index of the selected nodes should be unique
                index = random.randint(0,taskParameter-1)
                while index in type2SelectedNodes:
                    index = random.randint(0,taskParameter-1)
                type2SelectedNodes[index] = 0.0
        self.iotDeviceManager.waitForNodesToBeAvailable(2,type2SelectedNodes)
        mablogging.debug(f"Type2 task started, with selectedNodes: {type2SelectedNodes}")
        if not self.shutdownFlag:
            self.executeTaskInterface("type2", type2SelectedNodes)
       
            
    def onType2Completed1(self, future: Future):
        '''
        the callback function for the type2 task( the reserve task)
        '''
        type2Selectedaction = random.choice(self.action)
        type2SelectedNodes = {}
        maxdevices = self.cfg.get('devicesNumbers')        
        allocatedDevices = self.cfg.get('allocatedIoTNodenumEachTask')
        for i in range(0, maxdevices):
            if type2Selectedaction[i] != 0:
                type2SelectedNodes[i] = type2Selectedaction[i]
            if len(type2SelectedNodes) == allocatedDevices:
                break
        for i in range(0, allocatedDevices):
            if len(type2SelectedNodes) < allocatedDevices:
                type2SelectedNodes[i] = 0
        self.iotDeviceManager.waitForNodesToBeAvailable(2,type2SelectedNodes)
        if not self.shutdownFlag:
            self.executeTaskInterface("type2", type2SelectedNodes)
       
    def task(self,command, selectedNodes, taskType):
        '''
        test task function
        command: the command to execute the task
        selectedNodes: the selected nodes for the task, a dictionary, key is the node id, value is the allocation Ratio
                       for example {1: 0.5, 2: 0.5}
        taskType: the task type
        '''
        print(f"Task {taskType} started")
        time.sleep(0.1)  # simulate the task execution time
        print(f"Task {taskType} completed")
        self.updateDeviceStatus(taskType,selectedNodes,2) 
        returnResult = {
            "stdout": "Task completed",
            "stderr": "N/A",
            "executionTime": taskType+2
            }
        return returnResult
        
    def getTaskStatus(self, taskType):
        '''
        taskStatus: 0: not started, 1: processing, 2: completed
        '''
        return self.taskStatus[taskType]

    def updateTaskStatus(self, taskType, status):
        '''
        taskStatus: 0: not started, 1: processing, 2: completed
        '''
        self.taskStatus[taskType] = status
    
     # get the execution command
    def getExecutionCommand(self,selectedNodes, tasktypeId):
        '''
        get the execution command based on the selected nodes and the task type id
        selectedNodes: the selected nodes for the task, a dictionary, key is the node id, value is the allocation Ratio
                            for example {1: 0.5, 2: 0.5}
        tasktypeId: the id of the task type,id in the task queue 0:S, 1:W, 2:A, 3:B
        '''
        # Given configuration for IoT cluster nodes
        IoTclusterNodes = self.cfg.get('IoTclusterNodes')
        mpirunPath = self.cfg.get('mpirunPath')
        Tasks = self.cfg.get('Tasks')
        executableFile = Tasks[self.taskID].get('path')
        self.taskID += 1
        # check if the executable file exists
        if not os.path.exists(executableFile):
            mablogging.error(" %s does not exist", executableFile)
            mablogging.error(" %s does not exist", executableFile)
            # mablogging.error("The executable file does not exist")
            return
        # Mapping for device types based on selected node names
        device_type_mapping = {
            "pi": "rpi4",
            "master": "rpi4",
            "jetson": "jetson",
            "beagleboard": "beagleboard"
        }
        
        # Initialize command parts
        host_part = ""
        allocation_part = ""
        
        # Build the command based on selected nodes
        for node_id, allocation in selectedNodes.items():
            
            # Find the corresponding node in IoTclusterNodes
            node = next((item for item in IoTclusterNodes if item["id"] == node_id), None)
            if node:
                # Determine the device type for allocation part
                for device_type, type_key in device_type_mapping.items():
                    if device_type in node["name"]:
                        allocation_part += f"{type_key} {allocation} "
                        break
                if allocation == 0:
                    continue
                # Add to the host part of the command
                host_part += f"{node['name']}:{node['cpuCores']},"
        
        # Remove the trailing comma from the host part
        if host_part.endswith(","):
            host_part = host_part[:-1]
        
        # Complete command construction
        command = f"{mpirunPath} -host {host_part} {executableFile} {allocation_part}"
        if tasktypeId == 1:
            mablogging.info("Task%s command: %s", tasktypeId, command)
        return command

class IoTDeviceManager: 
    def __init__(self,cfg):
        self.cfg = cfg
        self.lock = Lock()
        self.condition = Condition(self.lock)
        # init the device status, 1 means available, 0 means busy
        self.deviceStatus = [1] * np.sum(cfg.get('devicesNumbers'))
        self.deviceClassNumber = cfg.get('devicesNumbers') # [2,4,5]
        # available device for each class 
        self.availableDeviceforEachClass = {}
        for catagory,deviceNumber in enumerate(self.deviceClassNumber):
            self.availableDeviceforEachClass[catagory] = list(range(sum(self.deviceClassNumber[0:catagory]),sum(self.deviceClassNumber[0:catagory])+deviceNumber))
        # print(f"availableDeviceforEachClass: {self.availableDeviceforEachClass}")
        

    def updateDeviceStatus(self,tasktypeId, selectedNodes,taskStatus):
        '''
        Update the device status based on the selected nodes and the task status
        selectedNodes: the selected nodes for the task, a dictionary, key is the node id, value is the allocation Ratio
                          for example {1: 0.5, 2: 0.5}
        taskStatus: 0: not started, 1: processing, 2: completed
        '''
        with self.lock:
            for node_id, allocation in selectedNodes.items():
                if taskStatus == 2:
                    if allocation > 0:
                        self.deviceStatus[node_id] = 1
                        self.condition.notify_all() 
                elif taskStatus == 1 or taskStatus == 0:
                    if allocation > 0:
                        self.deviceStatus[node_id] = 0
                        
        self.updateDeviceClassNumber(selectedNodes,taskStatus)
    
    def updateDeviceClassNumber(self,selectedNodes,taskStatus):
        '''
        Update the device class number based on the selected nodes and the task status
        selectedNodes: the selected nodes for the task, a dictionary, key is the node id, value is the allocation Ratio
                          for example {1: 0.5, 2: 0.5}
        taskStatus: 0: not started, 1: processing, 2: completed
        '''
        with self.lock:
            for node_id, allocation in selectedNodes.items():
                if taskStatus == 2:
                    if allocation > 0:
                        self.availableDeviceforEachClass[self.getDeviceType(node_id)].append(node_id)
                elif taskStatus == 1 or taskStatus == 0:
                    if allocation > 0:
                        # self.availableDeviceforEachClass[self.getDeviceType(node_id)].remove(node_id)
                        pass 
        

    def getDeviceType(self,node_id):
        '''
        get the device type based on the node id
        '''
        for i in range(len(self.deviceClassNumber)):
            if node_id < sum(self.deviceClassNumber[0:i+1]):
                return i
        return -1
    
    def getDeviceStatus(self):
        '''
        get the device status
        '''
        return self.deviceStatus
    
    def getDeviceClassNumber(self):
        '''
        get the device class number
        '''
        return self.availableDeviceforEachClass
                        
    def getAvailableNodes(self):
        '''
        Get the available nodes
        '''
        with self.lock:
            # find the indexes of the elements in the deviceStatus that are 1 
            availableNodes = [index for index, value in enumerate(self.deviceStatus) if value == 1]
            return availableNodes
                    
    def waitForNodesToBeAvailable(self,taskTypeId, selectedNodes):
        '''
        wait for the selected nodes to be available
        '''
        with self.lock:
            nodes_not_ready = True
            while nodes_not_ready:
                nodes_not_ready = False
                notAvailableNodes = []
                for node_id in selectedNodes.keys():
                    if selectedNodes[node_id] == 0: 
                        continue
                    if self.deviceStatus[node_id] == 0:
                        notAvailableNodes.append(node_id)        
                        nodes_not_ready = True
                if nodes_not_ready:
                    mablogging.warning("Task%s selected nodes:%s ,but %s are not available", taskTypeId, selectedNodes, notAvailableNodes)
                    # print(f"Selected nodes:{selectedNodes} ,but {notAvailableNodes} are not available")
                    self.condition.wait()  # wait for the nodes to be available
                else:
                    break
                
    def waitForClassDeviceToBeAvailable(self,task, DeviceClass):
        '''
        wait for the sekected class to have available devices, for example, wait for the class 1 to have available devices,if len(availableDeviceforEachClass[1]) > 0 return, else wait
        '''
        # get the device name based on the device class 0 JETSON, 1 RPI4, 2 BEAGLEBONE
        # task = /home/pi/jiangboNPB/NPB3.4.2/NPB3.4-MPI/bin/ep.S.x，just get ep.S.x
        task = task.split("/")[-1]
        DeviceName = ["JETSON", "RPI4", "BEAGLEBONE"][DeviceClass]
        with self.lock:
            nodes_not_ready = True
            while nodes_not_ready:
                nodes_not_ready = False
                if len(self.availableDeviceforEachClass[DeviceClass]) == 0:
                    nodes_not_ready = True
                    mablogging.warning("%s selected Device class:%s ,but no available devices", task, DeviceName)
                    self.condition.wait()
                else:
                    break
                
            
class MABIoTAgentTest:
    def __init__(self, cfg):
        self.cfg = cfg
        self.devicesNumbers = cfg.get('devicesNumbers')
        self.allocatedIoTNodenumEachTask = cfg.get('allocatedIoTNodenumEachTask')
        self.actions = generateDeviceAllocationRatio(self.devicesNumbers, self.allocatedIoTNodenumEachTask,11)
        self.scheduler = SchedulingSystem(cfg)
        
    def test(self,task,selectedNodes):
        '''
        run the task based on the selected nodes
        '''
        self.scheduler.schedule(task,selectedNodes)

    def createAllocationNodesFromChosenIndex(self,chosenDevicesIndex,allocatedIoTNodenumEachTask=4):
        '''
        Create the allocation nodes from the chosen Action index
        chosenDevicesIndex: the index of the chosen action
        allocatedIoTNodenumEachTask: the number of nodes allocated for each task
        
        return: the selected nodes for the task, a dictionary, key is the node id, value is the allocation Ratio
                            for example {1: 0.5, 2: 0.5}
        '''
        seletedNodes = self.actions[chosenDevicesIndex]
        # find the indexes of the elements that are 1.0
        one_indexes = [index for index, value in enumerate(seletedNodes) if value == 1.0]
        # find the indexes of the elements that are 0.0
        if one_indexes != [] :
            zero_indexes = [index for index, value in enumerate(seletedNodes) if value == 0.0]
            selected_zero_indexes = random.sample(zero_indexes, allocatedIoTNodenumEachTask-1)
             # create the allocation dictionary
            seletedNodes = {index: 1.0 for index in one_indexes}
            seletedNodes.update({index: 0.0 for index in selected_zero_indexes})
        else:
            seletedNodes =  {index: value for index, value in enumerate(seletedNodes) if value != 0}
        
        # seletedNodes 需要有4个节点，如果不足4个节点，需要补充
        taskParameter = self.cfg.get('taskParameter')
        if len(seletedNodes) < taskParameter:
            for i in range(taskParameter-len(seletedNodes)):
                # seletedNodes[i] = 0.0
                # the index of the selected nodes should be unique
                index = random.randint(0,taskParameter-1)
                while index in seletedNodes:
                    index = random.randint(0,taskParameter-1)
                seletedNodes[index] = 0.0
        return seletedNodes

class SchedulingSystem:
    def __init__(self, cfg):
        self.cfg = cfg
        self.taskManager = TaskManager(cfg, 500)
        # each device type has a unique deviceID,and it's the index of the deviceResource, for example [2,4,5], the deviceID is 0,1, for class 1, and 2,3,4,5 for class 2, and 6,7,8,9,10 for class 3,and the device ID is not changed
        # self.deviceID = self.cfg.get('devicesNumbers')
        self.deviceID = self.cfg.get('devicesNumbers')
        # the total number of IoT cluster nodes for ench device type [2,4,5]
        self.deviceResource = self.taskManager.iotDeviceManager.deviceStatus
        
    def schedule(self,task, selectedNodes):
        '''
        Schedule the task
        '''
        mablogging.debug(f"Task scheduled with selectedDevices: {selectedNodes}")
        deviceIDforThisTask = self.getDeviceIDforRunningTask(task,selectedNodes)
        mablogging.debug(f"device ID for this task: {deviceIDforThisTask}")
        mablogging.debug(f"deviceIDforThisDeviceType: {self.taskManager.iotDeviceManager.getDeviceClassNumber()}")
        # print(f"deviceIDforThisTask: {deviceIDforThisTask}")
        self.taskManager.executeTaskInterface("type1", deviceIDforThisTask)
        
        
    def getDeviceIDforRunningTask(self,task,selectedNodes):
        '''
        Get the device ID for running the task
        '''
        # print(f"selectedNodes: {selectedNodes}")
        availableDeviceforEachClass = self.taskManager.iotDeviceManager.getDeviceClassNumber()
        # print(f"availableDeviceforEachClass: {availableDeviceforEachClass}")
        # availableDeviceforEachClass: {0: [0, 1], 1: [2, 3, 4, 5], 2: [6, 7, 8, 9, 10]}
        deviceIDforThisTask = {}

        mablogging.debug(f"deviceIDforThisDeviceType: {availableDeviceforEachClass}")
        
        for node_id, allocation in selectedNodes.items():
            if allocation == 0:
                # if node_id not in deviceIDforThisTask, then set the value to 0,else 
                #   select other node
                if node_id not in deviceIDforThisTask:
                    deviceIDforThisTask[node_id] = 0
                else:
                    for i in range(sum(availableDeviceforEachClass)):
                        if i not in deviceIDforThisTask:
                            deviceIDforThisTask[i] = 0
                            break
                continue
            deviceResourceEnough = self.checkDeviceResource(node_id)
            DeviceType = self.taskManager.iotDeviceManager.getDeviceType(node_id)      
            if deviceResourceEnough:
                deviceIDforThisDeviceType = self.taskManager.iotDeviceManager.getDeviceClassNumber()[DeviceType].pop(0)
            else:
                self.taskManager.iotDeviceManager.waitForClassDeviceToBeAvailable(task, DeviceType)
                deviceIDforThisDeviceType = self.taskManager.iotDeviceManager.getDeviceClassNumber()[DeviceType].pop(0)
            
            deviceIDforThisTask[deviceIDforThisDeviceType] = allocation
        return deviceIDforThisTask
                
   
    def checkDeviceResource(self,node_id):
        '''
        Check the device resource
        '''
        deviceType = self.taskManager.iotDeviceManager.getDeviceType(node_id)
        deviceIDforThisDeviceType = self.taskManager.iotDeviceManager.getDeviceClassNumber()
        if len(deviceIDforThisDeviceType[deviceType]) > 0:
            return True
        else:
            return False
   
    def getDevicceMapping(self):
        '''
        device mapping: return the devices which is available for the task
        '''
        return self.taskManager.iotDeviceManager.getDeviceStatus()
        
# save and load the model
class SaveAndLoadModel:
    def __init__(self,cfg):
        '''
        cfg: the configuration file :config.yml
        '''
        self.cfg = cfg
        self.modelPath = self.cfg.get('modelPath')
        if not os.path.exists(self.modelPath):
            os.makedirs(self.modelPath)
            mablogging.info(f"Create the model path: {self.modelPath}")
    
    def saveModel(self, model, filename):
        '''
        Save the model
        '''
        filename = os.path.join(self.modelPath, filename)
        with open(filename, 'wb') as file:
            pickle.dump(model, file)
            
    def loadModel(self, filename):
        '''
        Load the model
        '''
        filename = os.path.join(self.modelPath, filename)
        with open(filename, 'rb') as file:
            return pickle.load(file)
  

def main():
    with open('testconfig.yml', 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    # create the log file
    setupGlobalLogger(cfg)
    saveAndLoadModel = SaveAndLoadModel(cfg=cfg)
    # create the MABIoTCluster
    mabIotAgenttest = MABIoTAgentTest(cfg)
    # load the total task 
    '''
    Tasks:
    - typeid: 0
        path: /home/pi/NPB3.4.2/NPB3.4-MPI/bin/ep.S.x
        class: EP
        size: S
    - typeid: 1 ....
    '''
    totalTestTasks = [task["path"] for task in cfg['Tasks']]
    if not totalTestTasks:
        mablogging.error(f"The total tasks are empty")
        exit()
    # create the MAB agent
    testMABAgentName = cfg.get('MABalgorithmName')
    modelpath = cfg.get('modelPath')
    # if the model exists, load the model  agent_{name}.pkl
    if os.path.exists(os.path.join(modelpath, f'agent_{testMABAgentName}.pkl')):
        mablogging.info(f"Load the MAB model from {modelpath}")
        # mabAgent = saveAndLoadModel.loadModel(f'agent_{testMABAgentName}.pkl')
        mabAgent = saveAndLoadModel.loadModel("agent_UCB1_3_2000_1_1.pkl")
    else:
        mablogging.error(f"The MAB model does not exist in {modelpath}")
        mablogging.error(f"Please train the MAB model first")
        exit()
    
    for task in totalTestTasks:
        mablogging.info(f"\n------Task: {task}-------------\n")
        deviceMapping = mabIotAgenttest.scheduler.getDevicceMapping()
        
        chosenDevicesIndex,chosenPlace = mabAgent.act(mabIotAgenttest.actions, deviceMapping)
        seletedNodes = mabIotAgenttest.createAllocationNodesFromChosenIndex(chosenDevicesIndex, mabIotAgenttest.allocatedIoTNodenumEachTask)
        # execute the task based on the selected nodes
        mabIotAgenttest.test(task,seletedNodes)
        
    # close the config file
    ymlfile.close()
    logging.shutdown()
    
if __name__ == "__main__":
    # start time 
    start = time.time()
    main()
    end = time.time()
    mablogging.info(f"Total time: {end - start}")
