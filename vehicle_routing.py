import multiprocessing as mp
import numpy as np
import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def create_data_model(timeMatrix, numVehicles, depot, timeWindows):
    """Stores the data for the problem."""
    data = {}
    data['time_matrix'] = timeMatrix.to_numpy()
    data['time_windows'] = timeWindows
    data['num_vehicles'] = numVehicles
    data['depot'] = depot
    return data


def print_solution(data, manager, routing, solution, processNumber):
    routes = {}
    """Prints solution on console."""
    time_dimension = routing.GetDimensionOrDie('Time')
    total_time = 0
    for vehicle_id in range(data['num_vehicles']):
        routes[vehicle_id] = pd.DataFrame(columns=['node', 'time'])
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            routes[vehicle_id] = routes[vehicle_id].append({'node': manager.IndexToNode(index), 'time': solution.Min(time_var)}, ignore_index=True)
            # plan_output += '{0} Time({1},{2}) -> '.format(
            #     manager.IndexToNode(index), solution.Min(time_var),
            #     solution.Max(time_var))
            index = solution.Value(routing.NextVar(index))
        time_var = time_dimension.CumulVar(index)
        routes[vehicle_id] = routes[vehicle_id].append({'node': manager.IndexToNode(index), 'time': solution.Min(time_var)}, ignore_index=True)
        # plan_output += '{0} Time({1},{2})\n'.format(manager.IndexToNode(index),
        #                                             solution.Min(time_var),
        #                                             solution.Max(time_var))
        plan_output += 'Time of the route: {}min\n'.format(
            solution.Min(time_var))
        print('Process:', processNumber, 'vehicle:', vehicle_id, solution.Min(time_var))
        #         print(plan_output)
        total_time += solution.Min(time_var)
    print('Process:', processNumber, 'total time of all routes: {}min'.format(total_time))
    return routes


def solver_status(status):
    if status == 0:
        return 'ROUTING_NOT_SOLVED: Problem not solved yet'
    elif status == 1:
        return 'ROUTING_SUCCESS: Problem solved successfully'
    elif status == 2:
        return 'ROUTING_FAIL: No solution found to the problem'
    elif status == 3:
        return 'ROUTING_FAIL_TIMEOUT: Time limit reached before finding a solution'
    elif status == 4:
        return 'ROUTING_INVALID: Model, model parameters, or flags are not valid'
    else:
        return "Unknown Status"


def route_names(routes, locations):
    namedRoutes = {}
    times = {}
    for vehicle in routes.keys():
        namedRoutes[vehicle] = locations[list(routes[vehicle]['node'].values)]
        times[vehicle] = routes[vehicle]['time'].values
    return namedRoutes, times


def tableau_route(routes, locations, timeMatrixFiltered):
    namedRoutes, times = route_names(routes, timeMatrixFiltered.index)

    tableauRoutes = pd.DataFrame(columns={'address', 'latitude', 'longitude', 'pairID', 'vehicleID', 'time'})
    for vehicle in namedRoutes.keys():
        for vertex in range(len(namedRoutes[vehicle]) - 1):
            currentVertexInfo = locations[locations.index == namedRoutes[vehicle][vertex]]
            currentVertexTime = times[vehicle][vertex]
            currentVertex = {'address': currentVertexInfo.index[0],
                             'latitude': currentVertexInfo['lat'].values[0],
                             'longitude': currentVertexInfo['long'].values[0],
                             'pairID': vertex,
                             'vehicleID': vehicle,
                             'time': currentVertexTime}

            nextVertexInfo = locations[locations.index == namedRoutes[vehicle][vertex + 1]]
            nextVertexTime = times[vehicle][vertex + 1]

            nextVertex = {'address': nextVertexInfo.index[0],
                          'latitude': nextVertexInfo['lat'].values[0],
                          'longitude': nextVertexInfo['long'].values[0],
                          'pairID': vertex,
                          'vehicleID': vehicle,
                          'time': nextVertexTime}

            tableauRoutes = tableauRoutes.append([currentVertex, nextVertex], ignore_index=True)
    return tableauRoutes


def time_windows(zone, timeMatrixFiltered, maxTimeWindow):
    timeWindows = []
    if zone == 1:
        for i in range(len(timeMatrixFiltered)):
            house = timeMatrixFiltered.index[i].split(' ')
            street = ' '.join(house[1:-4])

            if street == 'LINCOLN AVE,':
                timeWindows.append((0, maxTimeWindow))
            else:
                timeWindows.append((0, 50000))

    if zone == 2:
        for i in range(len(timeMatrixFiltered)):
            house = timeMatrixFiltered.index[i].split(' ')
            street = ' '.join(house[1:-4])

            if street == 'OXFORD ST,' or street == 'CHALMERS AVE,':
                timeWindows.append((0, maxTimeWindow))
            else:
                timeWindows.append((0, 50000))

    if zone == 3 or zone == 4 or zone == 5:
        for i in range(len(timeMatrixFiltered)):
            house = timeMatrixFiltered.index[i].split(' ')
            street = ' '.join(house[1:-4])

            timeWindows.append((0, 50000))



    return timeWindows


