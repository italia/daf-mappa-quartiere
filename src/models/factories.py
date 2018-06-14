from enum import Enum
import os.path

import numpy as np
import pandas as pd
import geopandas as gpd
import geopy, geopy.distance
from sklearn import gaussian_process

## TODO: find way to put this into some global settings
import os
import sys
import shapely

rootDir = os.path.dirname(os.path.dirname(__file__))
if rootDir not in sys.path:
    sys.path.append(rootDir)

from references import city_settings, common_cfg

from src.models.city_items import AgeGroup, ServiceArea, ServiceType, SummaryNorm # enum classes for the model
from src.models.core import ServiceUnit, ServiceEvaluator, ServiceValues, MappedPositionsFrame

    
## UnitFactory father class
class UnitFactory:
    def __init__(self, model_city, sepInput=';', decimalInput=','):
        assert isinstance(model_city, city_settings.ModelCity), 'ModelCity expected'
        self.model_city = model_city
        self._rawData = pd.read_csv(self.filepath, sep=sepInput, decimal=decimalInput)
        
    def extract_locations(self):

        defaultLocationColumns = common_cfg.coord_col_names
        if set(defaultLocationColumns).issubset(set(self._rawData.columns)):
            print('Location data found')
            # check and drop units outside provided city boundary
            geometry = [shapely.geometry.Point(xy) for xy in zip(
                self._rawData[defaultLocationColumns[0]],  # Long
                self._rawData[defaultLocationColumns[1]])]  # Lat
            bWithinBoundary = np.array(list(map(
                lambda p: p.within(self.model_city.convhull), geometry)))

            if not all(bWithinBoundary):
                print('%s -- dropping %i units outside city.' % (self.servicetype, sum(
                    ~bWithinBoundary)))
                self._rawData = self._rawData.iloc[bWithinBoundary, :].reset_index()

            # store geolocations as geopy Point
            locations = [geopy.Point(yx) for yx in zip(
                self._rawData[defaultLocationColumns[1]],  # Lat
                self._rawData[defaultLocationColumns[0]])]  # Long

            propertData = self._rawData.drop(defaultLocationColumns, axis=1)

        else:
            raise NotImplementedError('Locations not found - not implemented!')

        return propertData, locations

    def save_units_with_attendance_to_geojson(self, unitsList):
        ''' Trim units to the ones of this loader type and append attendance for matching id.
        Then export original unit data completed with attendance in geojson format'''
        data = gpd.GeoDataFrame(self._rawData).copy()
        # convert bool in GeoDataFrame to str in order to save it
        for col in data.columns:
            if data[col].dtype in (np.bool, bool):
                data[col] = data[col].astype(str)
        # build geometry column
        longCol, latCol = common_cfg.coord_col_names
        data = data.set_geometry(
            [shapely.geometry.Point(xy) for xy in zip(data[longCol], data[latCol])])

        # append attendance
        compatibleUnits = [u for u in unitsList if u.service == self.servicetype]
        if compatibleUnits:
            unitFrame = pd.DataFrame({self.idCol: [u.id for u in compatibleUnits],
                                      'Affluenza': [u.attendance for u in compatibleUnits]})
            data = data.merge(unitFrame, on=self.idCol)

        # save file and overwrite if it already exists
        try:
            os.remove(self.output_path)
        except OSError:
            pass

        data.to_file(self.output_path, driver='GeoJSON')

        return data

    @property
    def nUnits(self):
        return self._rawData.shape[0]

    @property
    def filepath(self):
        return self.model_city.service_paths[self.servicetype]

    @property
    def output_path(self):
        _, fullfile = os.path.split(self.filepath)
        filename, _ =os.path.splitext(fullfile)
        return os.path.join(common_cfg.units_output_path, filename + '.geojson')

    @staticmethod
    def get_factory(serviceType):
        typeFactory = [factory for factory in UnitFactory.__subclasses__() \
                       if factory.servicetype ==serviceType]
        assert len(typeFactory) <= 1, 'Duplicates in loaders types'
        if typeFactory:
            return typeFactory[0]
        else:
            print ("We're sorry, this service has not been implemented yet!")
            return []

    @staticmethod
    def make_loaders_for_city(modelCity):
        loadersDict = {}
        for sType in modelCity.keys():
            loadersDict[sType.label] = UnitFactory.get_factory(sType)(modelCity)
        return loadersDict

            
