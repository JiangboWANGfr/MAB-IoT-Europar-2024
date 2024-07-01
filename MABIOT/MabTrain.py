'''
file: MabTrain.py
author: Jiangbo WANG 
date: 2024-04-30
last modified: 2024-04-30
-----------------------------------
This file is used to train the MAB model for the IoT cluster
The MAB model is used to allocate the IoT cluster nodes for the tasks
'''
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


def randomPolicyFixedValues(totalIoTclusterNodesNum, allocatedIoTNodenumEachTask):
    '''
    Randomly select the allocatedIoTNodenumEachTask nodes from the totalIoTclusterNodesNum nodes
    Randomly select fixed_values for task allocation ensuring their sum is 1
    Allocate the task to the selected nodes
    totalIoTclusterNodesNum: the total number of IoT cluster nodes
    allocatedIoTNodenumEachTask: the number of nodes allocated for each task
    '''
    # Ensure the sum of the task allocations is 1
    # Define fixed values for task allocation
    fixed_values = np.arange(0, 1.1, 0.1)
    # Randomly select the allocatedIoTNodenumEachTask nodes from the totalIoTclusterNodesNum nodes
    selectedNodes = np.random.choice(range(totalIoTclusterNodesNum), allocatedIoTNodenumEachTask, replace=False)
    # Randomly select fixed_values for task allocation ensuring their sum is 1
    selectedValues = np.random.choice(fixed_values, 1, replace=False)
    selectedValues = np.append(np.round(selectedValues, 1),np.round( 1 - selectedValues, 1))
    # Allocate the task to the selected nodes
    taskAllocation = dict(zip(selectedNodes, selectedValues))
    
    return taskAllocation