def create_route(timeMatrixFiltered, numVehicles, depotLocation, routeLimit, locations, processNumber, zone, maxTimeWindow):
    # CITATION: https://developers.google.com/optimization/routing/vrp
    """Solve the CVRP problem."""
    print("In thread", processNumber)
    # Instantiate the data problem.

    # Creating the time windows
    timeWindows = time_windows(zone, timeMatrixFiltered, maxTimeWindow)

    # data = create_data_model(timeMatrixFiltered, numVehicles, depotLocation)
    data = create_data_model(timeMatrixFiltered, numVehicles, int(depotLocation), timeWindows)
    # For some reason you have to make depotLocation an int, otherwise it throws an error

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def time_callback(from_index, to_index):
        """Returns the travel time between the two nodes."""
        # Convert from routing variable Index to time matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['time_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Time Windows constraint.
    time = 'Time'
    routing.AddDimension(
        transit_callback_index,
        30,  # allow waiting time
        routeLimit,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        time)
    time_dimension = routing.GetDimensionOrDie(time)

    # Add time window constraints for each location except depot.
    for location_idx, time_window in enumerate(data['time_windows']):
        if location_idx == data['depot']:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
    # Add time window constraints for each vehicle start node.
    depot_idx = data['depot']
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(
            data['time_windows'][depot_idx][0],
            data['time_windows'][depot_idx][1])

    # Instantiate route start and end times to produce feasible times.
    for i in range(data['num_vehicles']):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i)))
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.End(i)))

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.SAVINGS)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC)

    search_parameters.time_limit.seconds = 600

    # search_parameters.solution_limit = 1

    # Solve the problem.
    print(f"Process: {processNumber}, starting")
    solution = routing.SolveWithParameters(search_parameters)
    print(f"Process: {processNumber}, Solver status:", solver_status(routing.status()))

    # Extracting the routes
    print(f"Process: {processNumber}, extracting the routes")
    routes = print_solution(data, manager, routing, solution, processNumber)

    print(f"Process: {processNumber}, creating tableau routes")
    tableauRoute = tableau_route(routes, locations, timeMatrixFiltered)

    print(f"Process: {processNumber}, saving: ")
    tableauRoute.to_csv(f"C:/Users/Aidan/OneDrive - Simon Fraser University (1sfu)/Garbage Route Optimization/routes/zone{zone}_{numVehicles}trucks.csv")


