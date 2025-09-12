import numpy as np
import sys
import os
import json
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import time
from devices.idq_tc1000_counter import * 
from devices.idq_tc1000_tol import *


class ScanParameters:
    def __init__(
        self,
        active_axes=None,
        resolution=None,
        step_size=None,
        step_velocity=None,
        polling_frequency=None,
        sleep_time=None,
        step_matrix=None,
        error_silent=None,
        filename=None,
    ):
        # defaults
        self.active_axes = ()
        self.resolution = {"X": 0, "Y": 0, "Z": 0}
        self.step_size = {"X": 0, "Y": 0, "Z": 0}
        self.step_velocity = None
        self.polling_frequency = 100
        self.sleep_time = 1
        self.step_matrix = {"X": [], "Y": [], "Z": []}
        self.error_silent = True
        self.filename = None

    
        if active_axes is not None:
            self.active_axes = active_axes
        if resolution is not None:
            self.resolution = resolution
        if step_size is not None:
            self.step_size = step_size
        if step_velocity is not None:
            self.step_velocity = step_velocity
        if polling_frequency is not None:
            self.polling_frequency = polling_frequency
        if sleep_time is not None:
            self.sleep_time = sleep_time
        if step_matrix is not None:
            self.step_matrix = step_matrix
        if error_silent is not None:
            self.error_silent = error_silent
        if filename is not None:
            self.filename = filename

    def __validate_position(self, position: tuple) -> tuple:
        if len(position) != len(self.active_axes):
            raise ValueError("ScanParameters.__validate_position(): coordinate dimension given is different from step matrix dimension.")
        return position

    
    def create_step_sequence(self):
        
        step_dims = list(size for size in self.resolution.values() if size > 0)
        self.active_axes = tuple(axis for axis, size in self.resolution.items() if size > 0)
        
        if not step_dims:
            raise ValueError("At least one resolution must be nonzero")
        
        for axis in self.active_axes:
            if self.step_size[axis] == 0:
                raise ValueError("Step sizes for active axes must be > 0")
                
        for axis in self.active_axes:
            for i in range(0, self.resolution[axis]):
                self.step_matrix[axis].append(round(i * self.step_size[axis], 9))

    
    def save(self, path: str):        # function to load params from file            
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.__dict__, f, indent=4)
            self.filename = path
            return True
        except Exception as e:
            # optional: print to stderr for debugging
            print(f"Error saving ScanParameters to {path}: {e}", file=sys.stderr)
            return False

    @classmethod
    def load(cls, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # unpack dictionary into the constructor
            return cls(**data)
        except Exception as e:
            print(f"Error loading ScanParameters from {path}: {e}", file=sys.stderr)
            return None


class ScanResults:
    def __init__(self, resolution: dict = {"X": 0, "Y": 0, "Z": 0}):
    
        if resolution != {"X": 0, "Y": 0, "Z": 0}:
            self.resolution = resolution
        else:
            raise ValueError("ScanResults.__init__(): wrong resolution argument passed.")
        
        self.active_axes = tuple(axis for axis, size in self.resolution.items() if size > 0)
        self.data_dims = tuple(size for size in self.resolution.values() if size > 0)
        self.data_matrix = np.empty(self.data_dims, dtype=object)

        self.filename = None

    def input_data(self, position: tuple, value: list) -> bool:
        self.data_matrix[position] = value


    def get_data(self, position: tuple) -> list:   
        try:
            return self.data_matrix[position]

        except Exception as e:
            print(f"ScanParameters.get_data(): encountered error -> {e}")

    def save(self, path:str) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                shape = tuple(self.resolution[ax] for ax in self.active_axes)
                serialized_data = []
                for idx in np.ndindex(shape):
                    obj_list = self.data_matrix[idx]
                    data_dict = {}
                    for obj in obj_list:
                        data_dict.update(obj.out())

                    entry={
                        "position": idx,
                        "values": data_dict
                    }
                    
                    serialized_data.append(entry)

                json.dump({
                    "resolution": self.resolution,
                    "data": serialized_data
                }, f, indent=2)                   
                
            self.filename = path
            return True
        except Exception as e:
            # optional: print to stderr for debugging
            print(f"Error saving ScanParameters to {path}: {e}", file=sys.stderr)
            return False

    @staticmethod
    def load(path:str):
        if not path:
            raise ValueError("ScanResults.load(): path must be given to load from file.")
        try:
            with open(path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            # Restore axes and resolution
            resolution = json_data["resolution"]
            obj = ScanResults(resolution)
            # Fill data_matrix with object lists
            for data_dict in json_data["data"]:
                counter_obj = CountData.input(data_dict["values"])
                tol_obj =  ToLData.input(data_dict["values"])

                obj_list = []
                if counter_obj:
                    obj_list.append(counter_obj)
                if tol_obj:
                    obj_list.append(tol_obj)
                
                pos = tuple(data_dict["position"])
                obj.input_data(pos, obj_list)
                
            return obj

        except Exception as e:
            import sys
            print(f"Error loading ScanResults from {path}: {e}", file=sys.stderr)
            return False

class Graph2D:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.title = {"name": "", "font": "", "fontsize": 16, "fontweight": "bold"}
        self.xlabel = {"name": "", "font": "", "fontsize": 10, "fontweight": "normal"}
        self.ylabel = {"name": "", "font": "", "fontsize": 10, "fontweight": "normal"}
        self.xaxis_majorlocator = 1
        self.yaxis_majorlocator = 1
        self.grid = {"visible": True, "linestyle": "--", "alpha": 1}
        self.file = {"name": "graph.png", "dpi": 500}

    def apply_settings(self):
        self.ax.set_title(self.title["name"], fontsize=self.title["fontsize"], fontweight=self.title["fontweight"])
        self.ax.set_xlabel(self.xlabel["name"], fontsize=self.xlabel["fontsize"], fontweight=self.xlabel["fontweight"])
        self.ax.set_ylabel(self.ylabel["name"], fontsize=self.ylabel["fontsize"], fontweight=self.ylabel["fontweight"])
        self.ax.xaxis.set_major_locator(MultipleLocator(self.xaxis_majorlocator))
        self.ax.yaxis.set_major_locator(MultipleLocator(self.yaxis_majorlocator))
        self.ax.grid(self.grid["visible"], linestyle=self.grid["linestyle"], alpha=self.grid["alpha"])

    def plot(self, x_data_list, y_data_list):
        self.ax.plot(x_data_list, y_data_list)

    def save(self):
        self.fig.savefig(self.file["name"], dpi=self.file["dpi"])

    def show(self):
        self.fig.show()



    
