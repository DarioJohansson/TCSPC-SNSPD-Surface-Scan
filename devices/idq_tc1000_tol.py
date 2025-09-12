import time
from utils.common import zmq_exec
from utils.acquisitions.histograms import *
import ast

# needs work to implement the class


class ToLData:
    def __init__(self, histogram: tuple[list, list] = None, time_created: float = None):
        
        if histogram != None or len(histogram[0]) == len(histogram[1]):
            self.x_data = histogram[0]
            self.y_data = histogram[1]
        else:
            raise ValueError("ToL Class: histogram needs to be specified and needs to be a tuple of two identical lenght lists (X and Y values)")
        
        if not time_created:
            self.time_created = time.time()
        else:
            self.time_created = time_created

    def out(self) -> dict:
        data = {"tol-x": self.x_data, "tol-y": self.y_data, "tol-timestamp": self.time_created}
        return data

    @staticmethod 
    def input(data: dict) -> bool:
        try:
            if data.get("tol-x") and data.get("tol-y") and data.get("tol-timestamp"):
                obj = ToLData(histogram=tuple(data.get("tol-x"), data.get("tol-y")), time_created=data.get("tol-timestamp"))
                return obj
            else:
                return None
        except:
            print("TOL object failed to load.")
            return None

class TCToL:
    def __init__(self, 
                    tc, 
                    input: 1|2|3|4, 
                    bwidth: int = 100, 
                    bcount: int = 1000, 
                    verbose: bool = False
                 ):
        self.bwidth = None
        self.bcount = None
        self.connection = tc
        self.verbose = verbose
        
        if input in range(0,4):
            self.input = input
            self.set_bwidth(bwidth)
            self.set_bcount(bcount)
        else:
            raise ValueError("TCToL: Failed to initialise. Invalid input channel for histogram acquisition.")
        
        if not self.input or not self.bwidth or not self.bcount:
            raise Exception("TCToL: Failed to initialise. User verbose mode for more info.")

    def set_bwidth(self, bwidth: int):  ## SOMETHING is off with the float int conversionto
        if bwidth:
            response = zmq_exec(self.connection, f"HIST{self.input}:BWID {bwidth}")
            if response.upper().strip() == f"VALUE SET TO {bwidth}":
                self.bwidth = bwidth
                return True
            
            if self.verbose:
                print(f"TCToL.set_bwidth(): Error from device -> {response}")           
            return False
        
        else:
            raise ValueError(f"TCToL.set_bwidth(): invalid bin width supplied: {bwidth}")
    
    def set_bcount(self, bcount: int):
        if bcount:
            response = zmq_exec(self.connection, f"HIST{self.input}:BCOU {bcount}")
            if response.upper().strip() == f"VALUE SET TO {bcount}":
                self.bcount = bcount
                return True
            if self.verbose:
                print(f"TCToL.set_bcount(): Error from device -> {response}")
            return False
        
        else:
            raise ValueError(f"TCToL.set_bcount(): invalid bin count supplied: {bcount}")


    def acquire(self, duration: int = None) -> ToLData:

        if not duration:
            raise ValueError("TCToL.acquire(): need to provide me with a valid acquisition duration value in seconds.")
        ### Configure the acquisition timer

        # Trigger RECord signal manually (PLAY command)
        zmq_exec(self.connection, "REC:TRIG:ARM:MODE MANUal")
        # Enable the RECord generator
        zmq_exec(self.connection, "REC:ENABle ON")
        # STOP any already ongoing acquisition
        zmq_exec(self.connection, "REC:STOP")
        # Record a single acquisition
        zmq_exec(self.connection, "REC:NUM 1")
        # Record for the request duration (in ps)
        zmq_exec(self.connection, f"REC:DURation {duration * 1e12}")
        # Flush previous data
        zmq_exec(self.connection, f"HIST{self.input}:FLUSh")  # Flush histogram

        zmq_exec(self.connection, "REC:PLAY")  # Start the acquisition

        wait_end_of_acquisition(self.connection)

        # Get histogram data
        Y_data = ast.literal_eval(zmq_exec(self.connection, f"HIST{self.input}:DATA?"))
        X_data = [i * self.bwidth for i in range(self.bcount)]
        tupl = (X_data, Y_data)
        data_object = ToLData(tupl)
        return data_object