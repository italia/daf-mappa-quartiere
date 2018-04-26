from enum import Enum
import os.path

import numpy as np
import pandas as pd
import geopandas as gpd
import geopy, geopy.distance
import shapely
from sklearn import gaussian_process

from matplotlib import pyplot as plt 
import seaborn as sns
plt.rcParams['figure.figsize']= (20,14)

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

    def __init__(self, positions=None, long=None, lat=None, idQuartiere=None):
        
        # build positions data
        if not positions:
            if idQuartiere is None:
                idQuartiere = np.full(long.shape, np.nan)
            # create mapping dict from coordinates
            mappingDict = {
                common_cfg.coordColNames[0]:long, #long
                common_cfg.coordColNames[1]:lat, #lat
                common_cfg.IdQuartiereColName: idQuartiere,    #quartiere aggregation
                            }
            # istantiate geopy positions
            geopyPoints = list(map(lambda y,x: geopy.Point(y,x), lat, long))
            mappingDict[common_cfg.positionsCol] = geopyPoints
            mappingDict[common_cfg.tupleIndexName] = [tuple(p) for p in geopyPoints] 
            
        else:
            assert all([isinstance(t, geopy.Point) for t in positions]),'Geopy Points expected'
            assert not long, 'Long input not expected if positions provided'
            assert not lat, 'Lat input not expected if positions provided'
            if idQuartiere is None:
                idQuartiere = np.full(len(positions), np.nan)
            # create mapping dict from positions    
            mappingDict = {
                common_cfg.coordColNames[0]: [x.longitude for x in positions], #long
                common_cfg.coordColNames[1]: [x.latitude for x in positions], #lat
                common_cfg.IdQuartiereColName: idQuartiere,    #quartiere aggregation
                common_cfg.positionsCol: positions, 
                common_cfg.tupleIndexName: [tuple(p) for p in positions]}
        
        # finally call DataFrame constructor
        super().__init__(mappingDict)
        self.set_index([common_cfg.IdQuartiereColName, common_cfg.tupleIndexName], inplace=True)
        

class ServiceValues(dict):
    '''A class to store, make available for aggregation and easily export estimated service values'''
    
    def __init__(self, mappedPositions):
        assert isinstance(mappedPositions, MappedPositionsFrame), 'Expected MappedPositionsFrame'
        self.mappedPositions = mappedPositions
        
        # initialise for all service types
        super().__init__({service: pd.DataFrame(
            np.zeros([mappedPositions.shape[0], len(AgeGroup.all())]),  
            index=mappedPositions.index, columns=AgeGroup.all()) 
                            for service in ServiceType})
        
    def plot_output(self, servType, ageGroup):
        '''Make output for plotting for a given serviceType and ageGroup'''
        # extract values
        valuesSeries = self[servType][ageGroup]
        # TODO: this is quite inefficient though still fast, optimise it
        joined = pd.concat([valuesSeries,self.mappedPositions], axis=1)

        # format output as (x,y,z) surface
        z = valuesSeries.values
        x = joined[common_cfg.coordColNames[0]].values
        y = joined[common_cfg.coordColNames[1]].values
        return x,y,z
        
    @property     
    def positions(self): 
        return list(self.mappedPositions.Positions.values)
        
        