class TaskManager:
    def __init__(self, cfg):
        '''
        cfg: the configuration file :config.yml
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
        self.totalTaskNum = len(cfg.get('Tasks'))
        self.taskStatus = {f"type{i}": 0 for i in range(self.totalTaskNum)}  # 0: not started, 1: processing, 2: completed   
        self.executor = ThreadPoolExecutor(max_workers=cfg.get('maxThreads'))
        self.futures = []
        self.iotDeviceManager = IoTDeviceManager(cfg)  
        self.reserveAction = generateDeviceAllocationRatio(cfg.get('totalIoTclusterNodesNum'), cfg.get('allocatedIoTNodenumForReserveTask'),11)
    
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
                # self.iotDeviceManager.updateDeviceStatus(taskType, selectedNodes,0)
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
        shreshouldTime = 20
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
                mablogging.info(f"Task{tasktypeId} STDOUT:\n{result.stdout}")
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
        for type1 task, the id is 1
        for type2 task, the id randomly selected from 1 to totalTaskNum
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
        type2SelectedNodes = random.choice(self.reserveAction)
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
        type2Selectedaction = random.choice(self.reserveAction)
        type2SelectedNodes = {}
        maxdevices = self.cfg.get('totalIoTclusterNodesNum')        
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
        if tasktypeId == 1:
            taskId = 1
        if tasktypeId == 2:
            taskId = np.random.randint(1,self.totalTaskNum+1)
        executableFile = Tasks[taskId-1].get('path')
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
        self.deviceStatus = [1] * np.sum(cfg.get('totalIoTclusterNodesNum'))
        

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
  # print(f"tasktypeId: {tasktypeId}, selectedNodes: {selectedNodes}, taskStatus: {taskStatus}, deviceStatus: {self.deviceStatus}")
                        
    def getAvailableNodes(self):
        '''
        Get the available nodes
        '''
        with self.lock:
            availableNodes = [node_id for node_id, status in enumerate(self.deviceStatus) if status == 1]
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
            
class MABIoTCluster:
    def __init__(self, cfg,taskManager):
        self.cfg = cfg
        self.totalIoTclusterNodesNum = cfg.get('totalIoTclusterNodesNum')
        self.allocatedIoTNodenumEachTask = cfg.get('allocatedIoTNodenumEachTask')
        self.runCircles = cfg.get('runCircles')
        self.steps = cfg.get('steps')
        self.rewards = np.zeros(self.steps)
        self.powerConsumptionFactor = cfg.get('powerConsumptionFactor')
        self.executionTimeFactor = cfg.get('executionTimeFactor')
        self.actions = generateDeviceAllocationRatio(self.totalIoTclusterNodesNum, self.allocatedIoTNodenumEachTask,11)
        self.taskManager = taskManager
        
    def reset(self):
        self.rewards = np.zeros(self.steps)
        
    def rewardversion1(self, selectedNodes, result):
        # get execution time and power consumption
        exercutionTime = self.getExecutionTimeFromResult(result)
        powerConsumption = self.getPowerConsumption(selectedNodes, result, self.cfg)
        # calculate the reward
        rewardExercutionTime = self.executionTimeFactor*20/(exercutionTime**1)
        # rewardPowerConsumption = self.powerConsumptionFactor *15* 1/powerConsumption
        rewardPowerConsumption = self.powerConsumptionFactor *15* 20/powerConsumption
        reward = rewardExercutionTime + rewardPowerConsumption
        # reward = 1/(exercutionTime + powerConsumption)
        mablogging.info("Execution time: %s, Power consumption(p*t): %s", round(exercutionTime, 2), round(powerConsumption, 2))
        mablogging.info("Execution time(1/t**2): %s, Power consumption(1/p): %s, Reward(t + p): %s", round(rewardExercutionTime, 2), round(rewardPowerConsumption, 2), round(reward, 2))
        return reward

    def rewardversion2(self, selectedNodes, result):
        # get execution time and power consumption
        exercutionTime = self.getExecutionTimeFromResult(result)
        powerConsumption = self.getPowerConsumption(selectedNodes, result, self.cfg)
        # calculate the reward
        rewardExercutionTime = self.executionTimeFactor * (exercutionTime**2) * 0.3
        # rewardPowerConsumption = self.powerConsumptionFactor *15* 1/powerConsumption
        rewardPowerConsumption = self.powerConsumptionFactor * powerConsumption * 0.01
        reward = 1/(rewardExercutionTime + rewardPowerConsumption)
        # reward = 1/(exercutionTime + powerConsumption)
        mablogging.info("Execution time: %s, Power consumption(p*t): %s", round(exercutionTime, 2), round(powerConsumption, 2))
        mablogging.info("Execution time(1/t**2): %s, Power consumption(1/p): %s, Reward(t + p): %s", round(rewardExercutionTime, 2), round(rewardPowerConsumption, 2), round(reward, 2))
        return reward

    def rewardversion3(self, selectedNodes, result):
        # get execution time and power consumption
        exercutionTime = self.getExecutionTimeFromResult(result)
        powerConsumption = self.getPowerConsumption(selectedNodes, result, self.cfg)
        # calculate the reward
        rewardExercutionTime = -self.executionTimeFactor*(exercutionTime)
        # rewardPowerConsumption = self.powerConsumptionFactor *15* 1/powerConsumption
        rewardPowerConsumption = -self.powerConsumptionFactor * powerConsumption
        reward = rewardExercutionTime + rewardPowerConsumption
        # reward = 1/(exercutionTime + powerConsumption)
        mablogging.info("Execution time: %s, Power consumption(p*t): %s", round(exercutionTime, 2), round(powerConsumption, 2))
        mablogging.info("Execution time(1/t**2): %s, Power consumption(1/p): %s, Reward(t + p): %s", round(rewardExercutionTime, 2), round(rewardPowerConsumption, 2), round(reward, 2))
        return reward
    
    def rewardversion4(self, selectedNodes, result):
        # get execution time and power consumption
        exercutionTime = self.getExecutionTimeFromResult(result)
        powerConsumption = self.getPowerConsumption(selectedNodes, result, self.cfg)
        # calculate the reward
        rewardExercutionTime = self.executionTimeFactor*1/(exercutionTime**2)
        # rewardPowerConsumption = self.powerConsumptionFactor *15* 1/powerConsumption
        powerConsumptionShreshold = self.cfg.get('rewardPowerConsumptionShreshold')
        powerConsumptionBeta = self.cfg.get('rewardPowerConsumptionBeta')
        powerConsumptionAlpha = self.cfg.get('rewardPowerConsumptionAlpha')
        rewardPowerConsumption = self.powerConsumptionFactor * 1/powerConsumption * powerConsumptionAlpha if powerConsumption < powerConsumptionShreshold else self.powerConsumptionFactor * 1/powerConsumption * powerConsumptionBeta
        reward = rewardExercutionTime + rewardPowerConsumption
        mablogging.info("Execution time: %s, Power consumption: %s", round(exercutionTime, 2), round(powerConsumption, 2))
        mablogging.info("Execution time(1/t**2): %s, Power consumption(1/p): %s, Reward(t + p): %s", round(rewardExercutionTime, 2), round(rewardPowerConsumption, 2), round(reward, 2))
        return reward
    
    
    def step(self, seletedNodes, step):
        '''
        seletedNodes: the selected nodes for the task, a dictionary, key is the node id, value is the allocation Ratio
                            for example {1: 0.5, 2: 0.5}
        taskType: the task type
        '''
        
        # check if the nodes are available or not
        self.taskManager.startReserveTask(seletedNodes,len(self.actions),step)
        self.taskManager.iotDeviceManager.waitForNodesToBeAvailable(1,seletedNodes)
        self.execution_time = None
        self.taskManager.executeTaskInterface("type1", seletedNodes)
        result = self.taskManager.resultqueue.get()
        self.taskManager.sotpReserveTask(step)
        while True:
            if result is not None:
                reward = self.rewardversion1(seletedNodes, result)
                # return reward
                return reward   
            else:
                continue   
    
        
    def getExecutionTimeFromResult(self,result):
        '''
        Get the execution time from the TASK result
        '''
        exercutionTimeMatch = re.search(r"CPU Time\s+=\s+([\d.]+)", result['stdout'])
        
        if exercutionTimeMatch:
            exercutionTime = float(exercutionTimeMatch.group(1)) if exercutionTimeMatch else "N/A"
        else:
            exercutionTime = result['executionTime']
            mablogging.error("Could not extract CPU time from the result")
        #print(result['executionTime'])
        return exercutionTime

    def getPowerConsumption(self,selectedNodes, result,cfg):
        '''
        Get the power consumption from the TASK result
        '''
        # get the power consumption from the result
        exercutionTime = self.getExecutionTimeFromResult(result)
        IoTclusterNodes = cfg.get('IoTclusterNodes')
        nodesPowerConsumption = {}
        powerConsumption = 0
        for node_id, allocation in selectedNodes.items():
            # Find the corresponding node in IoTclusterNodes
            node = next((item for item in IoTclusterNodes if item["id"] == node_id), None)
            if node:
                nodesPowerConsumption[node_id] = node['execAveWatt']
                if allocation > 0:
                    # powerConsumption += node['execAveWatt']
                    powerConsumption += exercutionTime * node['execAveWatt']
                    # mablogging.info("Node: %s, was allocated: %s, offical power: %3s, power consumption(cpuTime * p): %s", node_id, allocation, node['execAveWatt'], round(exercutionTime * node['execAveWatt'], 2)) 
        return powerConsumption

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
        
        # seletedNodes need 4 nodes, if the length of the seletedNodes is less than 4, we need to add the 0.0 nodes
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
    with open('config.yml', 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    # create the log file
    setupGlobalLogger(cfg)
    saveAndLoadModel = SaveAndLoadModel(cfg=cfg)
    # create the task manager
    taskManager = TaskManager(cfg)
    # create the MABIoTCluster environment
    mabIoTCluster = MABIoTCluster(cfg,taskManager)
    # create the MAB agent
    if cfg.get('MABalgorithmName') == 'UCB1':
        agent = UCB1([],[])
    if cfg.get('MABalgorithmName') == 'UCB2':
        agent = UCB2(0.1,[])
    elif cfg.get('MABalgorithmName') == 'EXP3':
        agent = EXP3(0.07,[])
    
    mablogging.info(f"Start the MAB model with {cfg.get('MABalgorithmName')} algorithm")
        
    # run the MABIoTCluster
    for i in range(mabIoTCluster.runCircles):
        agent.initialize(len(mabIoTCluster.actions))
        mablogging.info("actionSpace length: %s", len(mabIoTCluster.actions))
        for step in range(mabIoTCluster.steps):
            mablogging.info(f"\n----------------------------------Step: {step}----------------------------------------")
            # deviceMapping = [1-x for x in iotdevicemanger.deviceStatus]
            deviceMapping = taskManager.iotDeviceManager.deviceStatus
            mablogging.info(f"deviceMapping: {deviceMapping}")
            chosenDevicesIndex,chosenPlace = agent.act(mabIoTCluster.actions,deviceMapping)
            # print(f"Step: {step}, chosenDevicesIndex: {chosenDevicesIndex}, chosenPlace: {chosenPlace}")
            # chosenDevicesIndex = chosenDevicesIndex + 7200
            seletedNodes = mabIoTCluster.createAllocationNodesFromChosenIndex(chosenDevicesIndex, mabIoTCluster.allocatedIoTNodenumEachTask)
            reward = mabIoTCluster.step(seletedNodes, step)
            mablogging.info(f"Receive reward: {reward}")
            mabIoTCluster.rewards[step] = reward
            agent.update(chosenDevicesIndex, reward)
    
    # save agent model
    name = cfg.get('MABalgorithmName')
    allocatedIotNodenumEachTask = cfg.get('allocatedIoTNodenumEachTask')
    steps = cfg.get('steps')
    powerConsumptionFactor = cfg.get('powerConsumptionFactor')
    executionTimeFactor = cfg.get('executionTimeFactor')
    
    saveAndLoadModel.saveModel(agent, f'agent_{name}_{allocatedIotNodenumEachTask}_{steps}_{powerConsumptionFactor}_{executionTimeFactor}.pkl')
    mablogging.info('MAB model saved successfully: %s', f'agent_{name}.pkl')
    # close the config file
    ymlfile.close()
    logging.shutdown()
    
def main1():
    algoName = ['UCB1','UCB2','EXP3']
    
    for name in algoName:
        with open('config.yml', 'r') as ymlfile:
            cfg = yaml.safe_load(ymlfile)
        # create the log file
        setupGlobalLogger(cfg)
        saveAndLoadModel = SaveAndLoadModel(cfg=cfg)
        mablogging.info(f"Start the MAB model with {name} algorithm")
        mablogging.info('MAB model start')
        # create the task manager
        taskManager = TaskManager(cfg, cfg.get("steps"))
        # create the MABIoTCluster
        mabIoTCluster = MABIoTCluster(cfg,taskManager)
        # create the MAB agent
        if cfg.get('MABalgorithmName') == 'UCB1':
            agent = UCB1([],[])
        if cfg.get('MABalgorithmName') == 'UCB2':
            agent = UCB2(0.1,[])
        elif cfg.get('MABalgorithmName') == 'EXP3':
            agent = EXP3(0.07,[])
            
        # run the MABIoTCluster
        for i in range(mabIoTCluster.runCircles):
            agent.initialize(len(mabIoTCluster.actions))
            mablogging.info("actionSpace length: %s", len(mabIoTCluster.actions))
            for step in range(mabIoTCluster.steps):
                mablogging.info(f"Step: {step}")
                # deviceMapping = [1-x for x in iotdevicemanger.deviceStatus]
                deviceMapping = taskManager.iotDeviceManager.deviceStatus
                mablogging.info(f"deviceMapping: {deviceMapping}")
                chosenDevicesIndex,chosenPlace = agent.act(mabIoTCluster,deviceMapping)
                # print(f"Step: {step}, chosenDevicesIndex: {chosenDevicesIndex}, chosenPlace: {chosenPlace}")
                # chosenDevicesIndex = 11*step+1
                
                seletedNodes = mabIoTCluster.createAllocationNodesFromChosenIndex(chosenDevicesIndex, mabIoTCluster.allocatedIoTNodenumEachTask)
                print(f"seletedNodes: ",seletedNodes)
                reward = mabIoTCluster.step(seletedNodes, step)
                mablogging.info(f"Receive reward: {reward}")
                mabIoTCluster.rewards[step] = reward
                agent.update(chosenDevicesIndex, reward)
                
        
        # save agent model
        saveAndLoadModel.saveModel(agent, f'agent_{name}.pkl')
        mablogging.info('MAB model saved successfully: %s', f'agent_{name}.pkl')
        # close the config file
        ymlfile.close()
        logging.shutdown()

    
if __name__ == "__main__":
    # start time 
    start = time.time()
    main()
    end = time.time()
    mablogging.info(f"Total time: {end - start}")