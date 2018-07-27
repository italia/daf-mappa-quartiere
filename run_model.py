"""Run the whole model pipeline for all available cities and service types"""
print('\n Initialising MappaQuartiere model pipeline...')

from references import common_cfg
from src.models.city_items import ServiceType
from src.models.process_tools import ModelRunner

if __name__ == '__main__':

    """
    
    Set some values (in km) for the lengthscales associated to each 
    service type. 
    In the case of schools, we can set the power law for the service radius 
    to increase with size (0: no size effect; 1: linear effect). 
    
    """
    model_settings = {
        ServiceType.School.label: {
            'mean_radius': 0.4, 'size_power_law': 0.4},
        ServiceType.Library.label: {
            'mean_radius': 0.4},
        ServiceType.TransportStop.label: {
            'mean_radius': 0.3},
        ServiceType.Pharmacy.label: {
            'mean_radius': 0.5},
                    }

    runner = ModelRunner(model_settings)

    runner.run(attendance_correction_clip=common_cfg.demand_correction_clip)
