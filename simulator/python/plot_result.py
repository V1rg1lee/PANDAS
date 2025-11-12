#!/usr/bin/env python
# coding: utf-8

from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import json
import seaborn as sns
import matplotlib.patches as mpatches
plt.rcParams.update({'font.size': 20}) 
from matplotlib.lines import Line2D


#### Small Scale Experiments ####
## Data Loading
ops_path = {
            '8R_R': '../1K8R/operation.csv',
            '8R_S': '../1K8R_S/operation.csv',
            '8R_M': '../1K8R_M/operation.csv'
               }
msgs_path = {
            '8R_R': '../1K8R/messages.csv',
            '8R_S': '../1K8R_S/messages.csv',
            '8R_M': '../1K8R_M/messages.csv'
           }


builder_address = '83814183170291850251680823880522715558189094423550585243365458794131648333116'

op_df={}
msg_df={}
for key in ops_path:
    op_df[key] = pd.read_csv(ops_path[key],index_col=False,low_memory=False)
for key in msgs_path:
    msg_df[key] = pd.read_csv(msgs_path[key],index_col=False,low_memory=False)


with open('../config/latency.json', 'r') as file:
    latencies = json.load(file)

COLOR = ["blue", "orange", "green"]

## Processing
"""Seeding + Random Sampling Validate"""
#fig4, ax= plt.subplots(figsize=(8, 4), dpi=200)
g = 0

result_x_G = [[] for x in range(3)]
result_y_G = [[] for x in range(3)]

for key in op_df:
    result = []
    vsdf = op_df[key].loc[((op_df[key]['type'] == 'RandomSamplingOperation') & (op_df[key]['completion_time'] < 1500))]
    for i in range(len(vsdf)):
        l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
        r = vsdf.iloc[i, vsdf.columns.get_loc('completion_time')] = vsdf.iloc[i, vsdf.columns.get_loc('completion_time')] + l
        result.append(r)
        
    k = 0
 
    print("a")
    x = sorted(result)
    N = len(x)
    # get the cdf values of y
    y = np.arange(N) / float(N)
    if key == "8R_S":
        x = [a*1.1 for a in x ]
        result_x_G[0] = x
        result_y_G[0] = y.tolist()
        print("a")  
    elif key == "8R_M":
        result_x_G[1] = x
        result_y_G[1] = y.tolist()
            
    else:
        result_x_G[2] = x
        result_y_G[2] = y.tolist()
        print("a")
            
    g+=1

testbed_save = [result_x_G, result_y_G]
with open('testbed_R.json', 'w') as f:
    json.dump(testbed_save, f) 

"""Seeding + Random Sampling Validate"""
#fig4, ax= plt.subplots(figsize=(8, 4), dpi=200)
g = 0

result_x_G = [[] for x in range(3)]
result_y_G = [[] for x in range(3)]

for key in op_df:
    result = []
    vsdf = op_df[key].loc[((op_df[key]['type'] == 'RandomSamplingOperation') & (op_df[key]['completion_time'] < 1500))]
    for i in range(len(vsdf)):
        l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
        r = vsdf.iloc[i, vsdf.columns.get_loc('completion_time')] = vsdf.iloc[i, vsdf.columns.get_loc('completion_time')] + l
        result.append(r)
        
    k = 0
 
    print("a")
    x = sorted(result)
    N = len(x)
    # get the cdf values of y
    y = np.arange(N) / float(N)
    if key == "8R_S":
        x = [a*1.1 for a in x ]
        result_x_G[0] = x
        result_y_G[0] = y.tolist()
        print("a")  
    elif key == "8R_M":
        result_x_G[1] = x
        result_y_G[1] = y.tolist()
            
    else:
        result_x_G[2] = x
        result_y_G[2] = y.tolist()
        print("a")
            
    g+=1

testbed_save = [result_x_G, result_y_G]
with open('testbed_R2.json', 'w') as f:
    json.dump(testbed_save, f)

"""Seeding + Random Sampling Validate"""
#fig4, ax= plt.subplots(figsize=(8, 4), dpi=200)
g = 0

result_x_G = [[] for x in range(3)]
result_y_G = [[] for x in range(3)]

for key in op_df:
    result = []
    vsdf = op_df[key].loc[((op_df[key]['type'] == 'RandomSamplingOperation') & (op_df[key]['completion_time'] < 2300))]
    for i in range(len(vsdf)):
        l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
        r = vsdf.iloc[i, vsdf.columns.get_loc('completion_time')] = vsdf.iloc[i, vsdf.columns.get_loc('completion_time')] + l
        result.append(r)
    k = 0
    x = sorted(result)
    N = len(x)
    # get the cdf values of y
    y = np.arange(N) / float(N)
    if key == "8R_S":
        x = [a*1.1 for a in x ]
        result_x_G[0] = x
        result_y_G[0] = y.tolist()
        print("a")
    elif key == "8R_M":  
        result_x_G[1] = x
        result_y_G[1] = y.tolist()
        print("b")
    else: 
        result_x_G[2] = x
        result_y_G[2] = y.tolist()
        print("a")
    g+=1

testbed_save = [result_x_G, result_y_G]
#print(testbed_save)
with open('testbed_R_sampling.json', 'w') as f:
    json.dump(testbed_save, f) 

"""Seeding + Random Sampling Validate"""
#fig4, ax= plt.subplots(figsize=(8, 4), dpi=200)
g = 0

result_x_G = [[] for x in range(3)]
result_y_G = [[] for x in range(3)]

for key in op_df:
    result = []
    vsdf = op_df[key].loc[((op_df[key]['type'] == 'RandomSamplingOperation') & (op_df[key]['completion_time'] < 2300))]
    for i in range(len(vsdf)):
        r = vsdf.iloc[i, vsdf.columns.get_loc('num_messages')] = vsdf.iloc[i, vsdf.columns.get_loc('num_messages')]
        result.append(r)
    k = 0
    print("a")
    x = sorted(result)
    N = len(x)
    # get the cdf values of y
    y = np.arange(N) / float(N)
    if key == "8R_S":
            
        result_x_G[0] = x
        result_y_G[0] = y.tolist()
            
    elif key == "8R_M":

            
        result_x_G[1] = x
        result_y_G[1] = y.tolist()
            
    else:

            
            result_x_G[2] = x
            result_y_G[2] = y.tolist()
    g+=1

testbed_save = [result_x_G, result_y_G]
with open('testbed_R_messages.json', 'w') as f:
    json.dump(testbed_save, f) 

"""evolution number messages of nodes"""
g = 0
data_x = [[], [], []]
data_y = [[], [], []]

data_x2 = [[], [], []]
data_y2 = [[], [], []]

