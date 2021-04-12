import pandas as pd
import ast 
import multiprocessing as mp
import numpy as np
import csv
import time

def parse_query(df, pairID, process, lock, return_ls) -> list: 
    #takes directions column from google query as input

    lock.acquire()
    try:
        print(f"in process {process} the value of pairID is {pairID}")
    finally:
        lock.release()
    
    for inx,query in df.iterrows():    
        ls = []
        for command in ast.literal_eval(query['directions']):
            start = [command['start_location']['lng'], command['start_location']['lat'], pairID]
            end = [command['end_location']['lng'], command['end_location']['lat'], pairID]

            pairID += 1
            ls.extend([start,end])
        
    lock.acquire()
    try:
        print(f"process {process} is appending results")
        return_ls.append(ls)
    finally:
        lock.release()
        

def write_csv(ls,header) -> None:
    with open('test.csv', 'w', newline='') as f:

        write = csv.writer(f)

        write.writerow(header)
        write.writerows(ls)


def main():
    # read in the queries that have already been made
    print(f"reading in data")
    df = pd.read_csv('google-distance-csvs//Results1.csv',usecols=['directions'],nrows=100)

    NUM_PROCESSES = 6                                    #SET THIS VALUE 

    # divy up threads
    print(f"Diving workload into {NUM_PROCESSES} processes")
    segments = np.array_split(np.arange(0,len(df)), NUM_PROCESSES)
    dfs =[]
    for segment in segments:
        dfs.append(df.iloc[segment,:])

    # create threads
    processes = []
    manager = mp.Manager()
    return_ls = manager.list()
    lock = mp.Lock()

    # define threads and start threads
    for process in range(0, NUM_PROCESSES):
        processes.append(
            mp.Process(target=parse_query,args=(dfs[process], (process+1)*1000, process, lock, return_ls))
        )
        print(f"Starting process {process}")
        processes[process].start()

    # Joining the threads
    for process in range(0, NUM_PROCESSES):
        print(f"Joining thread {process} ")
        processes[process].join()

    res_ls = [in_in_ls for in_ls in return_ls for in_in_ls in in_ls ]

    print("writing csv")
    header = ['longitude','latitude','pairID']
    write_csv(res_ls,header)
    

if __name__ == '__main__':
    main()
