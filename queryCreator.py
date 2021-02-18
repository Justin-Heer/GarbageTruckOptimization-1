import pandas as pd
import numpy as np


def assign_grids(df, n_grids=10):
    '''
    creates an n_grids x n_grids grid and assigns each home in df to its correct grid.
    Inclusive lower boundary, exclusive upper boundary when calculating grid limits

    note: n_grids = 10 will return 100 unique grid points, so it will create 11x11 lines in order to
    return a 10x10 grid

    input

    df: should be a pandas DataFrame with addresses, longitude and lattitude values
    n_grids: the number of grids on 1 side of the final desired grid (n x n)

    returns the input dataframe with the added 'assigned_grid' column
    '''

    # create -1 column which will be filled
    df['gridX'] = -1
    df['gridY'] = -1

    # create grid arrays
    xgrids = np.linspace(df['long'].min(), df['long'].max(), n_grids + 1)
    ygrids = np.linspace(df['lat'].min(), df['lat'].max(), n_grids + 1)

    for xinx, xgrid in enumerate(xgrids[:-1]):
        bool1 = (df['long'] >= xgrid) & (df['long'] < xgrids[xinx + 1])
        df.loc[bool1, 'gridX'] = xinx
    for yinx, ygrid in enumerate(ygrids[:-1]):
        bool1 = (df['lat'] >= ygrid) & (df['lat'] < ygrids[yinx + 1])
        df.loc[bool1, 'gridY'] = yinx

    # assigns string column for easy human viewing
    df['grid'] = "[" + df['gridX'].astype(str) + "," + df['gridY'].astype(str) + "]"
    return df


def adjacent_houses(house, houses):
    # Row/Column of the house
    row = houses.loc[house,]['gridX']
    column = houses.loc[house,]['gridY']

    # DF of adjacent houses
    df = pd.DataFrame(columns=houses.columns)
    for r in range(row - 1, row + 2):
        for c in range(column - 1, column + 1):
            df = df.append(houses[(houses['gridX'].values == r) & (houses['gridY'].values == c)])

    return df


def create_queries(houses):
    counter = 0
    n = len(houses)
    # Creating df to hold the queries
    queries = pd.DataFrame(columns={'start', 'end'})
    for house in houses.iterrows():
        adjacentHouses = adjacent_houses(house[0], houses).index.tolist()
        start = [house[0] for i in range(len(adjacentHouses))]
        print(len(adjacentHouses))
        queries = queries.append({'start': start, 'end': adjacentHouses}, ignore_index=True)
        break
        # for adjacentHouse in adjacentHouses.iterrows():
        #     queries = queries.append({'start':house[0],'end':adjacentHouse[0]}, ignore_index=True)

        counter = counter + 1
        print(counter)
        if counter % 100 == 0:
            print('Percentage Complete: ',100*counter/n,'%',sep='')
    return queries


def main():
    df = pd.read_csv('poco-extract-long-lat.csv', index_col=0)

    inx = df.loc['NO ADDRESS, Port Coquitlam, BC, Canada', :].index
    df.drop(inx, inplace=True)

    df = assign_grids(df, 10)

    # Starting the recursion
    queries = create_queries(df)

    print(queries)


if __name__ == '__main__':
    main()
