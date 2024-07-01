"""
Example: python results2csv.py -l ../Tests/20230403/reward2_UCB_1000steps_2optimal.txt ../Tests/20230403_2/reward2_UCB_1000steps_2rewards.txt 
../Tests/20230403_2/reward2_UCB_1000steps_2regret.txt  --column_names "Optimal UCB" "Reward UCB" "Regret UCB"

For the number or words on each csv file, see https://stackoverflow.com/questions/22512333/unix-command-to-get-the-count-of-lines-in-a-csv-file

"""

import argparse
import pandas as pd
import sys
import time

def readcsv(file_list):
    hd = None
    # if args.column_names is not None:
    #     hd = args.column_names

    return pd.read_csv(file_list, header=hd)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l','--file_list', help='<Required> List of files to parse in reading order', default=[], nargs='+', required=True)
    parser.add_argument('--column_names', default=[], nargs='+') #  list of files to parse
    parser.add_argument('--output_file', default=None)
    args = parser.parse_args()

    # Setup logging directory if necessary
    if args.file_list is not None:
        df = pd.concat(map(readcsv, args.file_list)).T
        if args.column_names is not None:
            df.columns = args.column_names
            df.index.name = "T"
        
        df["Regret UCB / T"] = df[args.column_names[2]]/df.index
        print(df)
        df = df.iloc[0:10000]
        df.to_csv("analysis_"+args.column_names[0]+".csv")


        