## Grid maker
class GridMaker():
    '''
    A class to create a grid and map it to various given land subdivisions
    '''
    def __init__(self, cityGeoFilesDict, gridStep=0.1): #gridStep in km
        
        self._quartiereKey = 'quartieri' #hardcoded
        
        # load division geofiles with geopandas
        self.subdivisions = {}
        for name, fileName in cityGeoFilesDict.items():
            self.subdivisions[name] = gpd.read_file(fileName)
        
        # compute city boundary
        self.cityBoundary = shapely.ops.cascaded_union(self.subdivisions[self._quartiereKey]['geometry'])
        
        # precompute coordinate ranges
        self.longRange = (self.cityBoundary.bounds[0], self.cityBoundary.bounds[2])
        self.latRange = (self.cityBoundary.bounds[1], self.cityBoundary.bounds[3])
        self.longNGrid = int(self.longitudeRangeKm // gridStep)+1
        self.latNGrid = int(self.latitudeRangeKm // gridStep)+1
        
        (self._xPlot, self._yPlot) = np.meshgrid(np.linspace(*self.longRange, self.longNGrid),
                                     np.linspace(*self.latRange, self.latNGrid), indexing='ij')
        
        # construct point objects with same shape
        self._bInPerimeter = np.empty_like(self._xPlot, dtype=bool)
        self._IDquartiere = np.empty_like(self._xPlot, dtype=object)
        
        for (i,j),_ in np.ndenumerate(self._bInPerimeter):
            shplyPoint = shapely.geometry.Point((self._xPlot[i,j], self._yPlot[i,j]))
            # mark points outside boundaries
            self._bInPerimeter[i,j] = self.cityBoundary.contains(shplyPoint)
            if self._bInPerimeter[i,j]:
                bFound = False
                for iRow in range(self.subdivisions[self._quartiereKey].shape[0]):
                    thisQuartierePolygon = self.subdivisions[self._quartiereKey]['geometry'][iRow]
                    if thisQuartierePolygon.contains(shplyPoint):
                        # assign found ID
                        self._IDquartiere[i,j] = self.subdivisions[
                            self._quartiereKey][common_cfg.IdQuartiereColName][iRow]
                        bFound = True
                        break # skip remanining zones
                assert bFound, 'Point within city boundary was not assigned to any zone'
            
            else: # assign default value for points outside city perimeter
                self._IDquartiere[i,j] = np.nan
                
        # call common format constructor
        self.grid = MappedPositionsFrame(long=self._xPlot[self._bInPerimeter].flatten(),
                                                   lat=self._yPlot[self._bInPerimeter].flatten(),
                                                   idQuartiere=self._IDquartiere[self._bInPerimeter].flatten())
        
        self.fullGrid = MappedPositionsFrame(long=self._xPlot.flatten(), lat=self._yPlot.flatten(),
                                                   idQuartiere=self._IDquartiere.flatten())
      
      
    @property
    def longitudeRangeKm(self):
        return geopy.distance.great_circle(
            (self.latRange[0], self.longRange[0]), (self.latRange[0], self.longRange[1])).km
    @property
    def latitudeRangeKm(self):
        return geopy.distance.great_circle(
            (self.latRange[0], self.longRange[0]), (self.latRange[1], self.longRange[0])).km

    
## Plot tools
from scipy.interpolate import griddata
                
class ValuesPlotter:
    '''
    A class that plots various types of output from ServiceValues
    '''
    def __init__(self, serviceValues, bOnGrid=False):
        assert isinstance(serviceValues, ServiceValues), 'ServiceValues class expected'
        self.values = serviceValues
        self.bOnGrid = bOnGrid
        
        
    def plot_locations(self):
        '''
        Plots the locations of the provided ServiceValues'
        '''
        coordNames = common_cfg.coordColNames
        plt.figure()
        plt.scatter(self.values.mappedPositions[coordNames[0]],
                    self.values.mappedPositions[coordNames[1]])
        plt.xlabel(coordNames[0])
        plt.ylabel(coordNames[1])
        plt.axis('equal')
        plt.show()
        return None
    
        
    def plot_service_levels(self, servType, gridDensity=40, nLevels=50):
        '''
        Plots a contour graph of the results for each ageGroup.
        '''
        assert isinstance(servType, ServiceType), 'ServiceType expected in input'
        
        for ageGroup in self.values[servType].keys():
            
            xPlot,yPlot,z = self.values.plot_output(servType, ageGroup)
            
            if np.count_nonzero(z) > 0:
                if self.bOnGrid:
                    gridShape = (len(set(xPlot)), len(set(yPlot.flatten())))
                    assert len(xPlot) == gridShape[0]*gridShape[1], 'X values do not seem on a grid'
                    assert len(yPlot) == gridShape[0]*gridShape[1], 'Y values do not seem on a grid'
                    xi = np.array(xPlot).reshape(gridShape)
                    yi = np.array(yPlot).reshape(gridShape)
                    zi = z.reshape(gridShape)
                else:
                    # grid the data using natural neighbour interpolation
                    xi = np.linspace(min(xPlot), max(xPlot), gridDensity)
                    yi = np.linspace(min(yPlot), max(yPlot), gridDensity)
                    zi = griddata((xPlot, yPlot), z, (xi[None,:], yi[:,None]), 'linear')
                    
                plt.figure()
                plt.title(ageGroup)
                CS = plt.contourf(xi, yi, zi, nLevels)
                cbar = plt.colorbar(CS)
                cbar.ax.set_ylabel('Service level')
                plt.show()
            
        return None