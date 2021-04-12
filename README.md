# GarbageTruckOptimization

This repository contains all the code used in the Optimization of the Routes of the Waste Collection Vehicles for the City of Port Coquitlam, BC, Canada.  Note, all underlying 
data has been permanently deleted in keeping with Google's terms of service.  As such the code cannot be run as it currently stands.  This repy was made public for anyone who
wishes to further undertake this project or similar, but they will have to generate their own data.

## Report.pdf

This document contains the written report that pertains to the project.

## dijkstra.py

This script excutes dikjstra's algorithm on multiple concurrent threads that calculates the complete time matrix used in the optimization model.'

## Dijkstra.py

This script is an example implementaion of dijkstra's algorithm that we wrote to validate our findings.

## directions.ipynb

This workbook parses the directions returned from google maps into the complete list of directions in tableau format.

## distanceMatrix.ipynb

This workbook creates the distance matrix to use in the model.

## google.py

This script makes requests to the Google Directions API using concurrent threads.

## google-query-to-tableau.py

This script converts the results from the Google Directions API into a form usable in Tableau

## poco-grid.ipynb

This script converts the longitude and latitudes in Port Coquitlam into a grid to reduce the number of queries needed for the Google Directions API.

## regrids.ipynb

This script is an adjusted version of above.

## time inflation.ipynb

This workbook inflates the travel times between even/odd addresses on the same street

## vehicle_routing.py

This script executes the optimization model.