## UnitFactory children classes
class SchoolFactory(UnitFactory):

    servicetype = ServiceType.School
    nameCol = 'DENOMINAZIONESCUOLA'
    typeCol = 'ORDINESCUOLA'
    scaleCol = 'ALUNNI'
    idCol = 'CODSCUOLA'

    def load(self, meanRadius, privateRescaling=1, sizePowerLaw=0):
        
        assert meanRadius, 'Please provide a reference radius for the mean school size'
        (propertData, locations) = super().extract_locations()

        typeAgeDict = {'SCUOLA PRIMARIA': {AgeGroup.ChildPrimary:1},
                      'SCUOLA SECONDARIA I GRADO': {AgeGroup.ChildMid:1},
                      'SCUOLA SECONDARIA II GRADO': {AgeGroup.ChildHigh:1},}
        
        schoolTypes = propertData[self.typeCol].unique()
        assert set(schoolTypes) <= set(typeAgeDict.keys()), 'Unrecognized types in input'

        attendanceProxy = propertData[self.scaleCol].copy()

        # set the scale to be proportional to the square root of number of children
        scaleData = attendanceProxy**sizePowerLaw

        # mean value is mapped to input parameter
        scaleData = scaleData/scaleData.mean()* meanRadius

        # assign to new column
        rescaledName = 'SCALE'
        propertData[rescaledName] = scaleData
        unitList = []

        for scType in schoolTypes:
            bThisGroup = propertData[self.typeCol]==scType
            typeData = propertData[bThisGroup]
            typeLocations = [l for i,l in enumerate(locations) if bThisGroup[i]]

            for iUnit in range(typeData.shape[0]):
                rowData = typeData.iloc[iUnit,:]
                attrDict = {'level':scType, 'Public':rowData['bStatale']}
                thisUnit = ServiceUnit(self.servicetype, 
                        name=rowData[self.nameCol],
                        id=rowData[self.idCol],
                        position=typeLocations[iUnit], 
                        ageDiffusionIn=typeAgeDict[scType], 
                        scaleIn=rowData[rescaledName],
                        attributesIn=attrDict)

                if not attrDict['Public'] and privateRescaling !=1:
                    thisUnit.transform_kernels_with_factor(privateRescaling)

                unitList.append(thisUnit)
        
        return unitList


class LibraryFactory(UnitFactory):

    servicetype = ServiceType.Library
    nameCol = 'denominazioni.ufficiale'
    typeCol = 'tipologia-funzionale'
    idCol = 'codiceIsil'

    #def __init__(self, model_city):
        #super().__init__(model_city, decimalInput='.')
        
    def load(self, meanRadius):
        
        assert meanRadius, 'Please provide a reference radius for the mean library size'
        (propertData, locations) = super().extract_locations()
        
        # Modifica e specifica che per le fasce d'età
        possibleUsers = AgeGroup.all_but([AgeGroup.Newborn,AgeGroup.Kinder])
        typeAgeDict = {'Specializzata': {group:1 for group in possibleUsers},
                      'Importante non specializzata': {group:1 for group in possibleUsers},
                      'Pubblica': {group:1 for group in possibleUsers},
                      'NON SPECIFICATA': {group:1 for group in possibleUsers},
                      'Scolastica': {group:1 for group in [
                          AgeGroup.ChildPrimary, AgeGroup.ChildMid, AgeGroup.ChildHigh]},
                      'Istituto di insegnamento superiore': {
                          group:1 for group in AgeGroup.all_but([AgeGroup.Newborn,
                                                                 AgeGroup.Kinder,
                                                                 AgeGroup.ChildPrimary,
                                                                 AgeGroup.ChildMid])},
                      'Nazionale': {group:1 for group in possibleUsers},}
        
        libraryTypes = propertData[self.typeCol].unique()
        assert set(libraryTypes) <= set(typeAgeDict.keys()), 'Unrecognized types in input'
        
        unitList = []
                
        for libType in libraryTypes:
            bThisGroup = propertData[self.typeCol]==libType
            typeData = propertData[bThisGroup]
            typeLocations = [l for i,l in enumerate(locations) if bThisGroup[i]]

            for iUnit in range(typeData.shape[0]):
                rowData = typeData.iloc[iUnit,:]
                attrDict = {'level':libType}
                thisUnit = ServiceUnit(self.servicetype, 
                        name=rowData[self.nameCol],
                        id=rowData[self.idCol],
                        scaleIn=meanRadius,
                        position=typeLocations[iUnit], 
                        ageDiffusionIn=typeAgeDict[libType],
                        attributesIn=attrDict)
                unitList.append(thisUnit)
        
        return unitList