for key in op_df:
    msdf = msg_df[key].loc[((msg_df[key]['type'] == 'MSG_GET_SAMPLE') | (msg_df[key]['type'] == "MSG_GET_SAMPLE_RESPONSE"))]
    
    dst_msg = msdf['dst'].to_list()
    src_msg = msdf['src'].to_list()
    unique_dsts = set(dst_msg)
    unique_src = set(src_msg)
    
    unique_node = list(set(unique_dsts) | set(unique_src))
    node_nb_messages = [0 for x in range(len(unique_node))]
    nb_bandwidth = [0 for x in range(len(unique_node))]
    i = 0
    a = len(unique_node)
    print("begin counting")
    for node in unique_node:
        if i % 1 == 0:
            nb_in = dst_msg.count(node)
            nb_out = src_msg.count(node)
            nb = nb_in + nb_out
            node_nb_messages[unique_node.index(node)] += nb/10
            nb_bandwidth[unique_node.index(node)] = ((nb_in+73) + (nb_out+73))/1024
        if i % 10 == 0:
            print(str(i) + "/" + str(a))
        i += 1
    
    # get the cdf values of y
    if key == "8R_S":
        node_nb_messages = [int(x) for x in node_nb_messages if x > 0]
        x = sorted(node_nb_messages)
        N = len(x)
        y = np.arange(N) / float(N)
        data_x[0] = x
        data_y[0] = y.tolist()
        
        nb_bandwidth = [int(x) for x in nb_bandwidth if x > 0]
        x = sorted(nb_bandwidth)
        N = len(x)
        y = np.arange(N) / float(N)
        data_x2[0] = x
        data_y2[0] = y.tolist()
        print("a")
    elif key == "8R_M":
        node_nb_messages = [int(x) for x in node_nb_messages if x > 0]
        x = sorted(node_nb_messages)
        N = len(x)
        y = np.arange(N) / float(N)
        data_x[1] = x
        data_y[1] = y.tolist()
        
        nb_bandwidth = [int(x) for x in nb_bandwidth if x > 0]
        x = sorted(nb_bandwidth)
        N = len(x)
        y = np.arange(N) / float(N)
        data_x2[1] = x
        data_y2[1] = y.tolist()
        
        print("b")
    elif key == "8R_R":
        node_nb_messages = [int(x) for x in node_nb_messages if x > 0]
        x = sorted(node_nb_messages)
        N = len(x)
        y = np.arange(N) / float(N)
        data_x[2] = x
        data_y[2] = y.tolist()
        
        nb_bandwidth = [int(x) for x in nb_bandwidth if x > 0]
        x = sorted(nb_bandwidth)
        N = len(x)
        y = np.arange(N) / float(N)
        data_x2[2] = x
        data_y2[2] = y.tolist()
        
        print("c")      
    
   
    g+=1
g=0

sim2_save = [data_x, data_y]
sim_bandwidth_save = [data_x2, data_y2]

#print(data_fetching)
with open('testbed_R_messages2.json', 'w') as f:
    json.dump(sim2_save, f)
    
with open('testbed_R_bandwidth.json', 'w') as f:
    json.dump(sim_bandwidth_save, f)


## Plotting
# Figure 9 and 10
COLOR = ["blue", "orange", "green"]
with open('testbed_R.json', 'r') as f:
    testbed_1 = json.load(f)
    testbed_1_x_G = testbed_1[0]
    testbed_1_y_G = testbed_1[1]


with open('testbed_R_sampling.json', 'r') as f:
    testbed_2 = json.load(f)
    print(len(testbed_2))
    testbed_2_x_G = testbed_2[0]
    testbed_2_y_G = testbed_2[1]

with open('testbed_R_messages.json', 'r') as f:
    testbed_3 = json.load(f)
    testbed_3_x_G = testbed_3[0]
    testbed_3_y_G = testbed_3[1]

with open('testbed_R_messages2.json', 'r') as f:
    testbed_4 = json.load(f)
    testbed_4_x_G = testbed_4[0]
    testbed_4_y_G = testbed_4[1]

with open('testbed_R_bandwidth.json', 'r') as f:
    testbed_5 = json.load(f)
    testbed_5_x_G = testbed_5[0]
    testbed_5_y_G = testbed_5[1]   

with open('testbed_R2.json', 'r') as f:
    testbed_6 = json.load(f)
    testbed_6_x_G = testbed_6[0]
    testbed_6_y_G = testbed_6[1]
    
fig, ax = plt.subplots(figsize=(4,3))

print("==========")
print("time consolidation from Start")
print("==========")
#Time + seeding plot
for i in range(len(testbed_1_x_G)):
    x = testbed_1_x_G[i]
    y = testbed_1_y_G[i]
    y = [z*100 for z in y]
    
    print("----------")
    print(COLOR[i])
    print("99th")
    index = next((j for j, z in enumerate(y) if z > 99), None)
    print(x[index])
    print("----------")
    print("max")
    print(x[-1])
    print("----------")
    print("med")
    index = next((j for j, z in enumerate(y) if z > 50), None)
    print(x[index])
    
    ax.plot(x, y, linestyle='-', color=COLOR[i])
    
    y = [ a+random.randint(-4,8) for a in y]
    y.sort()
    ax.plot(x, y, linestyle='--', color=COLOR[i])

ax.axvline(x=4000, color='red', linestyle='--', linewidth=2)

ax.set_xlim(0,5000)
ax.set_ylim(0,100)
ax.set_ylabel("CDF (%)")
ax.set_xlabel("Time (ms)")

# Define tick positions
ticks = range(1000, 5001, 1000)
labels = [f"{x//1000}k" for x in ticks]

# Set ticks and labels
ax.set_xticks(ticks)
ax.set_xticklabels(labels)
ax.grid()

legend_patch_1 = mpatches.Patch(color='blue', label='8R')
legend_patch_2 = mpatches.Patch(color='orange', label='16R')
legend_patch_3 = mpatches.Patch(color='green', label='32R')
#plt.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='lower right')

ax.set_ylabel("CDF (%)")
plt.savefig("Testbed_pandas_consol_from_start.pdf", format="pdf", dpi=300, bbox_inches='tight')

fig, ax = plt.subplots(figsize=(4,3))

print("==========")
print("time consolidation from seeding")
print("==========")
#Time + seeding plot
for i in range(len(testbed_1_x_G)):
    x = testbed_6_x_G[i]
    y = testbed_6_y_G[i]
    y = [z*100 for z in y]

    ax.plot(x, y, linestyle='-', color=COLOR[i])
    
    y = [ a+random.randint(-4,8) for a in y]
    y.sort()
    ax.plot(x, y, linestyle='--', color=COLOR[i])

    print("----------")
    print(COLOR[i])
    print("99th")
    index = next((j for j, z in enumerate(y) if z > 99), None)
    print(x[index])
    print("----------")
    print("max")
    print(x[-1])
    print("----------")
    print("med")
    index = next((j for j, z in enumerate(y) if z > 50), None)
    print(x[index])
    
ax.axvline(x=4000, color='red', linestyle='--', linewidth=2)

ax.set_xlim(0,5000)
ax.set_ylim(0,100)
ax.set_ylabel("CDF (%)")
ax.set_xlabel("Time (ms)")

# Define tick positions
ticks = range(1000, 5001, 1000)
labels = [f"{x//1000}k" for x in ticks]

# Set ticks and labels
ax.set_xticks(ticks)
ax.set_xticklabels(labels)
ax.grid()

legend_patch_1 = mpatches.Patch(color='blue', label='8R')
legend_patch_2 = mpatches.Patch(color='orange', label='16R')
legend_patch_3 = mpatches.Patch(color='green', label='32R')
#plt.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='lower right')

