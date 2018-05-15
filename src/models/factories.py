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
from src.models.core import ServiceUnit, ServiceEvaluator, ServiceValues, MappedPositionsFrame

    
## UnitFactory father class
class UnitFactory:
    def __init__(self, path, sepInput=';', decimalInput=','):
        assert os.path.isfile(path), 'File "%s" not found' % path
        self.filepath = path

        self.rawData = pd.read_csv(self.filepath, sep=sepInput, decimal=decimalInput)
        self.nUnits = self.rawData.shape[0]
        
    def load_from_path(self):
           
        defaultLocationColumns = ['Lat', 'Long']
        if set(defaultLocationColumns).issubset(set(self.rawData.columns)):
            print('Location data found')
            # store geolocations as geopy Point
            locations = [geopy.Point(
                self.rawData.loc[i, defaultLocationColumns]) for i in range(self.nUnits)]
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
        elif serviceType == ServiceType.TransportStop:
            return TransportStopFactory(path)
        elif serviceType == ServiceType.Pharmacy:
            return PharmacyFactory(path)
        else:
            print ("We're sorry, this service has not been implemented yet!")

    @staticmethod
    def make_loaders_for_city(modelCity):
        paths = modelCity.servicePaths
        return {s.label: UnitFactory.createLoader(s, paths[s]) for s in modelCity.keys()}

            
## UnitFactory children classes
class SchoolFactory(UnitFactory):
    
    def __init__(self, path):
        super().__init__(path)
        self.servicetype = ServiceType.School
        
    def load(self, meanRadius):
        
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
        super().__init__(path, decimalInput='.')
        self.servicetype = ServiceType.Library
        
    def load(self, meanRadius):
        
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


class TransportStopFactory(UnitFactory):

    def __init__(self, path):
        super().__init__(path, decimalInput='.')
        self.servicetype = ServiceType.TransportStop

    def load(self, meanRadius):

        assert meanRadius, 'Please provide a reference radius for stops'
        (propertData, locations) = super().load_from_path()
        # make unique stop code
        propertData['stopCode'] = propertData['stop_id'] + '_' + propertData['route_id']
        # append route types
        routeTypeCol = 'route_type'
        gtfsTypesDict = {0: 'Tram', 1: 'Metro', 3: 'Bus'}
        assert all(propertData[routeTypeCol].isin(gtfsTypesDict.keys())), 'Unexpected route type'
        propertData['routeDesc'] = propertData[routeTypeCol].replace(gtfsTypesDict)

        nameCol = 'stopCode'
        typeCol = 'routeDesc'

        scaleDict = {0:meanRadius, 1: 2*meanRadius, 3: meanRadius}

        unitList = []
        for iUnit in range(propertData.shape[0]):
            rowData = propertData.iloc[iUnit, :]
            attrDict = {'routeType': rowData[typeCol]}
            thisUnit = ServiceUnit(self.servicetype,
                                   name=rowData[nameCol],
                                   position=locations[iUnit],
                                   ageDiffusionIn={g:1 for g in AgeGroup.all_but(
                                       [AgeGroup.Newborn, AgeGroup.Kinder])},
                                   scaleIn=scaleDict[rowData[routeTypeCol]],
                                   attributesIn=attrDict)
            unitList.append(thisUnit)

        return unitList


class PharmacyFactory(UnitFactory):

    def __init__(self, path):
        super().__init__(path)
        self.servicetype = ServiceType.Pharmacy

    def load(self, meanRadius):
        assert meanRadius, 'Please provide a reference radius for pharmacies'
        (propertData, locations) = super().load_from_path()

        nameCol = 'CODICEIDENTIFICATIVOFARMACIA'
        colAttributes = {'Descrizione': 'DESCRIZIONEFARMACIA', 'PartitaIva': 'PARTITAIVA'}

        unitList = []
        for iUnit in range(propertData.shape[0]):
            rowData = propertData.iloc[iUnit, :]
            attrDict = {name:rowData[col] for name, col in colAttributes.items()}
            thisUnit = ServiceUnit(self.servicetype,
                                   name=rowData[nameCol].astype(str),
                                   position=locations[iUnit],
                                   ageDiffusionIn={g: 1 for g in AgeGroup.all()},
                                   scaleIn=meanRadius,
                                   attributesIn=attrDict)
            unitList.append(thisUnit)

        return unitList


class UrbanGreenFactory(UnitFactory):

    def __init__(self, path):
        super().__init__(path)
        self.servicetype = ServiceType.UrbanGreen

    def load(self, meanRadius):
        assert meanRadius, 'Please provide a reference radius for urban green'
        (propertData, locations) = super().load_from_path()

        nameCol = 'CODICEIDENTIFICATIVOFARMACIA'
        colAttributes = {'Descrizione': 'DESCRIZIONEFARMACIA', 'PartitaIva': 'PARTITAIVA'}

        unitList = []
        for iUnit in range(propertData.shape[0]):
            rowData = propertData.iloc[iUnit, :]
            attrDict = {name: rowData[col] for name, col in colAttributes.items()}
            thisUnit = ServiceUnit(self.servicetype,
                                   name=rowData[nameCol].astype(str),
                                   position=locations[iUnit],
                                   ageDiffusionIn={g: 1 for g in AgeGroup.all()},
                                   scaleIn=meanRadius,
                                   attributesIn=attrDict)
            unitList.append(thisUnit)

        return unitList