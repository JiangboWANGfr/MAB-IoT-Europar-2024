import numpy as np
import yaml
def getTaskTypeId(taskType):
    '''
    get the task type id
    for type1 task, the id is 1
    for type2 task, the id randomly selected from 1 to totalTaskNum
    '''
    taskTypeIds = {
        "type1": 0,
        "type2": np.random.randint(0,2)
    }
    return taskTypeIds[taskType]

for i in range(10):
    print(getTaskTypeId("type2"))

with open("./config.yml", "r") as f:
    config = yaml.load(f)

tasks = config["Tasks"]
print(len(tasks))
print(tasks[0]["size"])