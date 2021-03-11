import multiprocessing as mp
import numpy as np
import pandas as pd
import time
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def create_data_model(df, numVehicles, depotLocation):
    """Stores the data for the problem."""
    data = {'distance_matrix': df.to_numpy(), 'num_vehicles': numVehicles, 'depot': depotLocation}
    return data


def print_solution(data, manager, routing, solution,processNumber):
    # CITATION: https://developers.google.com/optimization/routing/vrp
    routes = {}
    """Prints solution on console."""
    max_route_distance = 0
    for vehicle_id in range(data['num_vehicles']):
        routes[vehicle_id] = []
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        while not routing.IsEnd(index):
            # plan_output += ' {} -> '.format(manager.IndexToNode(index))
            routes[vehicle_id].append(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        # plan_output += '{}\n'.format(manager.IndexToNode(index))
        routes[vehicle_id].append(manager.IndexToNode(index))
        plan_output += 'Distance of the route: {}s\n'.format(route_distance)
        print('Process:',processNumber, plan_output)
        max_route_distance = max(route_distance, max_route_distance)
    print('Maximum of the route distances: {}s'.format(max_route_distance))
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
    for vehicle in routes.keys():
        namedRoutes[vehicle] = locations[routes[vehicle]]
    return namedRoutes


def tableau_route(routes, locations, timeMatrixFiltered):
    namedRoutes = route_names(routes, timeMatrixFiltered.index)

    tableauRoutes = pd.DataFrame(columns={'address', 'latitude', 'longitude', 'pairID', 'vehicleID'})
    for vehicle in namedRoutes.keys():
        for vertex in range(len(namedRoutes[vehicle]) - 1):
            currentVertexInfo = locations[locations.index == namedRoutes[vehicle][vertex]]
            currentVertex = {'address': currentVertexInfo.index[0],
                             'latitude': currentVertexInfo['lat'].values[0],
                             'longitude': currentVertexInfo['long'].values[0],
                             'pairID': vertex,
                             'vehicleID': vehicle}

            nextVertexInfo = locations[locations.index == namedRoutes[vehicle][vertex + 1]]

            nextVertex = {'address': nextVertexInfo.index[0],
                          'latitude': nextVertexInfo['lat'].values[0],
                          'longitude': nextVertexInfo['long'].values[0],
                          'pairID': vertex,
                          'vehicleID': vehicle}

            tableauRoutes = tableauRoutes.append([currentVertex, nextVertex], ignore_index=True)
    return tableauRoutes


def create_route(timeMatrixFiltered, numVehicles, depotLocation, routeLimit, locations, processNumber, zone):
    # CITATION: https://developers.google.com/optimization/routing/vrp
    """Solve the CVRP problem."""
    print("In thread", processNumber)
    # Instantiate the data problem.
    # data = create_data_model(timeMatrixFiltered, numVehicles, depotLocation)
    data = create_data_model(timeMatrixFiltered, numVehicles, int(depotLocation))
    # For some reason you have to make depotLocation an int, otherwise it throws an error

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        routeLimit,  # vehicle maximum travel distance # 5000
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.SAVINGS)
    # search_parameters.local_search_metaheuristic = (
    #     routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC)

    search_parameters.time_limit.seconds = 300

    search_parameters.solution_limit = 1

    #     search_parameters.lns_time_limit.seconds = 1

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
    # tableauRoute.to_csv(f"zone{zone}_{numVehicles}trucks.csv")


def main():
    # Number of processes
    numProcesses = 5

    # Reading in time matrix
    print("Reading in time matrix")
    timeMatrix = pd.read_csv('C:/Users/Aidan/OneDrive - Simon Fraser University (1sfu)/Garbage Route Optimization/timeMatrixInflated.csv',
                             index_col=0)

    # Reading in locations by zones
    print("Reading in locations by zone")
    locationsByZones = pd.read_csv('C:/Users/Aidan/OneDrive - Simon Fraser University (1sfu)/Garbage Route Optimization/poco-allzones.csv', index_col=0)
    locationsByZones.index = locationsByZones.index + ', Port Coquitlam, BC, Canada'  # Adding this so the addresses match the time matrix

    # Reading in all locations
    print("Reading in locations")
    locations = pd.read_csv('C:/Users/Aidan/OneDrive - Simon Fraser University (1sfu)/Garbage Route Optimization/locations.csv', index_col=0)

    print('Dividing up the time matrix by zone')
    # Dividing up the time matrix by zone
    timeMatrixFiltered = {}  # Contains the time matrix
    depotLocations = {}  # Contains the depot location in each subdivided time matrix
    # for zone in [1, 2, 3, 4, 5]:
    for zone in [1]:
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

    print(depotLocations)

    # # Creating jobs that need to be completed
    # jobs = [{'zone': 4, 'numTrucks': 3, 'limit': 5600}, #
    #         {'zone': 4, 'numTrucks': 4, 'limit': 4375}, #
    #         {'zone': 4, 'numTrucks': 5, 'limit': 3600},
    #         {'zone': 4, 'numTrucks': 6, 'limit': 3125},
    #         {'zone': 4, 'numTrucks': 7, 'limit': 2750}] #
    # jobs = [{'zone': 1, 'numTrucks': 3, 'limit': 6900},
    #         {'zone': 1, 'numTrucks': 4, 'limit': 5325},
    #         {'zone': 1, 'numTrucks': 5, 'limit': 4500},
    #         {'zone': 1, 'numTrucks': 6, 'limit': 3900},
    #         {'zone': 1, 'numTrucks': 7, 'limit': 3500}]
    jobs = [{'zone': 2, 'numTrucks': 3, 'limit': 6900},
            {'zone': 2, 'numTrucks': 4, 'limit': 5325},
            {'zone': 2, 'numTrucks': 5, 'limit': 4500},
            {'zone': 2, 'numTrucks': 6, 'limit': 3900},
            {'zone': 2, 'numTrucks': 7, 'limit': 3500}]

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
                             job['zone']
                             )
                       )
        )
    print('Starting the threads')
    # Starting the threads
    for process in range(0, numProcesses):
        processes[process].start()

    print('Joning the threads')
    # Joining the threads
    for process in range(0, numProcesses):
        processes[process].join()


if __name__ == '__main__':
    main()
