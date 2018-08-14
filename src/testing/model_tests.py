import unittest
import numpy as np
import pandas as pd
import os
import sys
import geopy

# absolute import preparation for when run as script
root_dir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.realpath(__file__))))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from references import city_settings
from references.city_items import AgeGroup, ServiceType
from src.models.core import ServiceUnit, ServiceEvaluator

mock_service_type = next(ServiceType.__iter__())
mock_age_group = next(AgeGroup.__iter__())
lengthscale = 1
city = city_settings.CITY_NAMES_LIST[0]


def get_sample_unit(coords=(40, 9)):
    """Generate a test service unit."""

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
                self.assertAlmostEqual(np.exp(- sigma ** 2 / 2), computed)


class TestCityLoading(unittest.TestCase):

    """Tests for TestDemandFrame.

    """
    def test_city_config(self):
        self.assertIsInstance(city_settings.get_city_config(city),
                              city_settings.ModelCity)

    def test_get_istat_cpa(self):
        model_city = city_settings.get_city_config(city)
        self.assertIsInstance(model_city.istat_cpa_data, pd.DataFrame)


class TestServiceEvaluator(unittest.TestCase):

    """Tests for ServiceEvaluator.

    """
    positions = [(40, 9), (40, 9.01), (40.01, 9), (40.01, 9.01)]
    unit_list = [get_sample_unit(yx) for yx in positions]

    def test_constructor(self):

        evaluator = ServiceEvaluator(self.unit_list)
        self.assertIsInstance(evaluator, ServiceEvaluator)

    def test_list_evaluation(self):
        evaluator = ServiceEvaluator(self.unit_list)
        interactions = evaluator.get_interactions_at(
            np.array(self.positions[0:3:2]))

        self.assertTrue(interactions)


if __name__ == '__main__':
    # Run all tests
    unittest.main()
