import subprocess
import time
import threading

class IoTDeviceManager:
    def __init__(self, device_count):
        # init the device status, 1 means available, 0 means busy
        self.deviceStatus = [1] * device_count
        # init the task queue
        self.taskQueue = []
        self.lock = threading.Lock()
    
    def addTask(self, taskId, cfg):
        # add the task to the task queue
        self.taskQueue.append((taskId, cfg))
        # try to execute the task
        self.tryExecuteTask()
    
    def tryExecuteTask(self):
        # try to execute the task in the task queue
        availableDevices = [index for index, status in enumerate(self.deviceStatus) if status == 1]
        # if there is available device and task queue is not empty , execute the task
        while availableDevices and self.taskQueue:
            selectedNode = availableDevices.pop(0)  # choose the first available device
            taskId, cfg = self.taskQueue.pop(0)  # choose the first task in the queue
            # update the device status to busy
            self.deviceStatus[selectedNode] = 0
            # Asynchronous execution of tasks. Simplified processing here. In actual applications, threads or asynchronous IO processing are required.
            self.executeTask(selectedNode, taskId, cfg)
            # update the device status to available
            self.deviceStatus[selectedNode] = 1
            #  try to execute the next task
            self.tryExecuteTask()
    
    def executeTask(self, selectedNode, taskId, cfg):
        selectedNodes = self.selectAvailableDevices(cfg['allocation'])
        if not selectedNodes:
            print("No available devices.")
            return
        # get the execution command
        command = self.getExecutionCommand(selectedNodes, taskId, cfg)
        # run the task in a new thread
        taskThread = threading.Thread(target=self.runCommand, args=(command, selectedNodes, taskId))
        taskThread.start()
        
    def runCommand(self, command, selectedNodes, taskId):
        start_time = time.time()
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        end_time = time.time()
        print(f"Task {taskId} STDOUT:\n{result.stdout}")
        executionTime = end_time - start_time
        print(f"Task {taskId} execution time: {executionTime}s")
        # 任务完成后更新设备状态
        self.updateDeviceStatus(selectedNodes)
        if result.returncode != 0:
            print(f"Task {taskId} failed with return code: {result.returncode}")
            
    def updateDeviceStatus(self, selectedNodes):
        with self.lock:
            for node_id in selectedNodes.keys():
                self.deviceStatus[node_id] = 1 # update the device status to available
        print("Device status updated: ", self.deviceStatus)

    def getExecutionCommand(self, selectedNodes, taskId, cfg):
        # generate the execution command according to the selected nodes and task configuration
        return "echo 'Hello, World!'"


if __name__ == "__main__": 
    cfg = {'allocation': 2} # task configuration, 2 devices are required
    taskManager = IoTDeviceManager(10) # 10 devices is available
    taskId = 1
    taskManager.executeTask(taskId, cfg)