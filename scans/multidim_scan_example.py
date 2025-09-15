

'''

First iteration of scan on a sample. This scan's structure must be something of the kind:
- Initiate necessary devices in correct order with hardcoded addresses
- Create data structure for measurements, which is a list with positions and counts

- Create a step list in sequence, which means a list populated by the values in which the nanopositioner will have to step on.
- The nanopositioner then zeroes it's position
- Sets a velocity
- The timecontroller records count and DataCount object has a time and frequency information.

'''
from devices.idq_tc1000_device import *
from devices.montana_cryoadvance_controls import *
from scans.scan_data_structures import *
from utils.common import connect
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import time
import signal
import sys




# Connections section

idq_ip = "149.132.99.103"  # Connection for IDQ
montana_ip = "149.132.99.104"


# Preparation of IDQ TC
try:
    timecontroller = TimeController(idq_ip)
    start_counter = timecontroller.get_counter("start")
    input1_counter = timecontroller.get_counter(1)
    input1_tol = timecontroller.get_tol(1)

    while not timecontroller.threshold(1, -0.1) or not timecontroller.threshold("start", -0.3):
        print("Could not set voltage threshold. Retrying")
        time.sleep(0.5)

    for i in ["start", 1]:
        timecontroller.enable_input(i)

except Exception as e:
    print(f"Error during preparation of IDQ: {e}")

print(f'Threshold on Start: {timecontroller.threshold("start")}\nThreshold on Input 1: {timecontroller.threshold(1)}\n')

# Preparation of Montana:
try:
    positioner = Positioner(montana_ip)

except Exception as e:
    print(f"Error during preparation of Montana: {e}")


# Preparation of Data Structures with settings

scan_set = ScanParameters()

axis_list = ["Y", "Z"]
scan_set.step_size["Z"]=0.000005   # metres
scan_set.step_size["Y"]=0.000005   # metres
scan_set.step_velocity=50 * 1e-6    # meters/sec  ##IMPLEMENT THIS IN THE POSITIONER CLASS. doing it manually from screen
scan_set.resolution["Z"]=2
scan_set.resolution["Y"]=2
input1_counter.set_integration_time(scan_set.counter_integration_time)

scan_sequencer = scan_set.initialize_step_sequencer()       # Initializes the sequencer, which is the object calculating the next movement of the positioner.

scan_res = scan_set.initialize_results()                    # Initializes the results, the object in chrge of storing data and saving/loading it to/from file.


############################## SCAN ROUTINE DEFINITION ###############################
# Returns CountData and ToLData in list.
def scan_motion(position_instruction: dict[str, float], scan_settings: ScanParameters, positioner: Positioner):


    actual_position=positioner.get_position(position_instruction["axis"])
    
    try_count=1
    while position_instruction["position"] != actual_position:
        positioner.move_to_position(position_instruction["axis"], position_instruction["position"])

        positioner.wait_end_motion(position_instruction["axis"], scan_settings.polling_frequency)
        time.sleep(0.25) # safety sleep
        
        actual_position=positioner.get_position(position_instruction["axis"])

        if try_count == scan_settings.max_positioner_retries:
            print(f"Took positioner {scan_settings.max_positioner_retries} times to get it right.\n Limit exceeded. Aborting.")
            exit()

        try_count+=1


########################################################################################

############################### COUNTER MEASUREMENT FUNCTION ###########################
def measure_frequency(step_index_vector: dict, scan_results: ScanResults, counter: TCCounter):
    data_obj = counter.count()
    scan_results.input_data(step_index_vector, data_obj)
########################################################################################
############################### ToL MEASUREMENT FUNCTION ###############################
def measure_tol(step_index_vector: dict, scan_results: ScanResults, acquisition_time: int, tol: TCToL):
    data_obj = tol.acquire(acquisition_time)                                # Hangs for X seconds.
    scan_results.input_data(step_index_vector, data_obj)                    # Inputs the diagram and proceeds
########################################################################################

def exit():
    print("Received signal to stop.")
    for axis in axis_list:
        positioner.stop(axis)
    for i in ["start", 1]:
        timecontroller.disable_input(i)
    
    sys.exit(0)


# Emergency Exit:
signal.signal(signal.SIGINT, exit)   # Ctrl+C
signal.signal(signal.SIGTERM, exit)  # kill <pid>




# MAIN LOOP LOGIC:


print("Tutto pronto. Premi invio...")
input()

start_time = time.time()

'''                                                     # Simulating for now.
for axis in axis_list:
    while not positioner.zero_position(axis):
        positioner.zero_position(axis)
        time.sleep(0.25)

    print(f"Zeroed {axis} axis.")
    time.sleep(0.25)
'''

index_vector = {axis: 0 for axis in axis_list}

while True:
    
    print(f"Current Position Index: {index_vector}")

    print("Measuring photon incidence freq:")
    measure_frequency(index_vector, scan_res, input1_counter)
    print(f"Measuring photon ToL for {scan_set.tol_acquisition_time} seconds:")
    measure_tol(index_vector, scan_res, scan_set.tol_acquisition_time, input1_tol)
    
    next = scan_sequencer.next_step_in_sequence()
    
    if next == None:
        break
    else:
        index_vector = next[0]
        motion_instructions = next[1]

    for instruction in motion_instructions:
        print(f"Moving Positioner to: {instruction}")
        
        '''
        scan_motion(instruction, scan_set, positioner)   ## Simulating for now, remove quotes when motion is required.
        '''

    time.sleep(scan_set.sleep_time)   # Another optional sleep margin, although not necessary.

end_time=time.time()

print(f"Time Elapsed for Scan: {end_time-start_time} S")



scan_res.save("C:\\Users\\cinzi\\Desktop\\scan-dump.json")
scan_set.save("C:\\Users\\cinzi\\Desktop\\scan-settings.json")

print("Premi invio per uscire...")
input()

