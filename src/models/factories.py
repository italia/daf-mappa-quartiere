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
from src.models.process_tools import MappedPositionsFrame
from src.models.services_supply import ServiceUnit, ServiceEvaluator, ServiceValues

    
## UnitFactory father class
class UnitFactory:
    def __init__(self, path):
        assert os.path.isfile(path), 'File "%s" not found' % path
        self.filepath = path
        self.rawData = pd.DataFrame()
        
    def load_from_path(self):
           
        defaultLocationColumns = ['Lat', 'Long']
        if set(defaultLocationColumns).issubset(set(self.rawData.columns)):
            print('Location data found')
            # store geolocations as geopy Point
            locations = [geopy.Point(self.rawData.loc[i, defaultLocationColumns]) for i in range(self.nUnits)]
            propertData = self.rawData.drop(defaultLocationColumns, axis=1)
        else:
            propertData = self.rawData
            locations = []
            
        return propertData, locations

    @staticmethod
    def createLoader(serviceType, path):
        if serviceType == ServiceType.School:
            return SchoolFactory(path)
        elif serviceType == ServiceType.Library:
            return LibraryFactory(path)
        else:
            print ("We're sorry, this service han not been implemented yet!")

            
## UnitFactory children classes
class SchoolFactory(UnitFactory):
    
    def __init__(self, path):
        super().__init__(path)
        self.servicetype = ServiceType.School
        
    def load(self, meanRadius):
        
        self.rawData = pd.read_csv(self.filepath, sep=';', decimal=',')
        self.nUnits = self.rawData.shape[0]
        
        
        assert meanRadius, 'Please provide a reference radius for the mean school size'
        (propertData, locations) = super().load_from_path()
        
        nameCol = 'DENOMINAZIONESCUOLA'
        typeCol = 'ORDINESCUOLA'
        scaleCol = 'ALUNNI'
        
        typeAgeDict = {'SCUOLA PRIMARIA': {AgeGroup.ChildPrimary:1},
                      'SCUOLA SECONDARIA I GRADO': {AgeGroup.ChildMid:1},
                      'SCUOLA SECONDARIA II GRADO': {AgeGroup.ChildHigh:1},}
        
        schoolTypes = propertData[typeCol].unique()
        assert set(schoolTypes) <= set(typeAgeDict.keys()), 'Unrecognized types in input'
        
        # set the scale to be proportional to the square root of number of children
        scaleData = propertData[scaleCol]**.5
        scaleData = scaleData/scaleData.mean() * meanRadius #mean value is mapped to input parameter
        propertData[scaleCol] = scaleData 
        unitList = []
                
        for scType in schoolTypes:
            bThisGroup = propertData[typeCol]==scType
            typeData = propertData[bThisGroup]
            typeLocations = [l for i,l in enumerate(locations) if bThisGroup[i]]

            for iUnit in range(typeData.shape[0]):
                rowData = typeData.iloc[iUnit,:]
                attrDict = {'level':scType}
                thisUnit = ServiceUnit(self.servicetype, 
                        name=rowData[nameCol], 
                        position=typeLocations[iUnit], 
                        ageDiffusionIn=typeAgeDict[scType], 
                        scaleIn=rowData[scaleCol],
                        attributesIn=attrDict)
                unitList.append(thisUnit)
        
        return unitList


class LibraryFactory(UnitFactory):
    
    def __init__(self, path):
        super().__init__(path)
        self.servicetype = ServiceType.Library
        
    def load(self, meanRadius):
        
        self.rawData = pd.read_csv(self.filepath, sep=';', decimal='.')
        self.nUnits = self.rawData.shape[0]
        
        assert meanRadius, 'Please provide a reference radius for the mean library size'
        (propertData, locations) = super().load_from_path()
        
        nameCol = 'denominazioni.ufficiale'
        typeCol = 'tipologia-funzionale'
        
        # Modifica e specifica che per le fasce d'età
        typeAgeDict = {'Specializzata': {group:1 for group in AgeGroup.all()},
                      'Importante non specializzata': {group:1 for group in AgeGroup.all()},
                      'Pubblica': {group:1 for group in AgeGroup.all()},
                      'NON SPECIFICATA': {AgeGroup.ChildPrimary:1},
                      'Scolastica': {AgeGroup.ChildPrimary:1},
                      'Istituto di insegnamento superiore': {AgeGroup.ChildPrimary:1},
                      'Nazionale': {AgeGroup.ChildPrimary:1},}
        
        libraryTypes = propertData[typeCol].unique()
        assert set(libraryTypes) <= set(typeAgeDict.keys()), 'Unrecognized types in input'
        
        unitList = []
                
        for libType in libraryTypes:
            bThisGroup = propertData[typeCol]==libType
            typeData = propertData[bThisGroup]
            typeLocations = [l for i,l in enumerate(locations) if bThisGroup[i]]

            for iUnit in range(typeData.shape[0]):
                rowData = typeData.iloc[iUnit,:]
                attrDict = {'level':libType}
                thisUnit = ServiceUnit(self.servicetype, 
                        name=rowData[nameCol], 
                        position=typeLocations[iUnit], 
                        ageDiffusionIn=typeAgeDict[libType], 
                        attributesIn=attrDict)
                unitList.append(thisUnit)
        
        return unitList