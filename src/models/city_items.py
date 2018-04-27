import numpy as np
import pandas as pd
from sklearn import gaussian_process
from matplotlib import pyplot as plt 
from enum import Enum
import os.path
import geopy

## Enum classes
class AgeGroup(Enum):
    Newborn= (0, 3)
    Kinder = (3,6)
    ChildPrimary= (6,10)
    ChildMid= (10,15)
    ChildHigh= (15,19) 
    Young= (19,25)
    Junior= (25,35)
    Senior= (35, 50) 
    Over50= (50, 65)
    Over65= (65, 74)
    Over74= (74, 200)
    
    def __init__(self, startAge, endAge):
        self.start = startAge
        self.end = endAge
    
    def comprehends(self, valueIn):
        return self.start <= valueIn < self.end
    
    @staticmethod
    def all():
        return([g for g in AgeGroup])

    @staticmethod
    def classify_array(arrayIn):
        return [AgeGroup.find_AgeGroup(y) for y in arrayIn]
    
    @staticmethod
    def find_AgeGroup(x):
            for g in AgeGroup.all():
                if g.comprehends(x):
                    return g
            raise 'Classes are not adiacent, failed to classify %s' % x
            
    @property
    def range(self): return self.end - self.start 
    
    
class ServiceArea(Enum):
    EducationCulture = 'EducazioneCultura'
    PublicSafety = 'Sicurezza'
    Health = 'Salute'
    
    
class SummaryNorm(Enum):
    l1= lambda x: sum(abs(x))
    l2= lambda x: (sum(x**2))**0.5
    lInf= lambda x: max(x)
    

class ServiceType(Enum):
    School = (1, ServiceArea.EducationCulture, SummaryNorm.l2, 'Scuole', 'MIUR')
    #
    Library = (2, ServiceArea.EducationCulture, SummaryNorm.l2, 'Biblioteche', 'MIBACT')
    
    #etc
    def __init__(self, _, areaOfService,
                 aggrNormInput=SummaryNorm.l2, label='', dataSource=''):
        self.aggrNorm = aggrNormInput
        self.serviceArea = areaOfService
        self.label = label
        self.dataSource = dataSource
        # initialise demand factors for each age group
        print('WARNING: mock demand factors initalised for ServiceTypes')
        self.demandFactors = pd.Series({a: np.random.uniform() for a in AgeGroup.all()}) #TODO: import this from input
    
    def aggregate_units(self, unitValues, axis=1):
        # assumes positions are stacked in rows
        return np.apply_along_axis(self.aggrNorm, axis, unitValues)
    
    @staticmethod
    def all():
        return([g for g in ServiceType])
    
#demandFactors = pd.DataFrame(np.ones([len(AgeGroup.all()), len(ServiceType.all())]), 
#                             index=AgeGroup.all(), columns=ServiceType.all())
# test utility 
def get_random_pos(n):
    out = list(map(geopy.Point, list(zip(np.round(
                                np.random.uniform(45.40, 45.50, n), 5),  
                                np.round(np.random.uniform(9.1, 9.3, n), 5)
                                )))) 
    return out
