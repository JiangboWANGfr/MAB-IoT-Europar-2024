import re
import os   
from ast import literal_eval
from drawPicture import drawReward
import pandas as pd
import matplotlib.pyplot as plt

class LogDataHandler:
    def extract_and_save_data(self, task_type, log_path, match_data, save_path):
        """
        Extracts specified data from a log file and saves it to a CSV file.
        
        :param task_type: The type of task to filter data.
        :param log_path: Path to the log file.
        :param match_data: List of data types to match (e.g., ['selectedNodes', 'CPUTime', 'ExecutionTime']).
        :param save_path: Path to save the extracted data.
        """
        # Read log file
        #check if the file exists
        if not os.path.exists(log_path):
            print("Error: Log file does not exist.go to the correct path(dataprocess)")
            exit()
        with open(log_path, 'r') as file:
            log_content = file.read()
        if not log_content:
            print("Error: Log file is empty.")
            return
        
        # Initialize a dictionary to hold extracted data
        data = {key: [] for key in match_data}
        # Define patterns based on match_data
        patterns = {
            'selectedNodes': r"Task" + re.escape(task_type) + r" started,with selectedNodes: (\{.*?\})",
            'CPUTime': r"CPU Time\s+=\s+([\d\.]+)",
            'ExecutionTime': r"Task" + re.escape(task_type) + r" task completed, execution time:\s+([\d\.]+)",
            'TotalPowerConsumption': r"Total PowerConsumption:\s*([\d\.]+)", #
            'TotalPowerConsumptionreward': r"Power consumption\(1\/p\):\s*([\d\.]+)", 
            'Executiontimereward': r"Execution time\(1\/t\*\*2\):\s*([\d\.]+)",
            'reward': r"Reward\(t \+ p\):\s*([\d\.]+)",
            'cputimeerror': r"Task 1 failed with return code: " 
            }
        # Extract data
        for key in match_data:
            if key in patterns:
                save_path_key = save_path + key + "_data.csv"
                # if save file exists, remove it
                if os.path.exists(save_path_key):
                    os.remove(save_path_key)
                # CPU time is a special case
                if key == 'cputimeerror':
                    break
                if key == 'CPUTime':  # now it is not used
                    timeout_indices = [m.start() for m in re.finditer(patterns['cputimeerror'], log_content)]
                    matches = re.finditer(patterns[key], log_content)
                    cputime_values = []
                    for match in matches:
                        remove_index = []
                        for index in timeout_indices:
                            if match.start() > index:
                                print("match.start(){},timeout_indices[0:5]{}".format(match.start(),timeout_indices[0:5]))
                                cputime_values.append(20)
                                remove_index.append(index)
                        for index in remove_index:
                            timeout_indices.remove(index)                                
                                
                        # if timeout_indices and match.start() > timeout_indices[0]:
                        #     # if the CPUTime is after the first timeout, set it to 20, then delete this timeout index
                        #     cputime_values.append(20)
                        #     timeout_indices.pop(0)
                        cputime_values.append(float(match.group(1)))
                    data[key].extend(cputime_values)
                
                else:
                    matches = re.findall(patterns[key], log_content)
                    data[key].extend(matches)
            
                # Create csv file
                # check if the directory exist
                if os.path.exists(save_path_key):
                    os.remove(save_path_key)
                if not os.path.exists(os.path.dirname(save_path_key)):
                    os.makedirs(os.path.dirname(save_path_key))    
                if not data[key]:
                    print(f"No data found for {key}.")
                    continue
                # Convert the data to DataFrame and save as CSV
                df = pd.DataFrame(data[key])
                df.to_csv(save_path_key, index=True, index_label='taskIndex', header=[key])
                print(f"[Extract] {key} data saved to {save_path_key}")
                

    def plot_data(self, data_path):
        """
        Reads the saved data file and plots the curve based on the extracted data.
        
        :param data_path: Path to the data file.
        """
        # Load the data
        df = pd.read_csv(data_path)
        #get the name of the column
        column_name = df.columns[1]
        # Plotting
        plt.figure(figsize=(10, 6))
        plt.plot(df.index[0:500], df[column_name][0:500], label=column_name, marker='o')
        plt.xlabel('Task Index')
        plt.ylabel('Time (seconds)')
        plt.title('Task Performance Analysis')
        plt.legend()
        plt.grid(True)
        # plt.show()
        savePath = data_path.split("_data.csv")[0] + ".png"
        plt.savefig(savePath)
        print(f"[Plot] Plot saved to {savePath}")

    def plot_bar(self, data_path):
        """
        Reads the saved data file and plots the curve based on the extracted data.
        
        :param data_path: Path to the data file.
        """
        # Load the data
        df = pd.read_csv(data_path)
        #get the name of the column
        column_name = df.columns[1]
        # Plotting
        plt.figure(figsize=(10, 6))
        bins = 20
        df[column_name].plot(kind='hist', bins=bins, rwidth=0.8)
        plt.title('{} Distribution in {} bins'.format(column_name, bins))
        plt.xlabel(column_name)
        plt.ylabel('Frequency')
        plt.grid(axis='y', alpha=0.75)  

        # plt.show()
        savePath = data_path.split("_data.csv")[0] + ".png"
        plt.savefig(savePath)
        print(f"[Plot] Plot saved to {savePath}")
        
    # get all the choices for the selectedNodes
    def get_choices(self, data_path,cputime_path, reward_path, power_path):
        """
        Reads the saved data file and plots the curve based on the extracted data.
        
        :param data_path: Path to the data file.
        """
        # Load the data
        df = pd.read_csv(data_path)
        #get the name of the column
        column_name = df.columns[1] # selectedNodes
        # {0: 0.3, 2: 0.7, 3: 0.0, 1: 0.0}" just keep 0.3 0.7
        import ast  # 引入 ast 模块用于将字符串解析为字典
        df[column_name] = df[column_name].apply(lambda x: ast.literal_eval(x))
        df[column_name] = df[column_name].apply(lambda x: {k: v for k, v in x.items() if v != 0})
        # df[column_name] = df[column_name].apply(lambda x: {k: v for k, v in ast.literal_eval(x).items() if k in [0, 2]} if isinstance(x, str) else x)
        print(df[column_name].value_counts())
        # # get the sum of the count of the selectedNodes
        print(df[column_name].value_counts().sum())
        
        # CPU time
        cputimedf = pd.read_csv(cputime_path)
        cputime_column_name = cputimedf.columns[1]
        totalCputime = 0 
        maxindex = 10
        # 求相同selectedNodes的cputime的和
        choice_index = df[column_name].value_counts().index
        choise_value = df[column_name].value_counts().values
        choise_cpu = []
        print(len(choice_index))
        for index in range(len(choice_index)):
            totalCputime = 0
            for i in range(len(df[column_name])):
                if df[column_name][i] == choice_index[index]:
                    totalCputime += cputimedf[cputime_column_name][i]
                    # if selectedNodes is {0:1.0} then print the cputime
                    # if choice_index[index] == {0:1.0}:
                        # print(cputimedf[cputime_column_name][i],end=" ")
            # averageCputime = totalCputime / choise_value[index]
            averageCputime = round(totalCputime / choise_value[index], 3)
            if index < maxindex:
                print(f"index: {index} selectedNodes: {choice_index[index]} has {choise_value[index]} times, and the average cputime is {averageCputime}")
            choise_cpu.append(averageCputime)
            # totalCputime += cputimedf[cputime_column_name][index]            
        # power consumption
        powerdf = pd.read_csv(power_path)
        power_column_name = powerdf.columns[1]
        totalPower = 0
        choise_power = []
        for index in range(len(choice_index)):
            totalPower = 0
            for i in range(len(df[column_name])):
                if df[column_name][i] == choice_index[index]:
                    totalPower += powerdf[power_column_name][i]
            # averagePower = totalPower / choise_value[index]
            averagePower = round(totalPower / choise_value[index], 3)
            if index < maxindex:
                print(f"index: {index} selectedNodes: {choice_index[index]} has {choise_value[index]} times, and the average power is {averagePower}")
            choise_power.append(averagePower)
        
        #execute time
        executiontimerewarddf = pd.read_csv(reward_path)
        executiontimereward_column_name = executiontimerewarddf.columns[1]
        totalExecutiontimereward = 0
        choise_executiontimereward = []
        for index in range(len(choice_index)):
            totalExecutiontimereward = 0
            for i in range(len(df[column_name])):
                if df[column_name][i] == choice_index[index]:
                    totalExecutiontimereward += executiontimerewarddf[executiontimereward_column_name][i]
            # averageExecutiontimereward = totalExecutiontimereward / choise_value[index]
            averageExecutiontimereward = round(totalExecutiontimereward / choise_value[index], 3)
            if index < maxindex:
                print(f"index: {index} selectedNodes: {choice_index[index]} has {choise_value[index]} times, and the average Reward is {averageExecutiontimereward}")
            choise_executiontimereward.append(averageExecutiontimereward)
        #reward
        
        
        
        showindex = 20
        # # Plotting
        plt.figure(figsize=(10,  6))
        ax1 = plt.gca()
        # df[column_name].value_counts().plot(kind='bar', color='blue', alpha=0.6, ax=ax1)
        df[column_name].value_counts().head(showindex).plot(kind='bar', color='tab:orange', alpha=0.6, ax=ax1)
        ax1.set_ylabel('Action Counts', color='tab:orange')
        # for i, cpu_time in enumerate(choise_cpu):
            # plt.text(i, cpu_time + 0.05, f'{cpu_time}', ha='center', va='bottom', color='red')

        # plot choise_cpu
        ax2 = ax1.twinx()
        ax2.plot(range(showindex), choise_cpu[:showindex], 'r-o')  # 'r-o' means red color, circle marker
        ax2.set_ylabel('CPU Time', color='red')  # set the label of y axis
        
        # plot choise_power
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 80))
        ax3.plot(range(showindex), choise_power[:showindex], 'g-o')
        ax3.set_ylabel('Power Consumption Reward', color='green')
        
        # plot choise_executiontimereward
        ax4 = ax1.twinx()
        ax4.spines['right'].set_position(('outward', 50))
        ax4.plot(range(showindex), choise_executiontimereward[:showindex], 'b-o')
        ax4.set_ylabel('Execution Time Reward', color='blue')
        

        plt.tight_layout(h_pad=7)
        plt.title('Selected Nodes Distribution')
        plt.xlabel('Selected Nodes')
        # plt.ylabel('Frequency')
        plt.grid(axis='y', alpha=0.75)  

        plt.show()
        savePath = data_path.split("_data.csv")[0] + ".png"
        plt.savefig(savePath)
        print(f"[Plot] Plot saved to {savePath}")

