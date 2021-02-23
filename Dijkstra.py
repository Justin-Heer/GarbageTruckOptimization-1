import pandas as pd
import numpy as np

class Dijkstra():
    
    def __init__(self, data):
        self.data = data
        self._pred_nodes = None
        self._source = None
    
 
    def dijkstra(self, source):
        """runs the dijkstra algorithm and returns a dataframe with the 
        minimum distances from the source to each node

        Args:
            source (string): must be from data.index
        """

        # Set source
        self._source = source
        
        # Create a list of unvisited houses to track which nodes the algo has not visited yet
        unvisited_ls = self.data.index.to_list()
        
        # Initialize your dataframe that stores the distances from the source
        # to each  house 
        dists_df = pd.DataFrame(np.Inf,index=self.data.index, columns=[self._source])

        # Create a set to store every house that has been visited, initialize it to the source
        visited_set = {self._source}

        # Create a variable to store the current house
        curr = self._source

        # Set the distance to the source as 0
        dists_df.loc[self._source] = 0

        # Create dict to store predecessor node
        pred_node = dict.fromkeys(self.data.index.to_list(), np.nan)
        
        # While unvisited_ls is not empty
        while unvisited_ls: 
            
            # If the distance to the current node is set to infinity, throw an error
            if dists_df.loc[curr].values[0] == np.Inf:
                print('curr is {}'.format(curr))
                raise Exception('not working properly')
            
            # Create an index of all the nodes connected to the current node
            inx = self.data[curr].notna()
            
            # If the current node has no connected nodes at all, throw an error
            if inx.sum() == 0:
                raise Exception('No distance data for this house')
            
            # for each node connected to the current node, we want to update the distances from the source
            for node in self.data.loc[curr,inx].index:
                
                # if the distance from the current node to the node in question plus
                # the distance from the source to the current node is less than the 
                # currently assigned distance from the source to the node in question, reassign
                
                if self.data.at[curr,node] + dists_df.at[curr, self._source] < dists_df.at[node, self._source]:
                    dists_df.at[node, self._source] = self.data.at[curr,node] + dists_df.at[curr, self._source]
            
            # We want to find the new minimum node, aka the next closest house to the source
            # node that hasn't been visited
            
            # first remove the current node from unvisited, because we have already visitied it above
            unvisited_ls.remove(curr)

            # Create a list of condender nodes for the minimum node
            lsOfNodes = list(set(unvisited_ls)-visited_set)
            
            # check if the minimum distance is infinity, if yes then set all values 
            # to big number and then terminate while loop
            if (dists_df.loc[lsOfNodes].min()[0] == np.Inf):
                dists_df.loc[lsOfNodes] = 1e6
                print('conditional termination of while loop')
                break
            
            # Set the new value of minNode
            try:
                minNode = dists_df.loc[lsOfNodes].idxmin()[0]
            except:
                # If lsOfNodes is empty then pass, this happens on the final loop iteration
                if not lsOfNodes:
                    pass
                else:
                    raise Exception('Error when calculating new minNode')
            
            # Assign the predecessor node to the new minNode
            pred_node[minNode] = curr

            # prepare for the next iteration, add the minNode to the visited set and set current node
            visited_set.add(minNode)
            curr = minNode

        # Assign value to attribute, not pythonic but works for now
        self._pred_nodes = pred_node

        return dists_df

    def node_path(self, node):
        steps = [node]
        while node != self._source:
            node = self._pred_nodes[node]
            steps.append(node)
        return steps