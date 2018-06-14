import numpy as np
import pandas as pd
import googlemaps
import pickle
import os
import sys

from references import common_cfg

# TODO: find way to put this into some global settings
rootDir = os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)


def append_geolocation_and_save(
        api_key, orig_data, query_addresses, target_file):

    gmaps = googlemaps.Client(key=api_key)
    # Geocoding an address
    locations_full = pd.Series.from_array([{}] * len(query_addresses))
    # hardcoded coordinates format
    coordinates = pd.DataFrame([[np.nan, np.nan]] * len(query_addresses),
                               columns=common_cfg.coord_col_names,
                               index=orig_data.index)
    multiple_results = pd.Series.from_array([] * len(query_addresses))

    for (i, address) in enumerate(query_addresses):
        geocode_result = gmaps.geocode(address)  # components={'location':CITY}
        if geocode_result:
            assert isinstance(geocode_result, list), 'Unexpected type'
            if len(geocode_result) > 1:  # multiple results, report first and
                multiple_results[i] = geocode_result

            # take first output
            locations_full[i] = geocode_result[0]

        print(i)

    # save full responses

    pickle_out = open(target_file + '_results.pickle', "wb")
    pickle.dump({'fullLoc': locations_full,
                 'extraResults': multiple_results}, pickle_out)
    pickle_out.close()

    # if using pickle, resume from here (not implemented)
    for i, location in enumerate(locations_full):
        if not location:
            continue
        this_location = location['geometry']['location']
        coordinates[common_cfg.coord_col_names[0]][i] = this_location['lng']
        coordinates[common_cfg.coord_col_names[1]][i] = this_location['lat']
        print(coordinates.iloc[i, :])

    # append coordinates
    geoloc_data = pd.concat([orig_data, coordinates], axis=1)
    geoloc_data.to_csv(target_file, sep=';', decimal=',')

    # print unidentified locations
    print(geoloc_data[geoloc_data.Lat.isnull()])
