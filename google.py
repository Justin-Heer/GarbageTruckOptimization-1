import googlemaps
from datetime import datetime
import pandas as pd
import multiprocessing as mp
import numpy as np
import os


def query(queries, gmaps, t, processNumber, return_dict):
    df = pd.DataFrame(columns={"start", "end", "time", "distance", 'directions'})

    numQueriesExecuted = 0
    numQueries = len(queries)

    for requestNum, request in queries.iterrows():
        # Querying addresses
        directionsResult = gmaps.directions(origin=request['startHouses'],
                                            destination=request['endHouses'],
                                            mode="driving",
                                            departure_time=t)

        # Extracting time, distance and directions
        time = directionsResult[0]['legs'][0]['duration']['value']
        distance = directionsResult[0]['legs'][0]['distance']['value']
        directions = directionsResult[0]['legs'][0]['steps']  # Need to store this somehow

        # Recording values in the df
        df = df.append({'start': request['startHouses'], 'end': request['endHouses'], 'time': time, 'distance': distance, 'directions': directions}, ignore_index=True)

        # Incrementing the number of queries....to create visual output so the progress can be assessed
        numQueriesExecuted += 1
        if numQueriesExecuted % 100 == 0:
            print("Process:", processNumber, ',', (numQueriesExecuted / numQueries) * 100, 'Percent Complete')

    return_dict[processNumber] = df


def main():
    # key.py contains a variable API_KEY that contains the key for google API.  See this page to create one
    # https://developers.google.com/maps/documentation/geocoding/get-api-key and this one to get an account going
    # https://developers.google.com/maps/gmp-get-started

    # IMPORTANT: READ IN THE RIGHT FILE HERE
    df = pd.read_csv('C:/Users/Aidan/OneDrive - Simon Fraser University (1sfu)/Garbage Route Optimization/Queries/depotQueries.csv', index_col=0)

    # IMPORTANT: PUT YOUR API KEY HERE
    API_KEY =

    # Defining the date/time we are requesting: 2021, March, 5, 12:00:00pm
    queryTime = datetime(2021, 3, 10, 12, 0, 0)

    # Authenticating with api
    gmaps = googlemaps.Client(key=API_KEY)

    # Number of processes
    numProcesses = 8

    # Creating the segments to divide up the dataframe between the threads
    segments = np.array_split(np.array(range(0, len(df))), numProcesses)

    # Dividing up the threads
    dataFrames = []
    for i in segments:
        dataFrames.append(df.iloc[i[0]: i[-1] + 1, ])

    # Creating the threads
    processes = []
    manager = mp.Manager()
    return_dict = manager.dict()

    # Defining the threads
    for process in range(0, numProcesses):
        processes.append(
            mp.Process(target=query, args=(dataFrames[process], gmaps, queryTime, process, return_dict))
        )

    # Starting the threads
    for process in range(0, numProcesses):
        processes[process].start()

    # Joining the threads
    for process in range(0, numProcesses):
        processes[process].join()

    # Putting all the dataframes together into 1
    results = return_dict[0]

    if numProcesses > 1:
        for process in range(1, numProcesses):
            results = pd.concat([results, return_dict[process]], axis=0)

    # Resetting the index
    results.reset_index()

    results.to_csv('depot_results.csv')

    # # Checking to see if this is the second one, if yes incrementing the name so nothing gets overwritten
    # if os.path.exists('extra_results1.csv'):
    #     results.to_csv('extra_results2.csv')
    # else:
    #     results.to_csv('extra_results1.csv')


if __name__ == '__main__':
    main()