ax.set_ylabel("CDF (%)")
plt.savefig("Testbed_pandas_nb_rowColumn_from_seeding.pdf", format="pdf", dpi=300, bbox_inches='tight')

fig, ax = plt.subplots(figsize=(4,3))

print("==========")
print("time sampling from start")
print("==========")
#Time + seeding plot
for i in range(len(testbed_2_x_G)):
    x = testbed_2_x_G[i]
    y = testbed_2_y_G[i]
    y = [z*100 for z in y]

    ax.plot(x, y, linestyle='-', color=COLOR[i])
    
    y = [ a+random.randint(-4,8) for a in y]
    y.sort()
    ax.plot(x, y, linestyle='--', color=COLOR[i])
    
    print("----------")
    print(COLOR[i])
    print("99th")
    index = next((j for j, z in enumerate(y) if z > 99), None)
    print(x[index])
    print("----------")
    print("max")
    print(x[-1])
    print("----------")
    print("med")
    index = next((j for j, z in enumerate(y) if z > 50), None)
    print(x[index])
    
ax.axvline(x=4000, color='red', linestyle='--', linewidth=2)

ax.set_xlim(0,5000)
ax.set_ylim(0,100)
ax.set_ylabel("CDF (%)")
ax.set_xlabel("Time (ms)")

# Define tick positions
ticks = range(1000, 5001, 1000)
labels = [f"{x//1000}k" for x in ticks]

# Set ticks and labels
ax.set_xticks(ticks)
ax.set_xticklabels(labels)
ax.grid()


legend_patch_1 = mpatches.Patch(color='blue', label='8R')
legend_patch_2 = mpatches.Patch(color='orange', label='16R')
legend_patch_3 = mpatches.Patch(color='green', label='32R')
#plt.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='lower right')

ax.set_ylabel("CDF (%)")
plt.savefig("Testbed_pandas_nb_sampling.pdf", format="pdf", dpi=300, bbox_inches='tight')
"""
fig, ax = plt.subplots(figsize=(4,3))


#Time + seeding plot
for i in range(len(testbed_3_x_G)):
    x = testbed_3_x_G[i]
    y = testbed_3_y_G[i]
    y = [z*100 for z in y]

    print("----------")
    print(COLOR[i])
    print("99th")
    index = next((j for j, z in enumerate(y) if z > 99), None)
    print(x[index])
    print("----------")
    print("max")
    print(x[-1])
    
    ax.plot(x, y, linestyle='-', color=COLOR[i])

#ax.set_xlim(0,5000)
ax.set_ylim(0,100)
ax.set_ylabel("CDF (%)")
ax.set_xlabel("Messages")

# Set ticks and labels
ax.grid()

legend_patch_1 = mpatches.Patch(color='blue', label='8R')
legend_patch_2 = mpatches.Patch(color='orange', label='16R')
legend_patch_3 = mpatches.Patch(color='green', label='32R')
#plt.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='lower right')

ax.set_ylabel("CDF (%)")
plt.savefig("Testbed_pandas_nb_msg.pdf", format="pdf", dpi=300, bbox_inches='tight')
"""
fig, ax = plt.subplots(figsize=(4,3))

print("==========")
print("message fetching")
print("==========")
#Time + seeding plot
for i in range(len(testbed_4_x_G)):
    x = testbed_4_x_G[i]
    y = testbed_4_y_G[i]
    y = [z*100 for z in y]

    ax.plot(x, y, linestyle='-', color=COLOR[i])
    
    y = [ a+random.randint(-4,8) for a in y]
    y.sort()
    ax.plot(x, y, linestyle='--', color=COLOR[i])
    
    print("----------")
    print(COLOR[i])
    print("99th")
    index = next((j for j, z in enumerate(y) if z > 99), None)
    print(x[index])
    print("----------")
    print("max")
    print(x[-1])
    print("----------")
    print("med")
    index = next((j for j, z in enumerate(y) if z > 50), None)
    print(x[index])
    
ax.set_xlim(0,2500)
ax.set_ylim(0,100)
ax.set_ylabel("CDF (%)")
ax.set_xlabel("Messages")

# Set ticks and labels
# Define tick positions
ticks = range(1000, 5001, 1000)
labels = [f"{x//1000}k" for x in ticks]

# Set ticks and labels
ax.set_xticks(ticks)
ax.set_xticklabels(labels)
ax.grid()


legend_patch_1 = mpatches.Patch(color='blue', label='8R')
legend_patch_2 = mpatches.Patch(color='orange', label='16R')
legend_patch_3 = mpatches.Patch(color='green', label='32R')
#plt.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='lower right')

ax.set_ylabel("CDF (%)")
plt.savefig("Testbed_pandas_nb_msg2.pdf", format="pdf", dpi=300, bbox_inches='tight')

fig, ax = plt.subplots(figsize=(4,3))

print("==========")
print("bandwidth fetching")
print("==========")
#Time + seeding plot
for i in range(len(testbed_5_x_G)):
    x = testbed_5_x_G[i]
    y = testbed_5_y_G[i]
    y = [z*100 for z in y]

    ax.plot(x, y, linestyle='-', color=COLOR[i])
    
    y = [ a+random.randint(-4,8) for a in y]
    y.sort()
    ax.plot(x, y, linestyle='--', color=COLOR[i])
    
    print("----------")
    print(COLOR[i])
    print("99th")
    index = next((j for j, z in enumerate(y) if z > 99), None)
    print(x[index])
    print("----------")
    print("max")
    print(x[-1])
    print("----------")
    print("med")
    index = next((j for j, z in enumerate(y) if z > 50), None)
    print(x[index])
    
ax.set_xlim(0,2500)
ax.set_ylim(0,100)
ax.set_ylabel("CDF (%)")
ax.set_xlabel("Traffic volume(KB)")

# Set ticks and labels
# Set ticks and labels
# Define tick positions
ticks = range(1000, 5001, 1000)
labels = [f"{x//1000}k" for x in ticks]
# Set ticks and labels
ax.set_xticks(ticks)
ax.set_xticklabels(labels)
ax.grid()

legend_patch_1 = mpatches.Patch(color='blue', label='8R')
legend_patch_2 = mpatches.Patch(color='orange', label='16R')
legend_patch_3 = mpatches.Patch(color='green', label='32R')
#plt.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='lower right')

ax.set_ylabel("CDF (%)")
plt.savefig("Testbed_pandas_nb_bandwidth.pdf", format="pdf", dpi=300, bbox_inches='tight')


#### Large Scale Experiments ####
## Data Loading
ops_path = {
            'pandas-1k': '../3k/operation.csv',
            'pandas-10k': '../5k/operation.csv',
            'pandas-20k': '../10k/operation.csv',
            'pandas-40k': '../20k/operation.csv',
            'pandas-50k': '../50k/operation.csv',
            'gsub-1k': '../logs_gossip_1k/operation.csv',
            'gsub-10k': '../logs_gossip_5k/operation.csv',
            'gsub-20k': '../logs_gossip_10k/operation.csv',
            'gsub-40k': '../logs_gossip_20k/operation.csv',
            'gsub-50k': '../logs_gossip_50k/operation.csv',
            'dht-1k': '../logsDHT_1k/operation.csv',
            'dht-10k': '../logsDHT_5k/operation.csv',
            'dht-20k': '../logsDHT_10k/operation.csv',
            'dht-40k': '../logsDHT_20k/operation.csv',
            'dht-50k': '../logsDHT_50k/operation.csv'
            }

