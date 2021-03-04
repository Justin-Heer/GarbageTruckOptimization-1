import multiprocessing as mp
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
import time


def createRoutes(locations, routes, start):
    completeRoutes = {}
    for i in range(0, len(locations)):
        if i == start:
            completeRoutes[locations[i]] = [locations[i]]
        else:
            vertex = i
            route = [locations[vertex]]

            while vertex != start:
                vertex = routes[vertex]
                route.append(locations[vertex])
                # route.insert(0, vertex)
                completeRoutes[locations[i]] = route
    return completeRoutes


def dijkstrasThread(graph, locations, rows, processNumber, travelTimesDict):
    # Defining data frame to hold shortest travel times
    results = pd.DataFrame(columns=locations)

    # Defining data frame to hold shortest routes
    routes = pd.DataFrame(columns=locations)

    numIterations = 0
    numQueries = len(rows)
    for row in rows:
        # Executing dijkstras
        dist_matrix = dijkstra(csgraph=graph, indices=row, directed=False)

        # Recording the travel times
        results.loc[locations[row]] = dist_matrix

        # Incrementing the number of queries....to create visual output so the progress can be assessed
        numIterations += 1
        if numIterations % 100 == 0:
            print("Process:", processNumber, ',', (numIterations / numQueries) * 100, 'Percent Complete')

    travelTimesDict[processNumber] = results


def main():
    # Number of processes
    numProcesses = 8
    t0 = time.time()
    print("Reading in sparse Matrix")
    sparseMatrix = pd.read_csv('C:/Users/Aidan/OneDrive - Simon Fraser University (1sfu)/Garbage Route Optimization/sparseTimeMatrix.csv', index_col=0)
    # sparseMatrix = pd.read_csv('delete.csv', index_col=0)

    print("Defining Graph")
    graph = csr_matrix(sparseMatrix)


    # Creating the segments to divide up the dataframe between the threads
    segments = np.array_split(np.array(range(0, int(len(sparseMatrix)))), numProcesses)

    # # Dividing up the threads
    # dataFrames = []
    # for i in segments:
    #     dataFrames.append(sparseMatrix.iloc[i[0]: i[-1] + 1, ])

    # Creating the threads
    processes = []
    manager = mp.Manager()
    travelTimes_dict = manager.dict()

    # Defining the threads
    for process in range(0, numProcesses):
        processes.append(
            mp.Process(target=dijkstrasThread, args=(graph, sparseMatrix.index.values, segments[process], process, travelTimes_dict))
        )

    t1 = time.time()
    print('Startup time:', t1 - t0, 'seconds')

    t0 = time.time()
    # Starting the threads
    for process in range(0, numProcesses):
        processes[process].start()

    # Joining the threads
    for process in range(0, numProcesses):
        processes[process].join()

    # Putting all the dataframes together into 1
    travelTimes = travelTimes_dict[0]

    if numProcesses > 1:
        for process in range(1, numProcesses):
            travelTimes = pd.concat([travelTimes, travelTimes_dict[process]], axis=0)

    t1 = time.time()
    print('Computation Time:', t1 - t0, 'seconds')

    print("Saving to Disk")

    # print(travelTimes)
    # print(routes)
    travelTimes.to_csv('travelTimes.csv')
    # routes.to_csv('routes1.csv')


if __name__ == '__main__':
    main()
