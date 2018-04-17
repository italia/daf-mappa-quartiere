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

from src.models.city_items import AgeGroup
from src.models.process_tools import MappedPositionsFrame

gaussKern = gaussian_process.kernels.RBF

### Demand modeling
class DemandUnit:
    def __init__(self, name, position, agesIn, attributesIn={}):
        assert isinstance(name, (str, np.int64)), 'Name must be string or int64'
        assert isinstance(agesIn, dict), 'AgesInput should be a dict'
        assert set(agesIn.keys()) <= set(AgeGroup.all()), 'Ages input keys should be AgeGroups'
        assert isinstance(position, geopy.Point), 'Position must be a geopy Point'
        assert isinstance(attributesIn, dict), 'Attributes can be provided in a dict'
        
        # expand input to all age group keys and assign default 0 to missing ones
        self.ages = {a: agesIn.get(a, 0) for a in AgeGroup.all()}
        self.name = name
        self.position = position
        self.polygon = attributesIn.get('geometry', [])
        self.attributes = attributesIn
        # precompute export format for speed
        unitIndex = [[attributesIn.get(common_cfg.IdQuartiereColName, np.nan)],\
                     [tuple(self.position)]]
     
        self.export = pd.DataFrame(self.ages, index = pd.MultiIndex.from_tuples(
                               [(attributesIn.get(common_cfg.IdQuartiereColName, np.nan), tuple(self.position))],
                               names=[common_cfg.IdQuartiereColName, common_cfg.tupleIndexName]))
        
    @property
    def totalPeople(self):
        return sum(self.ages.values())
    
## Factory class
class DemandUnitFactory:
    '''
    A class to istantiate DemandUnits
    '''
    def __init__(self, cityNameIn):
        assert cityNameIn in common_cfg.cityList, 'Unrecognised city name "%s"' % cityNameIn
        self.data = common_cfg.get_istat_cpa_data(cityNameIn)
        self.nSections = self.data.shape[0]
        self.unitList = [] # initialise
        
        # prepare the AgeGroups cardinalities
        groupsCol = 'ageGroup'
        peopleBySampleAge = common_cfg.fill_sample_ages_in_cpa_columns(self.data)
        dataByGroup = peopleBySampleAge.rename(AgeGroup.find_AgeGroup, axis='columns').T
        dataByGroup.index.name = groupsCol # index is now given by AgeGroup items
        dataByGroup = dataByGroup.reset_index() # extract to convert to categorical and groupby
        dataByGroup[groupsCol] = dataByGroup[groupsCol].astype('category')
        # finally assign in dict form where data.index are the keys
        self.peopleByGroup = dataByGroup.groupby(groupsCol).sum().to_dict()
        
    def make_units_at_centroids(self):
        unitList = []
        positionList = []
        # make units
        for iUnit in range(self.nSections):
            rowData = self.data.iloc[iUnit,:]
            sezId = self.data.index[iUnit]
            attrDict = {'geometry':rowData['geometry'], 
                        common_cfg.IdQuartiereColName: rowData[common_cfg.IdQuartiereColName]}
            # get polygon centroid and use that as position
            sezCentroid =rowData['geometry'].centroid
            sezPosition = geopy.Point(sezCentroid.y, sezCentroid.x)
            
            # check no location is repeated
            assert not any([x==sezPosition for x in positionList]), 'Repeated position found'
            positionList.append(sezPosition)
            
            thisUnit = DemandUnit(name=sezId, 
                        position=sezPosition, 
                        agesIn=self.peopleByGroup[sezId], 
                        attributesIn=attrDict)
            
            unitList.append(thisUnit)
        print('Imported a total population of %i' % sum([t.totalPeople for t in unitList]))
        self.unitList = unitList
        
        return unitList
  
    def export_mapped_positions(self):
        '''Get mapped positions for the computed list of DemandUnits'''
        
        assert self.unitList, 'Units not available, have you made them?'
        # initialise export
        mappedPositionsOut = MappedPositionsFrame(
            positions = [u.position for u in self.unitList],
            idQuartiere= [u.attributes.get(
                common_cfg.IdQuartiereColName, [np.nan]) for u in self.unitList])
            
        return mappedPositionsOut