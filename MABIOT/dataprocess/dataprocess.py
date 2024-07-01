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
            return
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
            'reward': r"Reward\(t \+ p\):\s*([\d\.]+)"
            }
        print(patterns)
        
        # Extract data
        for key in match_data:
            if key in patterns:
                save_path_key = save_path + key + "_data.csv"
                matches = re.findall(patterns[key], log_content)
                if key == 'selectedNodes':  # Convert string representation of dict to dict
                    pass
                    #matches = [eval(match) for match in matches]
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
        
handler = LogDataHandler()
handler.extract_and_save_data("1","./data/agent_2024-03-14_08-53.log",['selectedNodes', 'CPUTime', 'ExecutionTime', 'TotalPowerConsumptionreward', 'Executiontimereward', 'reward'],"./results/")

# if os.path.exists("./results/reward_data.csv"):
#     handler.plot_bar("./results/reward_data.csv")
# else:
#     print("No reward data found.")
    
# if os.path.exists("./results/CPUTime_data.csv"):
#     handler.plot_bar("./results/CPUTime_data.csv")
# else:
#     print("No CPUTime data found.")
    
# if os.path.exists("./results/ExecutionTime_data.csv"):
#     handler.plot_data("./results/ExecutionTime_data.csv")
# else:
#     print("No ExecutionTime data found.")
    
# if os.path.exists("./results/TotalPowerConsumptionreward_data.csv"):
#     handler.plot_bar("./results/TotalPowerConsumptionreward_data.csv")
# else:
#     print("No TotalPowerConsumption data found.")

# if os.path.exists("./results/Executiontimereward_data.csv"):
#     handler.plot_bar("./results/Executiontimereward_data.csv")
# else:
#     print("No Executiontime data found.")


if os.path.exists("./results/reward_data.csv"):
    data = pd.read_csv("./results/reward_data.csv")
    data = data['reward']
    drawReward(0, data, 'UCB1', './results',6, 2, True)