def main():
    # Number of processes
    numProcesses = 5

    # Reading in time matrix
    print("Reading in time matrix")
    # timeMatrix = pd.read_csv('C:/Users/Aidan/OneDrive - Simon Fraser University (1sfu)/Garbage Route Optimization/timeMatrixInflated.csv',
    #                          index_col=0)

    timeMatrix = pd.read_csv('C:/Users/Aidan/OneDrive - Simon Fraser University (1sfu)/Garbage Route Optimization/timeMatrix.csv',
                             index_col=0)
    timeMatrix = timeMatrix.iloc[timeMatrix.index != 'NO ADDRESS, Port Coquitlam, BC, Canada', timeMatrix.index != 'NO ADDRESS, Port Coquitlam, BC, Canada']  # Removing the pesky no address

    # Reading in locations by zones
    print("Reading in locations by zone")
    locationsByZones = pd.read_csv('C:/Users/Aidan/OneDrive - Simon Fraser University (1sfu)/Garbage Route Optimization/poco-allzones.csv', index_col=0)
    locationsByZones.index = locationsByZones.index + ', Port Coquitlam, BC, Canada'  # Adding this so the addresses match the time matrix

    # Reading in all locations
    print("Reading in locations")
    locations = pd.read_csv('C:/Users/Aidan/OneDrive - Simon Fraser University (1sfu)/Garbage Route Optimization/locations_updated.csv', index_col=0)
    locations = locations[locations.index != 'NO ADDRESS, Port Coquitlam, BC, Canada']  # Removing the pesky no address

    print('Dividing up the time matrix by zone')
    # Dividing up the time matrix by zone
    timeMatrixFiltered = {}  # Contains the time matrix
    depotLocations = {}  # Contains the depot location in each subdivided time matrix
    timeWindows = {}
    for zone in [1, 2, 3, 4, 5]:
    # for zone in [1]:
        # Creating a row just for the depot
        depot = pd.Series({'Garbage Zone': np.float64(zone)}, name='1737 Broadway St Port Coquitlam, BC, Canada')

        # Filtering locations by zone
        locationsByZonesFiltered = locationsByZones[(locationsByZones['Garbage Zone'] == zone)]

        # Adding in depot
        locationsByZonesFiltered = locationsByZonesFiltered.append(depot)

        # Filtering the time matrix by zone and storing them separately in a dictionary
        timeMatrixFiltered[zone] = timeMatrix.iloc[timeMatrix.index.isin(locationsByZonesFiltered.index),
                                                   timeMatrix.index.isin(locationsByZonesFiltered.index)]

        # # ******** Delete this ************
        # # elements = list(range(0, len(timeMatrixFiltered)))
        # elements = list(range(0, 30))
        # elements.append(1966)
        # timeMatrixFiltered[zone] = timeMatrixFiltered[zone].iloc[elements, elements]

        # Storing the location of the depot in each subdivided time matrix in a dict
        depotLocations[zone] = np.where(timeMatrixFiltered[zone].index == '1737 Broadway St Port Coquitlam, BC, Canada')[0][0]

    # Creating jobs that need to be completed
    # jobs = [{'zone': 1, 'numTrucks': 3, 'limit': 6900, 'maxTimeWindow': 5400},
    #         {'zone': 1, 'numTrucks': 4, 'limit': 5325, 'maxTimeWindow': 3600},
    #         {'zone': 1, 'numTrucks': 5, 'limit': 4500, 'maxTimeWindow': 3600},
    #         {'zone': 1, 'numTrucks': 6, 'limit': 3900, 'maxTimeWindow': 3600},
    #         {'zone': 1, 'numTrucks': 7, 'limit': 3500, 'maxTimeWindow': 3600}]

    jobs = [{'zone': 1, 'numTrucks': 3, 'limit': 5400, 'maxTimeWindow': 5400},
            {'zone': 1, 'numTrucks': 4, 'limit': 5000, 'maxTimeWindow': 3600},
            {'zone': 1, 'numTrucks': 5, 'limit': 4000, 'maxTimeWindow': 3600},
            {'zone': 1, 'numTrucks': 6, 'limit': 3300, 'maxTimeWindow': 3600}, #
            {'zone': 1, 'numTrucks': 7, 'limit': 2800, 'maxTimeWindow': 3600}] #

    # jobs = [{'zone': 2, 'numTrucks': 3, 'limit': 7000, 'maxTimeWindow': 10000},  # USE .PATH_CHEAPEST_ARC for all of zone 2
    #         {'zone': 2, 'numTrucks': 4, 'limit': 5400, 'maxTimeWindow': 10000},
    #         {'zone': 2, 'numTrucks': 5, 'limit': 4500, 'maxTimeWindow': 3600},#
    #         {'zone': 2, 'numTrucks': 6, 'limit': 4000, 'maxTimeWindow': 3600}, #
    #         {'zone': 2, 'numTrucks': 7, 'limit': 3500, 'maxTimeWindow': 3600}] #

    # jobs = [{'zone': 3, 'numTrucks': 3, 'limit': 6300, 'maxTimeWindow': 10000}, #
    #         {'zone': 3, 'numTrucks': 4, 'limit': 5000, 'maxTimeWindow': 10000}, #
    #         {'zone': 3, 'numTrucks': 5, 'limit': 4000, 'maxTimeWindow': 10000}, #
    #         {'zone': 3, 'numTrucks': 6, 'limit': 3700, 'maxTimeWindow': 10000}, # USE .PATH_CHEAPEST_ARC for num trucks 6 and 7
    #         {'zone': 3, 'numTrucks': 7, 'limit': 3500, 'maxTimeWindow': 10000}]

    # jobs = [{'zone': 4, 'numTrucks': 3, 'limit': 5600, 'maxTimeWindow': 10000},
    #         {'zone': 4, 'numTrucks': 4, 'limit': 4375, 'maxTimeWindow': 10000},
    #         {'zone': 4, 'numTrucks': 5, 'limit': 3600, 'maxTimeWindow': 10000},
    #         {'zone': 4, 'numTrucks': 6, 'limit': 3125, 'maxTimeWindow': 10000},
    #         {'zone': 4, 'numTrucks': 7, 'limit': 2750, 'maxTimeWindow': 10000}]

    # jobs = [{'zone': 5, 'numTrucks': 3, 'limit': 4500, 'maxTimeWindow': 10000},
    #         {'zone': 5, 'numTrucks': 4, 'limit': 3400, 'maxTimeWindow': 10000}, #
    #         {'zone': 5, 'numTrucks': 5, 'limit': 2800, 'maxTimeWindow': 10000}, #
    #         {'zone': 5, 'numTrucks': 6, 'limit': 2500, 'maxTimeWindow': 10000}, #
    #         {'zone': 5, 'numTrucks': 7, 'limit': 2100, 'maxTimeWindow': 10000}] #


    print("Defining threads")
    processes = []
    # Defining the threads
    for process in range(0, numProcesses):
        job = jobs[process]
        processes.append(
            mp.Process(target=create_route,
                       args=(timeMatrixFiltered[job['zone']],
                             job['numTrucks'],
                             depotLocations[job['zone']],
                             job['limit'],
                             locations,
                             process,
                             job['zone'],
                             job['maxTimeWindow']
                             )
                       )
        )
    print('Starting the threads')
    # Starting the threads
    for process in range(0, numProcesses):
        processes[process].start()

    print('Joining the threads')
    # Joining the threads
    for process in range(0, numProcesses):
        processes[process].join()


if __name__ == '__main__':
    main()