class TransportStopFactory(UnitFactory):

    servicetype = ServiceType.TransportStop
    nameCol = 'stopCode'
    typeCol = 'routeDesc'
    idCol = 'stopCode'

    def __init__(self, model_city):
        super().__init__(model_city, decimalInput='.')

    def load(self, meanRadius):

        assert meanRadius, 'Please provide a reference radius for stops'
        (propertData, locations) = super().extract_locations()
        # make unique stop code
        propertData['stopCode'] = propertData['stop_id'] + '_' + propertData['route_id']
        # append route types
        routeTypeCol = 'route_type'
        gtfsTypesDict = {0: 'Tram', 1: 'Metro', 3: 'Bus'}
        assert all(propertData[routeTypeCol].isin(gtfsTypesDict.keys())), 'Unexpected route type'
        propertData['routeDesc'] = propertData[routeTypeCol].replace(gtfsTypesDict)

        scaleDict = {0:meanRadius, 1: 2*meanRadius, 3: meanRadius}
        thresholdsDict = {t: None for t in scaleDict.keys()}

        unitList = []
        for iUnit in range(propertData.shape[0]):
            rowData = propertData.iloc[iUnit, :]
            unitRouteType = rowData[routeTypeCol]
            attrDict = {'routeType': rowData[self.typeCol]}
            cachedThresholds = thresholdsDict[unitRouteType] # this is None by default
            thisUnit = ServiceUnit(self.servicetype,
                                   name=rowData[self.nameCol],
                                   id=rowData[self.idCol],
                                   position=locations[iUnit],
                                   scaleIn=scaleDict[unitRouteType],
                                   ageDiffusionIn={g:1 for g in AgeGroup.all_but(
                                       [AgeGroup.Newborn, AgeGroup.Kinder])},
                                   kernelThresholds=cachedThresholds,
                                   attributesIn=attrDict)
            unitList.append(thisUnit)
            # if there were no thresholds for this unit type, cache the computed ones
            if not cachedThresholds:
                thresholdsDict[unitRouteType] = thisUnit.kerThresholds

        return unitList


class PharmacyFactory(UnitFactory):

    servicetype = ServiceType.Pharmacy
    nameCol = 'CODICEIDENTIFICATIVOFARMACIA'
    idCol = nameCol

    def __init__(self, model_city):
        super().__init__(model_city, decimalInput='.')

    def load(self, meanRadius):
        assert meanRadius, 'Please provide a reference radius for pharmacies'
        (propertData, locations) = super().extract_locations()

        colAttributes = {'Descrizione': 'DESCRIZIONEFARMACIA', 'PartitaIva': 'PARTITAIVA'}

        unitList = []
        cachedThresholds = None # unique value as all pharmacies share the same scale
        for iUnit in range(propertData.shape[0]):
            rowData = propertData.iloc[iUnit, :]
            attrDict = {name:rowData[col] for name, col in colAttributes.items()}
            thisUnit = ServiceUnit(self.servicetype,
                                   name=rowData[self.nameCol].astype(str),
                                   id = rowData[self.idCol],
                                   position=locations[iUnit],
                                   scaleIn=meanRadius,
                                   ageDiffusionIn={g: 1 for g in AgeGroup.all()},
                                   kernelThresholds=cachedThresholds,
                                   attributesIn=attrDict)
            unitList.append(thisUnit)
            # if there were no thresholds, cache the computed ones
            if not cachedThresholds:
                cachedThresholds = thisUnit.kerThresholds

        return unitList


class UrbanGreenFactory(UnitFactory):

    servicetype = ServiceType.UrbanGreen

    def load(self, meanRadius):
        assert meanRadius, 'Please provide a reference radius for urban green'
        (propertData, locations) = super().extract_locations()

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