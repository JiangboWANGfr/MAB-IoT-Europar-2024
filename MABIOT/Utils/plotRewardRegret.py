import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.ticker as ticker
import matplotlib.pyplot

ddata = pd.read_csv(
    "D://ENSEA//Coursenensea//annee3//DOUBLE-DEGREE//ESI_Project_de_recherche//mabIoT//Utils//analysis_Optimal UCB.csv")

ddataUCB = ddata[["Optimal UCB", "Reward UCB"]]
ddataUCB.rename(columns={'Optimal UCB': 'Optimal 2 over 8 UCB',
                'Reward UCB': 'Reward 2 over 8 UCB'}, inplace=True)

print(ddataUCB.head())
print(ddataUCB.columns.to_list())
print(ddataUCB.shape)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # Setup logging directory if necessary
    if ddata is not None:
        columns = ddata.columns.to_list()
        print(columns)
        sns.set_theme()
        sns.set_style("whitegrid")
        sns.set_context("poster", font_scale=1.3)
        ################ Reward #############

        reward = ddata[[columns[1], columns[2]]]
        # reward = ddata[columns[2]]
        g = sns.relplot(data=reward, height=8, aspect=2.2)
        g.ax.yaxis.set_major_locator(ticker.MultipleLocator(2.5))
        g.ax.xaxis.set_major_locator(ticker.MultipleLocator(10000))

        # g.set_axis_labels("Steps","Reward")
        # g.set_ylabels("Reward",fontsize=25)
        g.set_ylabels("Reward")
        # g.set_xlabels("Steps",fontsize=25)
        g.set_xlabels("Steps")
        # g.set_xticklabels(fontsize=15)

        plt.ylim(0)
        # leg = g._legend
        # # plt.setp(leg.get_texts(), fontsize='25')
        # leg.set_bbox_to_anchor([0.75, 0.22])
        plt.show()

        ################ Regret #############
        regret = ddata[columns[4]]
        # regret.rename(columns = {'Regret UCB / T':'UCB', 'Regret EXP3 / T':'EXP3'}, inplace = True)
        # regret.drop([0,1,2])
        # g = sns.relplot(data=regret,kind="line",height=8,aspect=2.2)
        g = sns.lineplot(data=regret)
        g.set_ylabel("Regret")
        g.set_xlabel("Steps")
        plt.ylim(0)
        # plt.xlim(0)
        leg = g.legend
        # leg.set_bbox_to_anchor([0.85, 0.72])

        # plt.show()
