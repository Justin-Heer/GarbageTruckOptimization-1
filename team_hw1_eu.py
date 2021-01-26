import pandas as pd
import googlemaps
from datetime import datetime, timedelta
from key import API_KEY

countries = ['Austria',
             'Belgium',
             'Bulgaria',
             'Croatia',
             'Czech Republic',
             'Denmark',
             'Estonia',
             'Finland',
             'France',
             'Germany',
             'Greece',
             'Hungary',
             'Italy',
             'Latvia',
             'Lithuania',
             'Luxembourg',
             'Netherlands',
             'Poland',
             'Portugal',
             'Romania',
             'Slovakia',
             'Slovenia',
             'Spain',
             'Sweden']
capitals = ['Vienna',
            'Brussels',
            'Sofia',
            'Zagreb',
            'Prague',
            'Copenhagen',
            'Tallinn',
            'Helsinki',
            'Paris',
            'Berlin',
            'Athens',
            'Budapest',
            'Rome',
            'Riga',
            'Vilnius',
            'Luxembourg (city)',
            'Amsterdam',
            'Warsar',
            'Lisbon',
            'Bucharest',
            'Bratislava',
            'Ljubljana',
            'Madrid',
            'Stockholm']

# Defining Dataframe
df = pd.DataFrame({'country': countries, 'capital': capitals})

# Authenticating with api
gmaps = googlemaps.Client(key=API_KEY())

# Querying google api to get addresses
addresses = []
latitude = []
longitude = []
for index, row in df.iterrows():
    results = gmaps.places(query=f"{row['capital']},{row['country']} city hall")
    latitude.append(results['results'][0]['geometry']['location']['lat'])
    longitude.append(results['results'][0]['geometry']['location']['lng'])
    addresses.append(results['results'][0]['formatted_address'])

df['address'] = addresses
df['lon'] = longitude
df['lat'] = latitude

print(df)

# Manually adding in a few addresses
df.iloc[1,]['address'] = 'Grand Place 1, 1000 Bruxelles, Belgium'
df.iloc[2,]['address'] = '33 Moskovska Str.Sofia 1000'
df.iloc[3,]['address'] = 'Town hall Zagreb, Trg Stjepana Radića 1, 10000, Zagreb, Croatia'
df.iloc[11,]['address'] = 'Budapest, Városház u. 9-11, 1052 Hungary'
df.iloc[13,]['address'] = 'Rātslaukums 1, Centra rajons, Rīga, LV-1050, Latvia'
df.iloc[15,]['address'] = '42 Place Guillaume II, 2090 Luxembourg'

print(df)
#
# # Querying the distances from google api
# distances = pd.DataFrame(columns=['from', 'to', 'distance'])
# now = datetime.now() + timedelta(hours=2)
# for i in range(0, df.count()['country']):
#     for j in range(0, df.count()['country']):
#         if i == j:
#             newRow = {'from': f"{df.iloc[i,]['capital']}, {df.iloc[i,]['country']}",
#                       'to': f"{df.iloc[j,]['capital']}, {df.iloc[j,]['country']}",
#                       'distance': 0}
#         else:
#             directions_result = gmaps.directions(df.iloc[i,]['address'],
#                                                  df.iloc[j,]['address'],
#                                                  mode="driving",
#                                                  departure_time=now)
#             newRow = {'from': f"{df.iloc[i,]['capital']}, {df.iloc[i,]['country']}",
#                       'to': f"{df.iloc[j,]['capital']}, {df.iloc[j,]['country']}",
#                       'distance': directions_result[0]['legs'][0]['distance']['value'] / 1000}
#         distances = distances.append(newRow, ignore_index=True)
#
# # Pivoting table to get the correct form
# distances = distances.pivot(index='from', columns='to', values='distance')
#
# # Saving data
# distances.to_csv('./distances.csv')
df.to_csv('./team_hw1_eu_capitals.csv', index=False)
