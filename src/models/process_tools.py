from enum import Enum
import os.path

import numpy as np
import pandas as pd
import geopandas as gpd
import geopy, geopy.distance
import shapely
from sklearn import gaussian_process

## TODO: find way to put this into some global settings
import os
import sys
rootDir = os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from references import common_cfg
from src.models.city_items import AgeGroup, ServiceArea, ServiceType, SummaryNorm # enum classes for the model


gaussKern = gaussian_process.kernels.RBF
# useful conversion function 
make_shapely_point = lambda geoPoint: shapely.geometry.Point((geoPoint.longitude, geoPoint.latitude))
# test utility
get_random_pos = lambda n: list(map(geopy.Point, list(zip(np.round(np.random.uniform(45.40, 45.50, n), 5), 
                                np.round(np.random.uniform(9.1, 9.3, n), 5)))))

## Mapped positions frame class
class MappedPositionsFrame(pd.DataFrame):
    '''A class to collect an array of positions alongside areas labels'''

    def __init__(self, idQuartiere, long=None, lat=None, positions=None):
      
        if not positions:
            # create mapping dict from coordinates
            mappingDict = {
                common_cfg.coordColNames[0]:long, #long
                common_cfg.coordColNames[1]:lat, #lat
                common_cfg.IdQuartiereColName: idQuartiere,    #quartiere aggregation
                            }
            #istantiate geopy positions
            geopyPoints = list(map(lambda y,x: geopy.Point(y,x), lat, long))
            mappingDict['Positions'] = geopyPoints
            
        else:
            assert all([isinstance(t, geopy.Point) for t in positionsIn]),'Geopy Points expected'
            assert not long, 'Long input not expected if positions provided'
            assert not lat, 'Lat input not expected if positions provided'
            mappingDict = {
                common_cfg.coordColNames[0]: [x.longitude for x in positions], #long
                common_cfg.coordColNames[1]: [x.latitude for x in positions], #lat
                common_cfg.IdQuartiereColName: idQuartiere,    #quartiere aggregation
                'Positions': positions
                            }
        
        # finally call DataFrame constructor
        super().__init__(mappingDict)
        
## Grid maker
class GridMaker():
    '''
    A class to create a grid and map it to various given land subdivisions
    '''
    def __init__(self, cityGeoFilesDict, gridStep=0.1): #gridStep in km
        self.quartiereKey = 'quartieri' #hardcoded
        
        # load division geofiles with geopandas
        self.subdivisions = {}
        for name, fileName in cityGeoFilesDict.items():
            self.subdivisions[name] = gpd.read_file(fileName)
        
        # compute city boundary
        self.cityBoundary = shapely.ops.cascaded_union(self.subdivisions[self.quartiereKey]['geometry'])
        
        # precompute coordinate ranges
        self.longRange = (self.cityBoundary.bounds[0], self.cityBoundary.bounds[2])
        self.latRange = (self.cityBoundary.bounds[1], self.cityBoundary.bounds[3])
        self.longNGrid = int(self.longitudeRangeKm // gridStep)+1
        self.latNGrid = int(self.latitudeRangeKm // gridStep)+1
        
        (self.xPlot, self.yPlot) = np.meshgrid(np.linspace(*self.longRange, self.longNGrid),
                                     np.linspace(*self.latRange, self.latNGrid), indexing='ij')
        
        # construct point objects with same shape
        self.bInPerimeter = np.empty_like(self.xPlot, dtype=bool)
        self.IDquartiere = np.empty_like(self.xPlot, dtype=object)
        
        for (i,j),_ in np.ndenumerate(self.bInPerimeter):
            shplyPoint = shapely.geometry.Point((self.xPlot[i,j], self.yPlot[i,j]))
            # mark points outside boundaries
            self.bInPerimeter[i,j] = self.cityBoundary.contains(shplyPoint)
            if self.bInPerimeter[i,j]:
                bFound = False
                for iRow in range(self.subdivisions[self.quartiereKey].shape[0]):
                    thisQuartierePolygon = self.subdivisions[self.quartiereKey]['geometry'][iRow]
                    if thisQuartierePolygon.contains(shplyPoint):
                        # assign found ID
                        self.IDquartiere[i,j] = self.subdivisions[
                            self.quartiereKey][common_cfg.IdQuartiereColName][iRow]
                        bFound = True
                        break # skip remanining zones
                assert bFound, 'Point within city boundary was not assigned to any zone'
        
        # initialise mapping dict
        mappingDict = {
            common_cfg.coordColNames[0]:self.xPlot[self.bInPerimeter].flatten(), #long
            common_cfg.coordColNames[1]:self.yPlot[self.bInPerimeter].flatten(), #lat
            common_cfg.IdQuartiereColName: self.IDquartiere[self.bInPerimeter],       #quartiere aggregation
                        } 
        # call common format constructor
        self.mappedPositions = MappedPositionsFrame(long=self.xPlot[self.bInPerimeter].flatten(),
                                                   lat=self.yPlot[self.bInPerimeter].flatten(),
                                                   idQuartiere=self.IDquartiere[self.bInPerimeter]
                                                   )
        
    @property
    def longitudeRangeKm(self):
        return geopy.distance.great_circle(
            (self.latRange[0], self.longRange[0]), (self.latRange[0], self.longRange[1])).km
    @property
    def latitudeRangeKm(self):
        return geopy.distance.great_circle(
            (self.latRange[0], self.longRange[0]), (self.latRange[1], self.longRange[0])).km    