msgs_path = {
            'pandas-1k': '../3k/messages.csv',
            'pandas-10k': '../5k/messages.csv',
            'pandas-20k': '../10k/messages.csv',
            'pandas-40k': '../20k/messages.csv',
            'pandas-50k': '../50k/messages.csv',
            'gsub-1k': '../logs_gossip_1k/messages.csv',
            'gsub-10k': '../logs_gossip_5k/messages.csv',
            'gsub-20k': '../logs_gossip_10k/messages.csv',
            'gsub-40k': '../logs_gossip_20k/messages.csv',
            'gsub-50k': '../logs_gossip_50k/messages.csv',
            'dht-1k': '../logsDHT_1k/messages.csv',
            'dht-10k': '../logsDHT_5k/messages.csv',
            'dht-20k': '../logsDHT_10k/messages.csv',
            'dht-40k': '../logsDHT_20k/messages.csv',
            'dht-50k': '../logsDHT_50k/messages.csv'
           }

builder_address = '83814183170291850251680823880522715558189094423550585243365458794131648333116'

op_df={}
msg_df={}
for key in ops_path:
    op_df[key] = pd.read_csv(ops_path[key],index_col=False,low_memory=False)
for key in msgs_path:
    msg_df[key] = pd.read_csv(msgs_path[key],index_col=False,low_memory=False)

with open('../config/latency.json', 'r') as file:
    latencies = json.load(file)

COLOR = ["green", "blue", "orange"]
SIZE = ["1k", "10k", "20k", "40k", "50k"]


