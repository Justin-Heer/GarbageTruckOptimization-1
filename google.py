import googlemaps
from datetime import datetime, time
from key import API_KEY
import time
import pandas as pd
import multiprocessing as mp


def query(location1, location2, gmaps, t, processNumber, return_dict):
    df = pd.DataFrame(columns={"PID1", "PID2", "results"})

    numQueries = len(location1) * len(location1)
    numQueriesExecuted = 0

    for i in location1.iterrows():
        for j in location2.iterrows():
            address1 = i[1]['Address'] + ', Port Coquitlam, BC'
            address2 = j[1]['Address'] + ', Port Coquitlam, BC'

            directionsResult = gmaps.directions(origin=address1,
                                                destination=address2,
                                                mode="driving",
                                                departure_time=t)

            df = df.append({'PID1': i[1]['PID'], 'PID2': j[1]['PID'], 'results': directionsResult}, ignore_index=True)
            numQueriesExecuted += 1
            if numQueriesExecuted % 100 == 0:
                print("Process:", processNumber, ',', (numQueriesExecuted / numQueries) * 100, 'Percent Complete')
    return_dict[processNumber] = df


def main():
    # key.py contains a variable API_KEY that contains the key for google API.  See this page to create one
    # https://developers.google.com/maps/documentation/geocoding/get-api-key and this one to get an account going
    # https://developers.google.com/maps/gmp-get-started

    df = pd.read_csv('locations.csv')
    df = df[['Address', 'Garbage Zone', 'PID']]
    df = df.iloc[0:10, :]

    queryTime = datetime(2021, 2, 2, 9, 0, 0)

    # Authenticating with api
    gmaps = googlemaps.Client(key=API_KEY)

    numProcesses = 8
    processes = []
    manager = mp.Manager()
    return_dict = manager.dict()
    t0 = time.time()
    for process in range(0, numProcesses):
        processes.append(
            mp.Process(target=query, args=(df, df, gmaps, queryTime, process, return_dict))
        )

    for process in range(0, numProcesses):
        processes[process].start()

    for process in range(0, numProcesses):
        processes[process].join()
    t1 = time.time()
    print('Time:', t1 - t0)


if __name__ == '__main__':
    main()
