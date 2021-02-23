import Dijkstra
import pandas as pd

data = pd.read_csv('csvs\dijkstra-data.csv', index_col=0)

# Creates and instance of the Dijkstra class
dj = Dijkstra.Dijkstra(data)

# Computes the min distance from input (source) to each node, returns dataframe
source = '1003 PRAIRIE AVE, Port Coquitlam, BC, Canada'
dists = dj.dijkstra(source)
# print(dists)

# Once the .dijkstra method has been called then you can access the predecessor nodes using
prednodes = dj._pred_nodes
# print(prednodes)

# You can also return the path to a node using
node = '1028 PRAIRIE AVE, Port Coquitlam, BC, Canada'
print(dj.node_path(node))

# You should be able to use the path and the dists dataframe to validate the results  
