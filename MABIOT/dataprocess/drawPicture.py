import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os
import time
import pandas as pd
import seaborn as sns
import pandas as pd
import matplotlib.ticker as ticker
from tqdm import trange


def draw_average_reward(cumulative_rewards, algoName):
    cumulative_rewards = list(cumulative_rewards)

    print("cumulative_rewards.shape:", len(cumulative_rewards))

    average = list(
        map(lambda x: x / (cumulative_rewards.index(x) + 1),
            cumulative_rewards))
    print("average.shape:", len(average))
    plt.plot(average, label=algoName)

    plt.legend()
    plt.xlabel('Time')
    plt.ylabel('Average Reward')
    plt.title('Performance of the %s Algorithm' % algoName)
    plt.show()


def draw_cumulative_reward(cumulative_rewards, algoName):

    plt.plot(cumulative_rewards, label=algoName)

    plt.legend()
    plt.xlabel('Time')
    plt.ylabel('Cumulative Reward')
    plt.title('Performance of the %s Algorithm' % algoName)
    plt.show()


def regret(reward, rewardL):
    # for each run
    rew = np.zeros(reward.shape)
    for run in range(0, rewardL.shape[0]):
        for step in trange(0, rewardL.shape[1]):
            rew[run, step] = np.max(
                np.sum(rewardL[run][0:step]))-np.sum(reward[run][0:step])
    rew = rew.mean(axis=0)
    print(np.max(np.sum(rewardL[run][1:step])))
    return rew


def save_results(args, agent, env, rewards, actionRewards, rewardsForregret):
    if args.output_path is not None:
        # Create output directory if necessary with year-month-day-hour-minute
        dirname = args.output_path + agent.name + '/' + \
            str(time.strftime("%Y-%m-%d-%H-%M-%S")) + '/'
        os.makedirs(dirname, exist_ok=True)
        filename = agent.name + '_' + \
            str(args.steps)+'steps_'+str(args.runs) + 'runs_'

    # save devices
    device = [str(x.model) for x in env.iotdevices]
    (np.asarray(device)).tofile(dirname+filename+"devices.txt", ",")
    (np.asarray(actionRewards)).tofile(dirname+filename+"rewards.txt", ",")

    ((np.asarray(actionRewards)).mean(axis=0)).tofile(
        dirname+filename + "rewardsmean.txt", ",")

    # save optimal reward and regret
    reg = regret(actionRewards, rewardsForregret)
    opt_rew = rewardsForregret.max(axis=2).mean(axis=0)
    opt_rew.tofile(dirname+filename + "optimal.txt", ",")
    reg.tofile(dirname+filename + "regret.txt", ",")

    print("[INFO] save results to file: ", dirname+filename)


def result2csv(dirname):
    # read txt files into a pd dataframe
    fileListWithDir = os.listdir(dirname)
    # 删除非文件夹的文件
    fileListWithDir.sort(key=lambda fn: os.path.getmtime(dirname+fn))
    last_dir = fileListWithDir[-1]
    print(last_dir)
    # get the last directory's files
    fileListWithDir = os.listdir(dirname+last_dir)
    print(fileListWithDir)
    # remove devices column name
    fileListWithDir = [fileListWithDir[i] for i in range(len(fileListWithDir))
                       if 'devices' not in fileListWithDir[i]]
    print(fileListWithDir)
    # remove the folder
    ListOnlyFile = [fileListWithDir[i] for i in range(len(fileListWithDir))
                    if os.path.isfile(dirname+last_dir+'/'+fileListWithDir[i])]
    print(ListOnlyFile)
    algoName = ListOnlyFile[0].split('_')[0]

    # split the file name and extract the last element as column name
    columns = [ListOnlyFile[i].split('_')[-1].split('.')[0]
               for i in range(len(ListOnlyFile))]
    # rename the columns name with algorithm name
    columns = [algoName+columns[i] for i in range(len(columns))]
    # read files into dataframe and transpose
    df = pd.DataFrame()
    for i in range(len(ListOnlyFile)):
        df[columns[i]] = pd.read_csv(
            dirname+last_dir+'/'+ListOnlyFile[i], header=None).T
    df[algoName+"Regret"+"/T"] = df[algoName+"regret"] / \
        (df.index)-df[algoName+"regret"][1]

    # save dataframe to csv
    outputName = 'analysis_data'+str(time.strftime("%Y-%m-%d-%H-%M-%S"))+'.csv'
    df.index.name = 'step'
    outputDir = dirname+last_dir+'/analysis/'
    # create output directory if not exist
    os.makedirs(outputDir, exist_ok=True)
    df.to_csv(outputDir+outputName+'.csv', index=True)
    filename = outputDir+outputName+'.csv'
    return filename


def drawRegret(fileName):
    algoData = pd.read_csv(fileName)
    algoName = "EXP3"
    algoRegret = algoData[[algoName+"Regret/T"]]
    g = sns.lineplot(data=algoRegret)
    g.set_ylabel("Regret")
    g.set_xlabel("Steps")
    leg = g.legend
    plt.show()


def drawRewardandOptimal(fileName):
    algoData = pd.read_csv(fileName)
    algoName = "EXP3"
    rewardAndOptimal = algoData[[algoName+"optimal", algoName+"rewards"]]
    sns.set_theme()
    sns.set_style("whitegrid")
    sns.set_context("poster", font_scale=1.3)
    g = sns.relplot(data=rewardAndOptimal, height=8, aspect=2.2)
    g.ax.xaxis.set_major_locator(ticker.MultipleLocator(5000))
    g.set_xlabels("Steps")
    g.set_ylabels("Reward")
    plt.ylim(0)
    leg = g._legend
    leg.set_bbox_to_anchor([0.75, 0.22])
    plt.show()


def drawReward(index, rewards, agentName, outputfile, num_devices, num_allocated_devices, freeze=False):
    plt.figure(index)
    axes = plt.gca()
    # axes.set_ylim(0, max(rewards) + 5)
    axes.set_ylim(min(rewards) - 5, max(rewards) + 5)
    plt.plot(rewards, label='rewards c = 2')
    plt.plot(np.convolve(np.asarray(rewards), np.ones(50),
                         'valid') / 50, label="rewards moving average 20")
    plt.xlabel('Steps')
    plt.ylabel('Reward')
    plt.title(format(agentName+' Avg performance. '+str(rewards.shape[0])+' steps, '+str(
        num_devices) + ' devices, '+str(num_allocated_devices)+' devices allocated'))
    plt.tight_layout()

    if outputfile is not None:
        outputfile = outputfile + "/reward/"
        print("[INFO] save figure to file: ", outputfile)
        os.makedirs(os.path.dirname(outputfile), exist_ok=True)
        savefilename = outputfile + agentName  + "_rewards"
        plt.savefig(savefilename)

    if freeze:
        if matplotlib.is_interactive():
            plt.ioff()
        plt.show(block=True)
    else:
        plt.show(block=False)
        plt.pause(0.001)


def saveImg(output_file, filename_text):
    basename = os.path.basename(output_file)
    dirname = os.path.dirname(output_file)
    basename = basename + filename_text
    os.makedirs(dirname, exist_ok=True)
    plt.savefig(dirname+'/'+basename)


if __name__ == '__main__':
    filename = result2csv("./output/EXP3/")
    drawRewardandOptimal(filename)
    drawRegret(filename)
