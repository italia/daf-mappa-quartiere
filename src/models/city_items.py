import numpy as np
from enum import Enum
import geopy


# Enum classes
class AgeGroup(Enum):
    Newborn = (0, 3)
    Kinder = (3, 6)
    ChildPrimary = (6, 10)
    ChildMid = (10, 15)
    ChildHigh = (15, 19)
    Young = (19, 25)
    Junior = (25, 35)
    Senior = (35, 50)
    Over50 = (50, 65)
    Over65 = (65, 74)
    Over74 = (74, 200)

    def __init__(self, start_age, end_age):
        self.start = start_age
        self.end = end_age

    def comprehends(self, value_in):
        return self.start <= value_in < self.end

    @staticmethod
    def all():
        return [g for g in AgeGroup]

    @staticmethod
    def all_but(excluded):
        return [g for g in AgeGroup if g not in excluded]

    @staticmethod
    def classify_array(array_in):
        return [AgeGroup.find_age_group(y) for y in array_in]

    @staticmethod
    def find_age_group(x):
        for g in AgeGroup.all():
            if g.comprehends(x):
                return g
        raise 'Classes are not adjacent, failed to classify %s' % x

    @property
    def range(self): return self.end - self.start


class ServiceArea(Enum):
    EducationCulture = 'EducazioneCultura'
    Transport = 'Trasporti'
    PublicSafety = 'Sicurezza'
    Health = 'Salute'
    Environment = 'Ambiente'


class SummaryNorm(Enum):
    l1 = 1
    l2 = 2
    lInf = np.inf


class ServiceType(Enum):
    School = (1,  # enum id
              ServiceArea.EducationCulture,
              SummaryNorm.l2,
              [AgeGroup.ChildPrimary, AgeGroup.ChildMid, AgeGroup.ChildHigh],
              'Scuole',
              'MIUR')
    #
    Library = (2,  # enum id
               ServiceArea.EducationCulture,
               SummaryNorm.l2,
               AgeGroup.all_but([AgeGroup.Newborn, AgeGroup.Kinder]),
               'Biblioteche',
               'MIBACT')
    #
    TransportStop = (3,  # enum id
                     ServiceArea.Transport,
                     SummaryNorm.l2,
                     AgeGroup.all_but([AgeGroup.Newborn, AgeGroup.Kinder]),
                     'Fermate TPL',
                     'GTFS Comuni')
    #
    Pharmacy = (4,  # enum id
                ServiceArea.Health,
                SummaryNorm.lInf,  # assume pharmacies are equivalent
                AgeGroup.all(),
                'Farmacie',
                'Min. Salute')

    UrbanGreen = (5,  # enum id
                  ServiceArea.Environment,
                  SummaryNorm.l2,
                  AgeGroup.all(),
                  'Aree Verdi',
                  'Open Data Comuni')

    def __init__(self, _, area_of_service,
                 aggr_norm_input=SummaryNorm.l2,
                 demand_ages_input=AgeGroup.all(),
                 label='', data_source=''):
        self.aggregation_norm = aggr_norm_input
        self.service_area = area_of_service
        self.label = label
        self.data_source = data_source
        # declare the AgeGroups that make use of this service
        assert isinstance(demand_ages_input, list), \
            'list expected for demand ages'
        assert all([isinstance(g, AgeGroup) for g in demand_ages_input]),\
            'AgeGroups expected'
        self.demand_ages = demand_ages_input

    def aggregate_units(self, unit_values, axis=1):
        # assumes positions are stacked in rows
        return np.apply_along_axis(
            lambda x: np.linalg.norm(x, ord=self.aggregation_norm.value),
            axis,
            unit_values)

    @staticmethod
    def all():
        return [g for g in ServiceType]


# test utility
def get_random_pos(n):
    out = list(map(geopy.Point, list(zip(np.round(
        np.random.uniform(45.40, 45.50, n), 5),
        np.round(np.random.uniform(9.1, 9.3, n), 5)
    ))))
    return out
