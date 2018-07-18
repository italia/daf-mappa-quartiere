import unittest
import numpy as np

import geopy
from references import common_cfg, istat_kpi, city_settings
from src.models.city_items import AgeGroup, ServiceType
from src.models.core import ServiceUnit, ServiceValues, MappedPositionsFrame, \
    KPICalculator

mock_service_type = next(ServiceType.__iter__())
mock_age_group = next(AgeGroup.__iter__())
lengthscale = 1


def get_sample_unit(coords=(40, 9)):
    sample_unit = ServiceUnit(
        service=mock_service_type,
        name='test unit',
        unit_id=1,
        position=geopy.Point(*coords),
        capacity=np.nan,
        lengthscales={mock_age_group: lengthscale},
        kernel_thresholds=None,
        attributes={})

    return sample_unit


class TestServiceUnit(unittest.TestCase):

    """Tests for ServiceUnit.

    """

    def test_constructor(self):
        sample_unit = get_sample_unit()
        self.assertIsInstance(sample_unit, ServiceUnit)

    def test_single_evaluation(self):
        sample_unit = get_sample_unit()
        for sigma in [1, 2, 3]:
            step = geopy.distance.great_circle(sigma)
            points_list = []
            #target_points = np.zeros_like([0,2])
            for bearing in np.arange(0, 360, 90):  # test many directions
                new_point = step.destination(
                    sample_unit.position, bearing=bearing)
                points_list.append(np.array(
                    [new_point.latitude, new_point.longitude]))
            interactions = sample_unit.evaluate(
                np.stack(points_list), mock_age_group)

            for computed in interactions:
                self.assertAlmostEquals(np.exp(- sigma ** 2 / 2), computed)

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromTestCase(TestServiceUnit))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
