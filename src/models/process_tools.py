
import numpy as np
import pandas as pd
import geopandas as gpd
import geopy, geopy.distance
import shapely
from sklearn import gaussian_process

from matplotlib import pyplot as plt 
import seaborn as sns
from scipy.interpolate import griddata
import json

## TODO: find way to put this into some global settings
import os
import sys
rootDir = os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

plt.rcParams['figure.figsize']= (20,14)

from references import common_cfg
from src.models.city_items import AgeGroup, ServiceArea, ServiceType, SummaryNorm # enum classes for the model
from src.models.core import ServiceValues, MappedPositionsFrame, KPICalculator
        
        
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

            xPlot, yPlot, z = self.values.plot_output(servType, ageGroup)

            if (~all(np.isnan(z))) & (np.count_nonzero(z)>0):
                if self.bOnGrid:
                    gridShape = (len(set(xPlot)), len(set(yPlot.flatten())))
                    assert len(xPlot) == gridShape[0] * gridShape[
                        1], 'X values do not seem on a grid'
                    assert len(yPlot) == gridShape[0] * gridShape[
                        1], 'Y values do not seem on a grid'
                    xi = np.array(xPlot).reshape(gridShape)
                    yi = np.array(yPlot).reshape(gridShape)
                    zi = z.reshape(gridShape)
                else:
                    # grid the data using natural neighbour interpolation
                    xi = np.linspace(min(xPlot), max(xPlot), gridDensity)
                    yi = np.linspace(min(yPlot), max(yPlot), gridDensity)
                    zi = griddata((xPlot, yPlot), z, (xi[None, :], yi[:, None]), 'nearest')

                plt.figure()
                plt.title(ageGroup)
                CS = plt.contourf(xi, yi, zi, nLevels)
                cbar = plt.colorbar(CS)
                cbar.ax.set_ylabel('Service level')
                plt.show()

        return None

class JSONWriter:
    def __init__(self, kpiCalc):
        assert isinstance(kpiCalc, KPICalculator), 'KPI calculator is needed'
        self.layersData = kpiCalc.quartiereKPI
        self.istatData = kpiCalc.istatKPI
        self.city = kpiCalc.city
        self.areasTree = {}
        for s in self.layersData:
            area = s.serviceArea
            self.areasTree[area] = [s] + self.areasTree.get(area, [])

    def make_menu(self):
        jsonList = common_cfg.make_output_menu(self.city,
                                               services=list(self.layersData.keys()))
        return jsonList

    def make_serviceareas_output(self, precision=4):
        out = dict()

        # make istat layer
        istatFrame = self.istatData.round(precision)
        origType = istatFrame.index.dtype.type
        dataIstat = istatFrame.reset_index().to_dict(orient='records')
        # restore type as pandas has a bug and casts to float if int
        for quartiereData in dataIstat:
            oldValue = quartiereData[common_cfg.IdQuartiereColName]
            if origType in (np.int32, np.int64, int):
                quartiereData[common_cfg.IdQuartiereColName] = int(oldValue)
        out[common_cfg.istatLayerName] = dataIstat

        # make layers
        for area, layers in self.areasTree.items():
            layerList = []
            for service in layers:
                data = self.layersData[service].round(precision)
                layerList.append(pd.Series(
                    data[AgeGroup.all()].as_matrix().tolist(),
                    index=data.index, name=service.name))
            areaData = pd.concat(layerList, axis=1).reset_index()
            print(areaData)
            out[area.value] = areaData.to_dict(orient='records')
        return out

    def write_all_files_to_default_path(self):
        # build and write menu
        with open(os.path.join(
                '../', common_cfg.vizOutputPath, 'menu.js'), 'w') as menuFile:
            json.dump(self.make_menu(), menuFile, sort_keys=True,
                      indent=4, separators=(',', ' : '))

        # build and write all areas
        areasOutput = self.make_serviceareas_output()
        for name, data in areasOutput.items():
            filename = '%s_%s.js' % (self.city, name)
            with open(os.path.join('../', common_cfg.outputPath,
                                   filename), 'w') as areaFile:
                json.dump(data, areaFile, sort_keys=True,
                          indent=4, separators=(',', ' : '))