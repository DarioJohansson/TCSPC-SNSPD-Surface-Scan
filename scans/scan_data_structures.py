import numpy as np
import sys
import os
import json
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from devices.idq_tc1000_counter import * 
from devices.idq_tc1000_tol import *

class StepSequencer():
    def __init__(self,
        resolution=None,
        step_size=None,
        ):
        if not resolution and not step_size:
            raise ValueError("StepSequencer.__init__(): resolution or step size empty or wrong format.")
        
        self.resolution = resolution
        self.step_size = step_size
        self.step_matrix = {}
        self.step_counter = {}
        self.active_axes = ()
        self.position = {}
        self.initialize_step_matrix()

    
    def zero_counter(self):
        for axis in self.step_counter.keys():
            self.step_counter[axis] = 0

    def initialize_step_matrix(self):
        
        step_dims = tuple(size for size in self.resolution.values() if size > 0)
        self.active_axes = tuple(axis for axis, size in self.resolution.items() if size > 0)
        
        if not step_dims:
            raise ValueError("StepSequencer.initialize_step_matrix(): At least one resolution must be nonzero")
        
        for axis in self.active_axes:
            if self.step_size[axis] == 0:
                raise ValueError("StepSequencer.initialize_step_matrix(): Step sizes for active axes must be different from 0")
                
        for axis in self.active_axes:
            self.position.update({axis: 0})
            self.step_matrix.update({axis: []})
            self.step_counter.update({axis: 0})
            for i in range(0, self.resolution[axis]):
                self.step_matrix[axis].append(round(i * self.step_size[axis], 9))           # Result of this will be a step matrix like so: {"Y": [steps], "Z": [steps]} if X resolution was left 0.

    def next_step_in_sequence(self) -> tuple[dict, list[dict]]|None:
        
        def diff_positions(old: dict, new: dict) -> list:
            changes = []
            for key, new_value in new.items():
                old_value = old.get(key)
                if old_value != new_value:
                    changes.append({"axis": key, "position": new_value})
            return changes
        
        old_position_vector = self.position

        # Next Step Index calculation        
        if self.step_counter != {axis: self.resolution[axis] - 1 for axis in self.active_axes}:
            for axis, value in self.step_counter.items():       ## Algorithm iterations: 4 works correctly now.
                if value < self.resolution[axis] - 1:
                    self.step_counter[axis] += 1
                    break
                else:
                    self.step_counter[axis] = 0

            # Now convert indexes to positions via the step size matrix 
            new_position_vector = {axis: self.step_counter[axis] * self.step_size[axis] for axis in self.active_axes}
            self.position = new_position_vector
            index_vector = self.step_counter
            motion_instructions = diff_positions(old_position_vector, new_position_vector)

            # Finally return the index vector and the instructions for motion.
            return index_vector, motion_instructions                # return signature iterations: at least 10 now.. my god. this should work, since the 
                                                                    # index vector is used by data input functions to put data in the right matrix slots
                                                                    # and instructions are interpreted by the positioner motion function.
        
        
        else:           # once scan is over, the sequences flips it's flag and outside functions can tell the sequence is over, to stop looping.
            self.step_counter = {axis: 0 for axis in self.active_axes}
            self.position = self.step_counter
            return None
        


class ScanParameters:
    def __init__(
        self,
        resolution=None,
        step_size=None,
        step_velocity=None,
        sleep_time=None,
        filename=None,
        polling_frequency = None,
        counter_integration_time = None,
        tol_acquisition_time = None,
        error_silent = None,
        max_positioner_retries = None
    ):
        # defaults
        self.resolution = {"X": 0, "Y": 0, "Z": 0}
        self.step_size = {"X": 0, "Y": 0, "Z": 0}           # Step size in meters
        self.step_velocity = None
        self.polling_frequency = 100
        self.counter_integration_time = 1000    # ms
        self.tol_acquisition_time = 60          # s
        self.sleep_time = 1
        self.error_silent = True
        self.filename = None
        self.max_positioner_retries = 10

    
        if resolution is not None:
            self.resolution = resolution
        if step_size is not None and type(step_size) == dict:
            self.step_size = {axis: round(value, 9) for axis, value in step_size.items()}
        if step_velocity is not None:
            self.step_velocity = round(step_velocity, 6)
        if polling_frequency is not None:
            self.polling_frequency = polling_frequency
        if counter_integration_time is not None:
            self.counter_integration_time = counter_integration_time
        if tol_acquisition_time is not None:
            self.tol_acquisition_time = tol_acquisition_time
        if sleep_time is not None:
            self.sleep_time = sleep_time
        if max_positioner_retries is not None:
            self.max_positioner_retries = max_positioner_retries
        if error_silent is not None:
            self.error_silent = error_silent
        if filename is not None:
            self.filename = filename

    def _validate_position(self, position: tuple) -> tuple:
        if len(position) != len(self.active_axes):
            raise ValueError("ScanParameters._validate_position(): coordinate dimension given is different from step matrix dimension.")
        return position

    def initialize_step_sequencer(self):
        return StepSequencer(self.resolution, self.step_size)
    
    def initialize_results(self):
        return ScanResults(self.resolution)
    
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
        
        for idx in np.ndindex(self.data_dims):
            self.data_matrix[idx] = []

        self.filename = None


    def input_data(self, position: dict, value: CountData|ToLData):
        tuple_position = tuple(value for value in position.values())
        self.data_matrix[tuple_position].append(value)


    def get_data(self, position: dict|tuple, data_type = None) -> list:  
        if type(position) == dict:
            tuple_position = tuple(value for value in position.values()) 
        elif type(position) == tuple:
            tuple_position = position

        if data_type not in [CountData, ToLData] and data_type != None:
            raise TypeError("ScanResults.get_data(): Provided wrong datatype for extraction.")
        
        try:
            if data_type == None:
                return self.data_matrix[tuple_position]
            else:
                for item in self.data_matrix[tuple_position]:
                    if type(item) == data_type:
                        return item

        except Exception as e:
            print(f"ScanParameters.get_data(): encountered error -> {e}")


    def save(self, path:str) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                shape = self.data_dims
                serialized_data = []
                for idx in np.ndindex(shape):                                       ## important indexing function numpy!!
                    explicit_position_idx = dict(zip(self.active_axes, idx))
                    obj_list = self.get_data(explicit_position_idx)
                    data_dict = {}
                    for obj in obj_list:
                        data_dict.update(obj.out())

                    entry={
                        "position": explicit_position_idx,
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
            
            pos = data_dict["position"]
            for item in obj_list:
                obj.input_data(pos, item)
            
        return obj


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



    
