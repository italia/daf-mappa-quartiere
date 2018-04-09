import numpy as np
import pandas as pd
from sklearn import gaussian_process
from matplotlib import pyplot as plt 
from enum import Enum
import os.path

## Enum classes
class AgeGroup(Enum):
    Newborn= (0, 3)
    ChildPrimary= (6,10)
    ChildMid= (11,13)
    ChildHigh= (14,18) 
    Young= (19,25)
    Junior= (26,35)
    Senior= (36, 50)
    Over50= (50, 64)
    Over65= (66, 80)
    Over80= (81, 200)
    def __init__(self, startAge, endAge):
        self.start = startAge
        self.end = endAge
    
    @staticmethod
    def all():
        return([g for g in AgeGroup])
    @property
    def range(self): return self.end - self.start
    
    
class ServiceArea(Enum):
    Education = 1
    PublicSafety = 2
    Health = 3
    
    
class SummaryNorm(Enum):
    l1= lambda x: sum(abs(x))
    l2= lambda x: (sum(x**2))**0.5
    lInf= lambda x: max(x)
    

class ServiceType(Enum):
    School = (1, ServiceArea.Education, SummaryNorm.l2)
    #
    SocialSupport = (2, ServiceArea.Health, SummaryNorm.l2)
    #
    PoliceStation = (2, ServiceArea.PublicSafety, SummaryNorm.l2)
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
