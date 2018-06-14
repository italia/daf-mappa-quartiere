import numpy as np
import pandas as pd
import googlemaps
from os import path

## TODO: find way to put this into some global settings
import os
import sys
rootDir = os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from references import common_cfg

def append_geolocation_and_save(APIkey, origData, queryAddresses, targetFile):
                       
    gmaps = googlemaps.Client(key=APIkey)
    # Geocoding an address
    locationsFull = pd.Series.from_array([{}]*len(queryAddresses))
    # hardcoded coordinates format
    coordinates = pd.DataFrame([[np.nan, np.nan]] * len(queryAddresses),
                               columns=common_cfg.coord_col_names, index = origData.index)
    multipleResults = pd.Series.from_array([]*len(queryAddresses))

    for (i, address) in enumerate(queryAddresses):
        geocode_result = gmaps.geocode(address, components={'location':'Milano'})
        if geocode_result:
            assert isinstance(geocode_result, list) #check type
            if len(geocode_result) > 1: # multiple results, report first and
                multipleResults[i] = geocode_result

            # take first output
            locationsFull[i] = geocode_result[0]

        print(i)

    # save full responses
    import pickle
    pickle_out = open(targetFile + '_results.pickle',"wb")
    pickle.dump({'fullLoc': locationsFull, 'extraResults': multipleResults}, pickle_out)
    pickle_out.close()

    for i, locat in enumerate(locationsFull): ## if using pickle, run from here
        if not locat:
            continue
        thisLocation = locat['geometry']['location']
        coordinates[common_cfg.coord_col_names[0]][i] = thisLocation['lng']
        coordinates[common_cfg.coord_col_names[1]][i] = thisLocation['lat']
        print(coordinates.iloc[i,:])

    # append coordinates
    geolocData = pd.concat([origData, coordinates], axis=1)
    geolocData.to_csv(targetFile, sep=';', decimal=',')

    # print unidentified locations
    print(geolocData[geolocData.Lat.isnull()])