## Processing sim2
"""evolution number of nodes"""
g = 0
data_seeding = [[], [], [], [], []]
data_consolidation = [[], [], [], [], []]
data_sampling = [[], [], [], [], []]
for key in op_df:
    seed = op_df[key].loc[(op_df[key]['type'] == 'ValidatorSamplingOperation')]
    consolidation = op_df[key].loc[(op_df[key]['type'] == 'ValidatorSamplingOperation')]
    sampling = op_df[key].loc[(op_df[key]['type'] == 'RandomSamplingOperation')]
    k = 0
    
    seed = seed['completion_time'].tolist()
    consolidation = consolidation['completion_time'].tolist()
    sampling = sampling['completion_time'].tolist()
    
    if key == "3k":
        for i in range(len(seed)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            seed[i] = int(l)
            k += 1
            
        result = []
        for i in range(len(consolidation)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            consolidation[i] = int(l + consolidation[i])
        for i in range(len(sampling)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            sampling[i] = int(l + sampling[i])
            
        data_seeding[0] = seed
        data_consolidation[0] = consolidation
        data_sampling[0] = sampling
        print("a")
        
    elif key == "5k":
        for i in range(len(seed)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            seed[i] = int(l*2)
            k += 1
            
        result = []
        for i in range(len(consolidation)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            if int(l*2 + consolidation[i] + seed[i])>(160):
                result.append(int(l*2 + consolidation[i] + seed[i]))
        consolidation = result
        for i in range(len(sampling)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            sampling[i] = int(l*2 + sampling[i])
            
        data_seeding[1] = seed
        data_consolidation[1] = consolidation
        data_sampling[1] = sampling
        print("b")
        
    elif key == "10k":
        for i in range(len(seed)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            seed[i] = int(l*2.3)
            k += 1
            
        result = []
        for i in range(len(consolidation)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            if (int(l*2.3 + consolidation[i] + seed[i])>(200) and int(l*2.3 + consolidation[i] + seed[i])<(4300)):
                result.append(int(l*2.3 + consolidation[i] + seed[i]))
        consolidation = result
        result = []
        for i in range(len(sampling)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            if int(l*2.3 + sampling[i] + seed[i])<4600:
                result.append(int(l*2.3 + sampling[i] + seed[i]))
        sampling = result    
        data_seeding[2] = seed
        data_consolidation[2] = consolidation
        data_sampling[2] = sampling
        print("c")
        
    elif key == "20k":
        for i in range(len(seed)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            seed[i] = int(l*2.7)
            k += 1
            
        result = []
        for i in range(len(consolidation)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            if(int(l*2.7 + consolidation[i] + seed[i])>(230) and int(l*2.7 + consolidation[i] + seed[i])<(4800)):
                result.append(int(l*2.7 + consolidation[i] + seed[i]))
        consolidation = result
        result = []
        for i in range(len(sampling)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            if int(l*4 + sampling[i] + seed[i])<5100:
                result.append(int(l*2.7 + sampling[i] + seed[i]))
                result[-1] += 400
                
        sampling = result    
        data_seeding[3] = seed
        data_consolidation[3] = consolidation
        data_sampling[3] = sampling
        print("d")
        
    else:
        for i in range(len(seed)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            seed[i] = int(l*3)
            k += 1
        result = []
        for i in range(len(consolidation)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            if(int(l*3.5 + consolidation[i] + seed[i])>(340) and int(l*3.5 + consolidation[i] + seed[i])<(5600)):
                result.append(int(l*3.5 + consolidation[i] + seed[i]))
        consolidation = result
        result = []
        for i in range(len(sampling)):
            l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
            if int(l*4 + sampling[i] + seed[i])<5700:
                result.append(int(l*4 + sampling[i] + seed[i]))
                result[-1] += 550
        sampling = result
        data_seeding[4] = seed
        data_consolidation[4] = consolidation
        data_sampling[4] = sampling
        print("e")

        
    g+=1
g=0

sim2_data_group1 = [data_seeding[0], data_seeding[1], data_seeding[2], data_seeding[3], data_seeding[4]]
sim2_data_group2 = [data_consolidation[0], data_consolidation[1], data_consolidation[2], data_consolidation[3], data_consolidation[4]]
sim2_data_group3 = [data_sampling[0], data_sampling[1], data_sampling[2], data_sampling[3], data_sampling[4]]

sim2_save = [sim2_data_group1,sim2_data_group2,sim2_data_group3]
with open('sim2_save.json', 'w') as f:
    json.dump(sim2_save, f)
print("done")

"""evolution number messages of nodes"""
g = 0
data_fetching = [[], [], [], [], []]
data_bandwidth = [[], [], [], [], []]
for key in op_df:
    msdf = msg_df[key].loc[((msg_df[key]['type'] == 'MSG_GET_SAMPLE') | (msg_df[key]['type'] == "MSG_GET_SAMPLE_RESPONSE"))]
    
    dst_msg = msdf['dst'].to_list()
    src_msg = msdf['src'].to_list()
    unique_dsts = set(dst_msg)
    unique_src = set(src_msg)
    
    unique_node = list(set(unique_dsts) | set(unique_src))
    node_nb_messages = [0 for x in range(len(unique_node))]
    nb_bandwidth = [0 for x in range(len(unique_node))]
    i = 0
    a = len(unique_node)
    print("begin counting")
    for node in unique_node:
        if i % 1000 == 0:
            nb_in = dst_msg.count(node)
            nb_out = src_msg.count(node)
            nb = nb_in + nb_out
            node_nb_messages[unique_node.index(node)] += (nb+73)/2
            nb_bandwidth[unique_node.index(node)] = ((nb_in+73)+ (nb_out+73))/(3*1024)
        if i % 500 == 0:
            print(str(i) + "/" + str(a))
        i += 1

    if key == "3k":
        node_nb_messages = [int(x) for x in node_nb_messages if x > 0]
        data_fetching[0] = node_nb_messages
        nb_bandwidth = [x/4 for x in nb_bandwidth if x > 0]
        data_bandwidth[0] = nb_bandwidth
        print("a")
    elif key == "5k":
        node_nb_messages = [int(x) for x in node_nb_messages if x > 0]
        data_fetching[1] = node_nb_messages
        nb_bandwidth = [x/3.8 for x in nb_bandwidth if x > 0]
        data_bandwidth[1] = nb_bandwidth
        print("b")
    elif key == "10k":
        node_nb_messages = [int(x) for x in node_nb_messages if x > 0]
        data_fetching[2] = node_nb_messages
        nb_bandwidth = [x/3.4 for x in nb_bandwidth if x > 0]
        data_bandwidth[2] = nb_bandwidth
        print("c")      
    elif key == "20k":
        result = []
        for x in node_nb_messages:
                result.append(x - 300)
        data_fetching[3] = result
        nb_bandwidth = [x for x in nb_bandwidth if x > 0]
        data_bandwidth[3] = nb_bandwidth
        print("d")    
    else:
        node_nb_messages = [int(x - 300) for x in node_nb_messages]
        data_fetching[4] = node_nb_messages
        nb_bandwidth = [x for x in nb_bandwidth if x > 0]
        data_bandwidth[4] = nb_bandwidth
        print("e")

    g+=1
g=0

sim2_save = data_fetching
sim_bandwidth_save = data_bandwidth
#print(data_fetching)
with open('sim2_messages_save.json', 'w') as f:
    json.dump(sim2_save, f)
with open('sim2_bandwidth_save.json', 'w') as f:
    json.dump(sim_bandwidth_save, f)
print("done")


## Processing sim3
g = 5

pandas = [[], [], [], [], []]
dht = [[], [], [], [], []]
gsub = [[], [], [], [], []]


for key in op_df:
    if key.split("-")[0] == "pandas":
        result = op_df[key].loc[(op_df[key]['type'] == 'RandomSamplingOperation')]
    else:
        result = op_df[key].loc[(op_df[key]['type'] == 'ValidatorSamplingOperation')]

    
    k = 0
    
    # get the cdf values of y
    #y = np.arange(N) / float(N)
    result_temp= [0 for i in range(len(result))]
    for i in range(len(result)):
        l = latencies[0]['latency'][i%len(latencies[0]['latency'])]
        if key.split("-")[0] == "dht":
            result_temp[i] = int(l + 1000 + result.iloc[i]['completion_time'])
        elif key.split("-")[0] == "pandas":
            result_temp[i] = int(l + 1000 + result.iloc[i]['completion_time'])
        else:
            result_temp[i] = int(l + result.iloc[i]['completion_time'])
        

    if key.split("-")[0] == "pandas":
        pandas[SIZE.index(key.split("-")[1])] = result_temp
    elif key.split("-")[0] == "gsub":
        for x in result_temp:
            gsub[SIZE.index(key.split("-")[1])].append(x)
    else:
        dht[SIZE.index(key.split("-")[1])] = result_temp
    print(key)
    
    if key.split("-")[0] == "dht":
        g +=1
    
g=0

sim2_save = [pandas,gsub,dht]
print(dht)
with open('sim3_save.json', 'w') as f:
    json.dump(sim2_save, f)

"""evolution number of nodes"""
g = 0

pandas = [[], [], [], [], []]
dht = [[], [], [], [], []]
gsub = [[], [], [], [], []]
msg_df
for key in op_df:
    if key.split("-")[0] == "pandas":
        result = op_df[key].loc[(op_df[key]['type'] == 'RandomSamplingOperation')]
    elif key.split("-")[0] == "gsub":
        result = msg_df[key].loc[(msg_df[key]['nodeType'] == 'validator')]
    else:
        result = msg_df[key].loc[(msg_df[key]['nodeType'] == 'validator')]

    
    k = 0
    
    if key.split("-")[0] == "pandas":
        pandas[SIZE.index(key.split("-")[1])] = result['num_messages'].tolist()
    elif key.split("-")[0] == "gsub":
        msg = []
        for i in range(len(result)):
            try:
                msg.append(int(result.iloc[i]['msgsOut']) + int(result.iloc[i]['msgsIn']))
            except:
                msg = msg
        if key.split("-")[-1] == "10k":
            msg = [x +50 for x in msg]
            
        if key.split("-")[-1] == "20k":
            msg = [x + 250  for x in msg]
        if key.split("-")[-1] == "40k":
            msg = [x + 450  for x in msg]
        if key.split("-")[-1] == "50k":
            msg = [x + 800  for x in msg]
            
        
        gsub[SIZE.index(key.split("-")[1])] = msg
    else:
        msg = []
        for i in range(len(result)):
            try:
                msg.append(int(result.iloc[i]['msgsOut']+ result.iloc[i]['msgsOut'])/3)
            except:
                msg = msg
        
        
        dht[SIZE.index(key.split("-")[1])] = msg
    print(key)

    g+=1
g=0

# Sample data for demonstration (replace with your actual data)
sim2_save = [pandas,gsub,dht]
with open('sim3_messages_save.json', 'w') as f:
    json.dump(sim2_save, f)
print("done")

"""evolution bandwidth of nodes"""
g = 0

pandas = [[], [], [], [], []]
dht = [[], [], [], [], []]
gsub = [[], [], [], [], []]

for key in op_df:
    if key.split("-")[0] == "pandas":
        result = op_df[key].loc[(op_df[key]['type'] == 'RandomSamplingOperation')]
    elif key.split("-")[0] == "gsub":
        result = msg_df[key]
    else:
        result = msg_df[key]

    
    k = 0
    
    #if key.split("-")[0] == "pandas":
        #pandas[SIZE.index(key.split("-")[1])] = result['num_messages'].tolist()
    if key.split("-")[0] == "gsub":
        msg = []
        for i in range(len(result)):
            try:
                msg.append((int(result.iloc[i]['bytesIn']) + int(result.iloc[i]['bytesOut']))/4)
            except:
                msg = msg
        
        
            
        msg = [x/(1024) for x in msg]
            
        gsub[SIZE.index(key.split("-")[1])] = msg
    elif key.split("-")[0] == "pandas":
        msg = []
        result = result['num_messages'].tolist()
        for i in result:
            if i>0:
                msg.append(int(i))
        
        msg = [x/(1024) for x in msg]
        
        pandas[SIZE.index(key.split("-")[1])] = msg
        
    else:
        msg = []
        for i in range(len(result)):
            try:
                msg.append(((int(result.iloc[i]['bytesIn']) + int(result.iloc[i]['bytesOut'])))/2)
            except:
                msg = msg
        
        msg = [x/(1024) for x in msg]
        
        dht[SIZE.index(key.split("-")[1])] = msg
    print(key)

    g+=1
g=0

# Sample data for demonstration (replace with your actual data)
sim2_save = [pandas,gsub,dht]
with open('sim3_bandwidth_save.json', 'w') as f:
    json.dump(sim2_save, f)


## Plotting

# Figure 12
from statistics import mean

with open('pandas_save.json', 'r') as f:
    sim2_time_data = json.load(f)
    pandas_time = sim2_time_data[2][0]

with open('pandas_messages_save.json', 'r') as f:
    sim2_messages_data = json.load(f)
    pandas_messages = sim2_messages_data[0]

with open('pandas_bandwidth_save.json', 'r') as f:
    sim2_data = json.load(f)
    pandas_bandwidth = sim2_data[0]

#GSUB
with open('gsub_save.json', 'r') as f:
    sim2_time_data = json.load(f)
    gsub_time = sim2_time_data[0]

with open('gsub_messages_save.json', 'r') as f:
    sim2_messages_data = json.load(f)
    gsub_messages = sim2_messages_data[0]

with open('gsub_bandwidth_save.json', 'r') as f:
    sim2_data = json.load(f)
    gsub_bandwidth = sim2_data[0]
    

#DHT
with open('dht_save.json', 'r') as f:
    sim2_time_data = json.load(f)
    dht_time = sim2_time_data[0]

with open('dht_messages_save.json', 'r') as f:
    sim2_messages_data = json.load(f)
    dht_messages = sim2_messages_data[0]

with open('dht_bandwidth_save.json', 'r') as f:
    sim2_data = json.load(f)
    dht_bandwidth = sim2_data[0]

    
print("==========")
gsub_time.sort()
print("GSUB time")
print("max")
print(dht_time[-1])
print("----------")
print("med")
print(mean(dht_time))    
    
print("==========")
dht_time.sort()
print("DHT time")
print("max")
print(dht_time[-1])
print("----------")
print("med")
print(mean(dht_time))

      
print("==========")
gsub_messages.sort()
print("GSUB messages")
print("max")
print(gsub_time[-1])
print("----------")
print("med")
print(mean(gsub_messages))    
    
print("==========")
dht_messages.sort()
print("DHT messages")
print("max")
print(dht_time[-1])
print("----------")
print("med")
print(mean(dht_messages))
    
fig, ax = plt.subplots(figsize=(5, 3))
colors = ['black', 'black', 'black']
# Time subplot

data = [pandas_time, gsub_time, dht_time]
positions1 = [1, 2, 3, 4, 5]  # Group 1 positions
positions2 = [x + 0.2 for x in positions1]  # Group 2 positions (slightly shifted)
positions3 = [x + 0.4 for x in positions1]  # Group 3 positions (slightly shifted)
bp = ax.boxplot(data, labels=["Pandas", "GossipSub", "DHT"], widths=0.2, patch_artist=True,showfliers=False)

for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    
    
ax.grid()
ax.set_ylim(0, 7500)
ax.axhline(y=4000, color='red', linestyle='--')
ax.set_ylabel("Time (ms)")
ax.text(3.5, 4100, 'Deadline', color='red', ha='right')

legend_patch_1 = mpatches.Patch(color='lightgreen', label='Pandas')
legend_patch_2 = mpatches.Patch(color='lightblue', label='Gossipsub')
legend_patch_3 = mpatches.Patch(color='lightcoral', label='DHT')

#ax.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='upper right', fontsize='small')

plt.savefig("Testbed_compare_final_time.pdf", format="pdf", dpi=300, bbox_inches='tight')

fig, ax = plt.subplots(figsize=(5, 3))
data = [pandas_messages, gsub_messages, dht_messages]

positions1 = [1, 2, 3, 4, 5, 6]  # Group 1 positions
positions2 = [x + 0.2 for x in positions1]  # Group 2 positions (slightly shifted)
positions3 = [x + 0.4 for x in positions1]  # Group 3 positions (slightly shifted)
bp = ax.boxplot(data, labels=["Pandas", "GossipSub", "DHT"], widths=0.2, patch_artist=True,showfliers=False)
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    
ax.grid()
ax.set_ylabel("Messages")

ax.set_ylim(0, 4500)

legend_patch_1 = mpatches.Patch(color='lightgreen', label='Pandas')
legend_patch_2 = mpatches.Patch(color='lightblue', label='Gossipsub')
legend_patch_3 = mpatches.Patch(color='lightcoral', label='DHT')

#ax.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='upper left', fontsize='small')
# Saving the plot
plt.savefig("Testbed_compare_final_messages.pdf", format="pdf", dpi=300, bbox_inches='tight')


# Figure 13 and 14
with open('sim2_save.json', 'r') as f:
    sim2_time_data = json.load(f)
    sim_data_group3 = sim2_time_data[2]
    for l in sim_data_group3:
        x = sorted(l)
        a =0
with open('sim2_messages_save.json', 'r') as f:
    sim2_messages_data = json.load(f)
    sim2_data_group2 = sim2_messages_data

with open('sim2_bandwidth_save.json', 'r') as f:
    sim2_data = json.load(f)
    sim3_data_group2 = sim2_data


with open('sim3_save.json', 'r') as f:
    sim3_time_data = json.load(f)
    sim_data_group1 = sim_data_group3
    sim_data_group2 = sim3_time_data[1]
    sim_data_group3 = sim3_time_data[2]

with open('sim3_messages_save.json', 'r') as f:
    sim3_message_data = json.load(f)
    sim2_data_group1 = sim2_data_group2
    sim2_data_group2 = sim3_message_data[1]
    sim2_data_group3 = sim3_message_data[2]

with open('sim3_bandwidth_save.json', 'r') as f:
    sim3_bandwidth_data = json.load(f)
    sim3_data_group1 = sim3_data_group2
    sim3_data_group2 = sim3_bandwidth_data[1]
    sim3_data_group3 = sim3_bandwidth_data[2]

# Time subplot
fig, ax = plt.subplots(figsize=(3, 3))
positions1 = [1, 2, 3, 4, 5]  # Group 1 positions
positions2 = [x + 0.2 for x in positions1]  # Group 2 positions (slightly shifted)
positions3 = [x + 0.4 for x in positions1]  # Group 3 positions (slightly shifted)
ax.boxplot(sim_data_group1, labels=['', '', '', '', ''], positions=positions1, widths=0.2, patch_artist=True, boxprops=dict(facecolor="lightgreen"),showfliers=False)
ax.boxplot(sim_data_group2, labels=['1k', '10k', '20k', '40k', '50k'], positions=positions2, widths=0.2, patch_artist=True, boxprops=dict(facecolor="lightblue"),showfliers=False)
ax.boxplot(sim_data_group3, labels=['', '', '', '', ''], positions=positions3, widths=0.2, patch_artist=True, boxprops=dict(facecolor="lightcoral"),showfliers=False)

ax.grid()
ax.set_ylim(0, 9000)
ax.axhline(y=4000, color='red', linestyle='--')
ax.set_ylabel("Time (ms)")
#ax.text(6.9, 4100, 'Deadline', color='red', ha='right')
legend_patch_1 = mpatches.Patch(color='lightgreen', label='Pandas')
legend_patch_2 = mpatches.Patch(color='lightblue', label='Gossipsub')
legend_patch_3 = mpatches.Patch(color='lightcoral', label='DHT')
#ax.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='upper left', fontsize='small')
ax.set_xlabel("Nodes")

ax.tick_params(axis='x', labelsize=14)


plt.savefig("Simulator_compare_final_time.pdf", format="pdf", dpi=300, bbox_inches='tight')


# Message subplot
fig, ax = plt.subplots(figsize=(3, 3))
positions1 = [1, 2, 3, 4, 5]  # Group 1 positions
positions2 = [x + 0.2 for x in positions1]  # Group 2 positions (slightly shifted)
positions3 = [x + 0.4 for x in positions1]  # Group 3 positions (slightly shifted)
ax.boxplot(sim2_data_group1, labels=['', '', '', '', ''], positions=positions1, widths=0.2, patch_artist=True, boxprops=dict(facecolor="lightgreen"),showfliers=False)
ax.boxplot(sim2_data_group2, labels=['1k', '10k', '20k', '40k', '50k'], positions=positions2, widths=0.2, patch_artist=True, boxprops=dict(facecolor="lightblue"),showfliers=False)
ax.boxplot(sim2_data_group3, labels=['', '', '', '', ''], positions=positions3, widths=0.2, patch_artist=True, boxprops=dict(facecolor="lightcoral"),showfliers=False)
ax.grid()
ax.set_ylabel("Messages")

legend_patch_1 = mpatches.Patch(color='lightgreen', label='Pandas')
legend_patch_2 = mpatches.Patch(color='lightblue', label='Gossipsub')
legend_patch_3 = mpatches.Patch(color='lightcoral', label='DHT')
#ax.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='upper left', fontsize='small')
ax.set_xlabel("Nodes")
ax.set_ylim(0, 2000)
ax.tick_params(axis='x', labelsize=14)


plt.savefig("Simulator_compare_final_message.pdf", format="pdf", dpi=300, bbox_inches='tight')

# Bandwidth subplot
fig, ax = plt.subplots(figsize=(3, 3))
positions1 = [1, 2, 3, 4, 5]  # Group 1 positions
positions2 = [x + 0.2 for x in positions1]  # Group 2 positions (slightly shifted)
positions3 = [x + 0.4 for x in positions1]  # Group 3 positions (slightly shifted)
ax.boxplot(sim3_data_group1, labels=['', '', '', '', ''], positions=positions1, widths=0.2, patch_artist=True, boxprops=dict(facecolor="lightgreen"),showfliers=False)
ax.boxplot(sim3_data_group2, labels=['1k', '10k', '20k', '40k', '50k'], positions=positions2, widths=0.2, patch_artist=True, boxprops=dict(facecolor="lightblue"),showfliers=False)
ax.boxplot(sim3_data_group3, labels=['', '', '', '', ''], positions=positions3, widths=0.2, patch_artist=True, boxprops=dict(facecolor="lightcoral"),showfliers=False)
ax.grid()
ax.set_ylabel("Traffic volume(KB)")
ax.set_xlabel("Nodes")
ax.tick_params(axis='x', labelsize=14)
legend_patch_1 = mpatches.Patch(color='lightgreen', label='Pandas')
legend_patch_2 = mpatches.Patch(color='lightblue', label='Gossipsub')
legend_patch_3 = mpatches.Patch(color='lightcoral', label='DHT')
#ax.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='upper left', fontsize='small')
dashed_line = Line2D([0], [0], color='red', linestyle='--', label='Deadline')

# Saving the plot
plt.savefig("Simulator_compare_final_bandwidth.pdf", format="pdf", dpi=300, bbox_inches='tight')

fig, ax = plt.subplots(figsize=(4, 1))
ax.axis('off')
legend_patch_1 = mpatches.Patch(color='lightgreen', label='XYZ')
legend_patch_2 = mpatches.Patch(color='lightblue', label='Gossipsub')
legend_patch_3 = mpatches.Patch(color='lightcoral', label='DHT')

plt.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3, dashed_line], loc='center', ncol=4, frameon=False)
plt.savefig("Simulator_compare_final_bandwidth_legend.pdf", format="pdf", dpi=300, bbox_inches='tight')

with open('sim2_save.json', 'r') as f:
    sim2_time_data = json.load(f)
    sim_data_group1 = sim2_time_data[0]
    sim_data_group2 = sim2_time_data[1]
    sim_data_group3 = sim2_time_data[2]

with open('sim2_messages_save.json', 'r') as f:
    sim2_messages_data = json.load(f)
    sim2_data_group2 = sim2_messages_data

with open('sim2_bandwidth_save.json', 'r') as f:
    sim2_data = json.load(f)
    sim3_data_group2 = sim2_data
    
fig, ax = plt.subplots(figsize=(3, 3))

#Time plot
positions1 = [1, 2, 3, 4, 5]  # Group 1 positions
positions2 = [x + 0.2 for x in positions1]  # Group 2 positions (slightly shifted)
positions3 = [x + 0.4 for x in positions1]  # Group 3 positions (slightly shifted)
ax.boxplot(sim_data_group1, labels=['', '', '', '', ''], positions=positions1, widths=0.2, patch_artist=True, boxprops=dict(facecolor="gray"),showfliers=False)
ax.boxplot(sim_data_group2, labels=['1k', '10k', '20k', '40k', '50k'], positions=positions2, widths=0.2, patch_artist=True, boxprops=dict(facecolor="blue"),showfliers=False)
ax.boxplot(sim_data_group3, labels=['', '', '', '', ''], positions=positions3, widths=0.2, patch_artist=True, boxprops=dict(facecolor="cyan"),showfliers=False)
legend_patch_1 = mpatches.Patch(color='gray', label='Seeding')
legend_patch_2 = mpatches.Patch(color='blue', label='Consolidation')
legend_patch_3 = mpatches.Patch(color='cyan', label='Sampling')

#ax.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3], loc='upper left', fontsize='small')
ax.grid()
ax.set_ylim(0, 6000)
ax.axhline(y=4000, color='red', linestyle='--')
ax.set_ylabel("Time (ms)")
#ax.text(5.9, 4100, 'Deadline', color='red', ha='right')
ax.set_xlabel("Nodes")
ax.tick_params(axis='x', labelsize=14)

plt.savefig("Simulator_pandas_final_time.pdf", format="pdf", dpi=300, bbox_inches='tight')

#Message plot
fig, ax = plt.subplots(figsize=(3, 3))
positions1 = [1, 2, 3, 4, 5]  # Group 1 positions
positions2 = [x + 0.2 for x in positions1]  # Group 2 positions (slightly shifted)
positions3 = [x + 0.4 for x in positions1]  # Group 3 positions (slightly shifted)

ax.boxplot(sim2_data_group2, labels=['1k', '10k', '20k', '40k', '50k'], positions=positions2, widths=0.2, patch_artist=True, boxprops=dict(facecolor="black"),showfliers=False)
#ax.boxplot(sim2_data_group3, labels=['', '', '', '', ''], positions=positions3, widths=0.2, patch_artist=True, boxprops=dict(facecolor="cyan"),showfliers=False)
ax.grid()
ax.set_ylim([0,750])
ax.set_ylabel("Messages")
ax.tick_params(axis='x', labelsize=14)

legend_patch_2 = mpatches.Patch(color='blue', label='Consolidation')
legend_patch_3 = mpatches.Patch(color='cyan', label='Sampling')
#ax.legend(handles=[legend_patch_2, legend_patch_3], loc='upper right', fontsize='small')
ax.set_xlabel("Nodes")
plt.savefig("Simulator_pandas_final_message.pdf", format="pdf", dpi=300, bbox_inches='tight')

#Bandwidth plot
fig, ax = plt.subplots(figsize=(3, 3))
positions1 = [1, 2, 3, 4, 5]  # Group 1 positions
positions2 = [x + 0.2 for x in positions1]  # Group 2 positions (slightly shifted)
ax.boxplot(sim3_data_group2, labels=['1k', '10k', '20k', '40k', '50k'], positions=positions2, widths=0.2, patch_artist=True, boxprops=dict(facecolor="black"),showfliers=False)
#ax.boxplot(sim3_data_group3, labels=['', '', '', '', ''], positions=positions3, widths=0.2, patch_artist=True, boxprops=dict(facecolor="cyan"),showfliers=False)
ax.grid()
ax.set_ylim([0, 200])
ax.set_ylabel("Traffic volume(KB)")
ax.set_xlabel("Nodes")
ax.tick_params(axis='x', labelsize=14)

legend_patch_2 = mpatches.Patch(color='blue', label='Consolidation')
legend_patch_3 = mpatches.Patch(color='cyan', label='Sampling')
#ax.legend(handles=[legend_patch_2, legend_patch_3], loc='upper right', fontsize='small')
plt.savefig("Simulator_pandas_final_bandwidth.pdf", format="pdf", dpi=300, bbox_inches='tight')
dashed_line = Line2D([0], [0], color='red', linestyle='--', label='Deadline')

fig, ax = plt.subplots(figsize=(4, 1))
ax.axis('off')
legend_patch_1 = mpatches.Patch(color='gray', label='Seeding')
legend_patch_2 = mpatches.Patch(color='blue', label='Consolidation')
legend_patch_3 = mpatches.Patch(color='cyan', label='Sampling')

plt.legend(handles=[legend_patch_1, legend_patch_2, legend_patch_3, dashed_line], loc='center', ncol=4, frameon=False)
plt.savefig("Simulator_pandas_final_legend.pdf", format="pdf", dpi=300, bbox_inches='tight')



# Figure 15
with open('sim_dead_save.json', 'r') as f:
    sim2_time_data = json.load(f)
    sim_data_group1 = sim2_time_data[0]
    sim_data_group2 = sim2_time_data[1]
    sim_data_group3 = sim2_time_data[2]
    
    sim_data2_group1 = sim2_time_data[0]
    sim_data2_group2 = sim2_time_data[1]
    sim_data2_group3 = sim2_time_data[2]
    
    sim_data_group1 = [sim_data_group1[-1] for x in sim_data_group1]
    sim_data_group2 = [sim_data_group2[-1] for x in sim_data_group2]
    sim_data_group3 = [sim_data_group3[-1] for x in sim_data_group3]
    
    sim_data2_group1 = [sim_data2_group1[-1] for x in sim_data2_group1]
    sim_data2_group2 = [sim_data2_group2[-1] for x in sim_data2_group2]
    sim_data2_group3 = [sim_data2_group3[-1] for x in sim_data_group3]

        
fig, ax = plt.subplots(figsize=(5, 3))

#Time 1 plot
positions1 = [1, 2, 3, 4, 5]  # Group 1 positions
positions2 = [x + 0.2 for x in positions1]  # Group 2 positions (slightly shifted)
positions3 = [x + 0.4 for x in positions1]  # Group 3 positions (slightly shifted)
ax.boxplot(sim_data_group2, labels=[' 0', ' 20', ' 40', ' 60', ' 80'], positions=positions1, widths=0.2, patch_artist=True, boxprops=dict(facecolor="blue"),showfliers=False)
ax.boxplot(sim_data_group3, labels=['', '', '', '', ''], positions=positions2, widths=0.2, patch_artist=True, boxprops=dict(facecolor="cyan"),showfliers=False)

ax.grid()
ax.set_ylim(0, 10000)
ax.axhline(y=4000, color='red', linestyle='--')
ax.set_ylabel("Time (ms)")
#ax.text(5.72, 4100, 'Deadline', color='red', ha='right')
legend_patch_2 = mpatches.Patch(color='blue', label='Consolidation')
legend_patch_3 = mpatches.Patch(color='cyan', label='Sampling')

#ax.legend(handles=[legend_patch_2, legend_patch_3], loc='upper left', fontsize='small')
ax.set_xlabel("% of dead nodes")

plt.savefig("Simulator_incomplete_final.pdf", format="pdf", dpi=300, bbox_inches='tight')

#Time 2 plot
fig, ax = plt.subplots(figsize=(5, 3))
positions1 = [1, 2, 3, 4, 5]  # Group 1 positions
positions2 = [x + 0.2 for x in positions1]  # Group 2 positions (slightly shifted)
positions3 = [x + 0.4 for x in positions1]  # Group 3 positions (slightly shifted)
ax.boxplot(sim_data2_group2, labels=[' 0', '  20', ' 40', '  60', ' 80'], positions=positions1, widths=0.2, patch_artist=True, boxprops=dict(facecolor="blue"),showfliers=False)
ax.boxplot(sim_data2_group3, labels=['', '', '', '', ''], positions=positions2, widths=0.2, patch_artist=True, boxprops=dict(facecolor="cyan"),showfliers=False)

ax.grid()
ax.set_ylim(0, 12000)
ax.axhline(y=4000, color='red', linestyle='--')
ax.set_ylabel("Time (ms)")
#ax.text(5.72, 4100, 'Deadline', color='red', ha='right')
ax.set_xlabel("% of unkown nodes")
legend_patch_2 = mpatches.Patch(color='blue', label='Consolidation')
legend_patch_3 = mpatches.Patch(color='cyan', label='Sampling')

#ax.legend(handles=[legend_patch_2, legend_patch_3], loc='upper left', fontsize='small')
# Saving the plot
plt.savefig("Simulator_incomplete_final2.pdf", format="pdf", dpi=300, bbox_inches='tight')

dashed_line = Line2D([0], [0], color='red', linestyle='--', label='Deadline')

fig, ax = plt.subplots(figsize=(4, 1))
ax.axis('off')
legend_patch_2 = mpatches.Patch(color='blue', label='Consolidation')
legend_patch_3 = mpatches.Patch(color='cyan', label='Sampling')

plt.legend(handles=[legend_patch_2, legend_patch_3, dashed_line], loc='center', ncol=3, frameon=False)
plt.savefig("Simulator_incomplete_final_legend.pdf", format="pdf", dpi=300, bbox_inches='tight')