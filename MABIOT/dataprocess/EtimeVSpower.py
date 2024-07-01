import re
import os   
from ast import literal_eval
from drawPicture import drawReward
import numpy as np
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
    
    def plotTimeVSpower(self, timepath,powerpath):
        """
        Reads the saved data file and plots the curve based on the extracted data.
        
        :param data_path: Path to the data file.
        """
        # Load the data
        time = pd.read_csv(timepath)
        power = pd.read_csv(powerpath)
     
        #get the name of the column
        column_name_time = time.columns[1]
        column_name_power = power.columns[1]

        # if time1<2 time1= time1 *3
        startdata = 0000
        datasize = 1000
        enddata = startdata + datasize
        time1 = time[column_name_time][startdata:enddata]
        power1 = power[column_name_power][startdata:enddata]
        alpha = 7
        beta = 6.5
        shreshould = 6
        # power1 = np.array([x*alpha if x<shreshould else x*beta for x in power[column_name_power][startdata:enddata]])
        # Plotting
        plt.figure(figsize=(10, 6))
        # if time<2 time= time *3 
        plt.plot(time.index[startdata:enddata], time1, label=column_name_time, marker='o')
        plt.plot(power.index[startdata:enddata], power1, label=column_name_power, marker='^')
        plt.xlabel('Task Index')
        plt.ylabel('Time (seconds)')
        plt.title('Task Performance Analysis with alpha={},beta={},shreshould={}'.format(alpha,beta,shreshould))
        plt.legend()
        plt.grid(True)
        plt.show()
        savePath = timepath.split("_data.csv")[0] + ".png"
        plt.savefig(savePath)
        
        print(f"[Plot] Plot saved to {savePath}")


def getpowerParameter(timepath,powerpath):
    """
    Reads the saved data file and plots the curve based on the extracted data.
    
    :param data_path: Path to the data file.
    """
    # Load the data
    time = pd.read_csv(timepath)
    power = pd.read_csv(powerpath)
 
    #get the name of the column
    column_name_time = time.columns[1]
    column_name_power = power.columns[1]
    
    #beta is from 0 to 100,step is 0.1
    betas = [x*0.1 for x in range(0,100)]
    alphas = [x*0.1 for x in range(0,100)]
    # minsum = max int 
    minsum = 100000000
    minbeta = 0
    minalpha = 0
    minshrerould = 0
    for beta in betas:
        for alpha in alphas:
            for shrerould in range(1,10):
            # 阈值 1-5
                time1 = np.array(time[column_name_time])
                power1 = np.array([x*beta if x<shrerould else x*alpha for x in power[column_name_power]])
                # get the sum of the power1 * time1
                time1_power1_sum = abs(time1 - power1)
                sum1 = np.sum(time1_power1_sum**2)
                if sum1 < minsum:
                    minsum = sum1
                    minbeta = beta
                    minalpha = alpha
                    minshrerould = shrerould
         
            print("beta:",round(beta,2),"sum:",sum1,"minbeta:",minbeta,"minalpha:",minalpha,"minshrerould:",minshrerould)
    print("minbeta:",minbeta,"minalpha:",minalpha,"shrerould:",shrerould)

handler = LogDataHandler()
# handler.extract_and_save_data("1","./data/agent_2024-03-11_10-38.log",['selectedNodes', 'CPUTime', 'ExecutionTime', 'TotalPowerConsumptionreward', 'Executiontimereward', 'reward'],"./results/")

if os.path.exists("./results/Executiontimereward_data.csv") and os.path.exists("./results/TotalPowerConsumptionreward_data.csv"):
    # getpowerParameter("./results/Executiontimereward_data.csv","./results/TotalPowerConsumptionreward_data.csv")
    handler.plotTimeVSpower("./results/Executiontimereward_data.csv","./results/TotalPowerConsumptionreward_data.csv")
else:
    print("No reward data found.")
    

# if os.path.exists("./results/reward_data.csv"):
#     data = pd.read_csv("./results/reward_data.csv")
#     data = data['reward']
#     drawReward(0, data, 'UCB1', './results',6, 2, True)
