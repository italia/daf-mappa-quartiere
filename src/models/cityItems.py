import numpy as np
import pandas as pd
from sklearn import gaussian_process
from matplotlib import pyplot as plt 
from enum import Enum
import os.path

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
        out = []
        def assign_group(x):
            for g in AgeGroup.all():
                if g.comprehends(x):
                    return g
            raise 'Classes are not adiacent, failed to classify %s' % x
        return [assign_group(y) for y in arrayIn]
    
    @property
    def range(self): return self.end - self.start 
    
    
class ServiceArea(Enum):
    EducationCulture = 1
    PublicSafety = 2
    Health = 3
    
    
    
class SummaryNorm(Enum):
    l1= lambda x: sum(abs(x))
    l2= lambda x: (sum(x**2))**0.5
    lInf= lambda x: max(x)
    

class ServiceType(Enum):
    School = (1, ServiceArea.EducationCulture, SummaryNorm.l2)
    #
    SocialSupport = (2, ServiceArea.Health, SummaryNorm.l2)
    #
    PoliceStation = (3, ServiceArea.PublicSafety, SummaryNorm.l2)
    #
    Library = (4, ServiceArea.EducationCulture, SummaryNorm.l2)
    
    #etc
    def __init__(self, _, areaOfService, aggrNormInput=SummaryNorm.l2):
        self.aggrNorm = aggrNormInput
        self.serviceArea = areaOfService
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
