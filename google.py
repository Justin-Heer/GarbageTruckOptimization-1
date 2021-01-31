import googlemaps
from datetime import datetime, time
from key import API_KEY
import  time


# key.py contains a variable API_KEY that contains the key for google API.  See this page to create one https://developers.google.com/maps/documentation/geocoding/get-api-key and this one to get an account going https://developers.google.com/maps/gmp-get-started

# Authenticating with api
gmaps = googlemaps.Client(key=API_KEY)

now = datetime.now()
nineAM = datetime(2021, 1, 31, 9, 0, 0)
# We'll need to loop through all the addresses here

t0 = time.time()
directionsResult = gmaps.directions(origin='301 Stewardson Way, New Westminster, BC V3M 2A5',
                                    destination='771 Sixth St, New Westminster, BC V3L 3C6',
                                    mode="driving",
                                    departure_time=nineAM)
t1 = time.time()
bruteForceTime = t1 - t0
print(bruteForceTime)

print(directionsResult)
