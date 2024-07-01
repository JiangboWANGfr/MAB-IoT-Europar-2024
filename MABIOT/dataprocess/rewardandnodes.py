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
                if key == 'CPUTime':
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
    
    def choise_cpu(self, choice_index,choise_value, cputimedf, selectedNodes):
        totalCputime = 0 
        choise_cpu = []
        for index in range(len(choice_index)):
            totalCputime = 0
            for i in range(len(selectedNodes['selectedNodes'])):
                if selectedNodes['selectedNodes'][i] == choice_index[index]:
                    totalCputime += cputimedf['CPUTime'][i]
            averageCputime = totalCputime / choise_value[index]
            choise_cpu.append(averageCputime)
        return choise_cpu
    
    def choise_power(self, choice_index,choise_value, powerdf, selectedNodes):
        totalPower = 0
        choise_power = []
        for index in range(len(choice_index)):
            totalPower = 0
            for i in range(len(selectedNodes['selectedNodes'])):
                if selectedNodes['selectedNodes'][i] == choice_index[index]:
                    totalPower += powerdf['TotalPowerConsumption'][i]
            averagePower = totalPower / choise_value[index]
            choise_power.append(averagePower)
        return choise_power

    def choise_executiontimereward(self, choice_index,choise_value, executiontimerewarddf, selectedNodes):
        totalExecutiontimereward = 0
        choise_executiontimereward = []
        for index in range(len(choice_index)):
            totalExecutiontimereward = 0
            for i in range(len(selectedNodes['selectedNodes'])):
                if selectedNodes['selectedNodes'][i] == choice_index[index]:
                    totalExecutiontimereward += executiontimerewarddf['Executiontimereward'][i]
            averageExecutiontimereward = totalExecutiontimereward / choise_value[index]
            choise_executiontimereward.append(averageExecutiontimereward)
        return choise_executiontimereward
    
    def choise_reward(self, choice_index,choise_value, rewarddf, selectedNodes):
        totalReward = 0
        choise_reward = []
        for index in range(len(choice_index)):
            totalReward = 0
            for i in range(len(selectedNodes['selectedNodes'])):
                if selectedNodes['selectedNodes'][i] == choice_index[index]:
                    totalReward += rewarddf['reward'][i]
            averageReward = totalReward / choise_value[index]
            choise_reward.append(averageReward)
        return choise_reward
    
    # get all the choices for the selectedNodes
    def get_choices(self, data_path,cputime_path, executiontimereward_path, power_path,reward_path):
        """
        Reads the saved data file and plots the curve based on the extracted data.
        
        :param data_path: Path to the data file.
        """
        # Load the data
        selectedNodes = pd.read_csv(data_path)
        #get the name of the column
        column_name = selectedNodes.columns[1] # selectedNodes
        # {0: 0.3, 2: 0.7, 3: 0.0, 1: 0.0}" just keep 0.3 0.7
        import ast  
        selectedNodes[column_name] = selectedNodes[column_name].apply(lambda x: ast.literal_eval(x))
        selectedNodes[column_name] = selectedNodes[column_name].apply(lambda x: {k: v for k, v in x.items() if v != 0})
        # selectedNodes[column_name] = selectedNodes[column_name].apply(lambda x: {k: v for k, v in ast.literal_eval(x).items() if k in [0, 2]} if isinstance(x, str) else x)
        print(selectedNodes[column_name].value_counts())
        # # get the sum of the count of the selectedNodes
        print(selectedNodes[column_name].value_counts().sum())
        
        
        choice_index = selectedNodes[column_name].value_counts().index
        choise_value = selectedNodes[column_name].value_counts().values
        maxindex = 50
        
        # CPU time
        # choise_cpu = self.choise_cpu(choice_index,choise_value, pd.read_csv(cputime_path), selectedNodes)
        # power consumption
        # choise_power = self.choise_power(choice_index,choise_value, pd.read_csv(power_path), selectedNodes)
        #execute time
        # choise_executiontimereward = self.choise_executiontimereward(choice_index,choise_value, pd.read_csv(executiontimereward_path), selectedNodes)
        #reward
        choise_reward = self.choise_reward(choice_index,choise_value, pd.read_csv(reward_path), selectedNodes)
            
        
        showindex = 50
        # # Plotting
        plt.figure(figsize=(10,  6))
        ax1 = plt.gca()
        # df[column_name].value_counts().plot(kind='bar', color='blue', alpha=0.6, ax=ax1)
        selectedNodes[column_name].value_counts().head(showindex).plot(kind='bar', color='tab:orange', alpha=0.6, ax=ax1)
        ax1.set_ylabel('Action Counts', color='tab:orange')
        # for i, cpu_time in enumerate(choise_cpu):
            # plt.text(i, cpu_time + 0.05, f'{cpu_time}', ha='center', va='bottom', color='red')

        # # plot choise_cpu
        # ax2 = ax1.twinx()
        # ax2.plot(range(showindex), choise_cpu[:showindex], 'r-o')  # 'r-o' means red color, circle marker
        # ax2.set_ylabel('CPU Time', color='red')  # set the label of y axis
        
        # # plot choise_power
        # ax3 = ax1.twinx()
        # ax3.spines['right'].set_position(('outward', 80))
        # ax3.plot(range(showindex), choise_power[:showindex], 'g-o')
        # ax3.set_ylabel('Power Consumption Reward', color='green')
        
        # # plot choise_executiontimereward
        # ax4 = ax1.twinx()
        # ax4.spines['right'].set_position(('outward', 50))
        # ax4.plot(range(showindex), choise_executiontimereward[:showindex], 'b-o')
        # ax4.set_ylabel('Execution Time Reward', color='blue')
        
        # # plot power consumption + execution time reward
        # result = [choise_executiontimereward[i] + choise_power[i] for i in range(showindex)]
        # ax4 = ax1.twinx()
        # ax4.spines['right'].set_position(('outward', 110))
        # ax4.plot(range(showindex), result, 'c-o')
        # ax4.set_ylabel('Execution Time Reward', color='cyan')
        
        # plot choise_reward
        ax5 = ax1.twinx()
        ax5.spines['right'].set_position(('outward', 50))
        ax5.plot(range(showindex), choise_reward[:showindex], 'r-o')  #m-o means magenta color, circle marker
        ax5.set_ylabel('Reward', color='magenta')
        
        

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
filename = "2431_5000_1_1.log"
filename = "476_10000_1_1_EXP3.log"
filename = "476_2000_1_1.log"

handler.extract_and_save_data("1","./data/"+filename, ['selectedNodes', 'CPUTime', 'ExecutionTime', 'TotalPowerConsumption', 'TotalPowerConsumptionreward', 'Executiontimereward', 'reward'], "./results/")

if os.path.exists("./results/selectedNodes_data.csv") and os.path.exists("./results/selectedNodes_data.csv"):
    # getpowerParameter("./results/Executiontimereward_data.csv","./results/TotalPowerConsumptionreward_data.csv")
    handler.get_choices("./results/selectedNodes_data.csv","./results/CPUTime_data.csv","./results/Executiontimereward_data.csv","./results/TotalPowerConsumptionreward_data.csv","./results/reward_data.csv")
else:
    print("No reward data found.")
    


if os.path.exists("./results/reward_data.csv"):
    data = pd.read_csv("./results/reward_data.csv")
    data = data['reward'][0:2000]
    drawReward(0, data, 'EPX3', './results',11, 3, True)
