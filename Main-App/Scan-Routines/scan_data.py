import numpy as np
import time
from idq_tc1000 import counter, tol


class ToLData:
    def __init__(self, histogram: ToLHistogram = None, acquisition_info: ToLInfo = None):
        
        if histogram != None and type(histogram) == ToLHistogram:
            self.histogram = histogram
        else:
            raise ValueError("ToL Class: histogram needs to be specified and needs to be the correct object type.")

        if acquisition_info and type(acquisition_info) == ToLInfo:
            self.acquisition_info = acquisition_info
        
        self.time_created = time.time()


class VolumetricDataArray:
    def __init__(self, resolution: list = [0, 0, 0]):
        # ?Sanity checks on resolution
        self.x_res = resolution[0]
        self.y_res = resolution[1]
        self.z_res = resolution[2]
        self.data = np.empty((resolution[0],resolution[1],resolution[2]), dtype=object)
    
    def input(self, position: list, value: list[Count,ToL]) -> bool:
        # ?Sanity checks on position
        # ?Sanity checks on value
        try:
            self.data[position[0], position[1], position[2]] = value
            return True
        except:
            return False
        
    def output(self, position: list) -> list[Count,ToL]:
        # Sanity checks on position request
        return self.data[position[0], position[1], position [2]]
    

    