handler = LogDataHandler()
# filename = "476_2000_1_1.log"
# filename = "2431_5000_1_1.log"
# filename = "476_10000_1_1_EXP3.log"
# filename = "agent_2024-05-05_00-22.log"
# filename = "agent_2024-05-02_11-41.log"
filename = "agent_2024-05-10_00-51.log"
filename = "agent_2024-05-17_08-59.log"
filename = "agent_2024-05-17_23-462.log"
# filename = "agent_2024-05-17_11-52.log"
filename = "agent_2024-05-18_21-14.log"
filename = "agent_2024-05-10_15-332.log"
filename = "agent_2024-05-18_09-35.log"
filename = "zzztest2.log"


handler.extract_and_save_data("1","./data/"+filename, ['selectedNodes', 'CPUTime', 'ExecutionTime', 'TotalPowerConsumption', 'TotalPowerConsumptionreward', 'Executiontimereward', 'reward'], "./results/")

if os.path.exists("./results/selectedNodes_data.csv") and os.path.exists("./results/selectedNodes_data.csv"):
    # getpowerParameter("./results/Executiontimereward_data.csv","./results/TotalPowerConsumptionreward_data.csv")
    handler.get_choices("./results/selectedNodes_data.csv","./results/CPUTime_data.csv","./results/Executiontimereward_data.csv","./results/TotalPowerConsumptionreward_data.csv")
else:
    print("No reward data found.")
    

if os.path.exists("./results/reward_data.csv"):
    data = pd.read_csv("./results/reward_data.csv")
    data = data['reward']
    print(data[0:10])
    drawReward(0, data, 'EXP3', './results',11, 3, True)
