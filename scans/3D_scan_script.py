from devices.idq_tc1000_device import *
from devices.montana_cryoadvance_controls import *
from scans.scan_data_structures import *
import time
import signal
import sys
import os

## some util functions before we start:

def time_calculator(scan_settings, count=False, tol=False):
    time_per_grid_point = scan_settings.sleep_time
    if count:
        time_per_grid_point += scan_settings.counter_integration_time*1e-3
    if tol:
        time_per_grid_point += scan_settings.tol_acquisition_time
    
    grid_tuple = tuple(value for value in scan_settings.resolution.values())
    result = 0
    
    for i in grid_tuple:  #DIY tuple multiplication
        if result == 0:
            result = i
        else:
            result = result * i
    
    return result * time_per_grid_point


## Let'go:

########################### Connections section #################################

idq_ip = "149.132.99.103"  # Connection for IDQ
montana_ip = "149.132.99.104"

########################## Preparation of IDQ TC ################################
try:
    timecontroller = TimeController(idq_ip)
    start_counter = timecontroller.get_counter("start")
    input1_counter = timecontroller.get_counter(1)
    input1_tol = timecontroller.get_tol(1)


except Exception as e:
    print(f"Error during preparation of IDQ: {e}")


############################# Preparation of Montana ###############################
try:
    positioner = Positioner(montana_ip)

except Exception as e:
    print(f"Error during preparation of Montana: {e}")


################################ Scan Settings #####################################

scan_set = ScanParameters()
results_filepath = None
parameters_filepath = None
# Default values
axis_list = ["Y", "Z"]            
scan_set.step_size["Z"] = 0.00001   # metres
scan_set.step_size["Y"] = 0.00001   # metres
scan_set.resolution["Z"] = 60
scan_set.resolution["Y"] = 60
scan_set.counter_integration_time = 200 # ms
scan_set.tol_acquisition_time = 30      # s
scan_set.tol_bcount = 1000
scan_set.tol_bwidth = 1000
scan_set.tol_delay = 1400000
scan_set.sleep_time = 0
scan_started = False
settings_not_applied=True
input1_threshold = -0.1
start_threshold = -0.3


# --- USER PROMPTS ---

while settings_not_applied:
    # Scan Results Path
    results_path_input = input(f"Enter the full filepath of where the results file should be saved:")
    if results_path_input.strip():
        base_dir = os.path.dirname(os.path.abspath(results_path_input)) or '.'

        if not os.path.isdir(base_dir) or not os.access(base_dir, os.W_OK):
            print("Results Filepath Invalid (not accessible or non-existent)")
            continue
        else:
            results_filepath = results_path_input.strip()
    
    # Scan Parameters Path
    params_path_input = input(f"Enter the full filepath of where the scan-settings file should be saved:")
    if params_path_input.strip():
        base_dir = os.path.dirname(os.path.abspath(params_path_input)) or '.'

        if not os.path.isdir(base_dir) or not os.access(base_dir, os.W_OK):
            print("Results Filepath Invalid (not accessible or non-existent)")
            continue
        else:
            parameters_filepath = params_path_input.strip()
    
    # Axis list
    axis_input = input(f"Enter axis list as comma-separated values (current: {axis_list}) or press Enter to keep: ")
    if axis_input.strip():
        axis_list = [axis.strip().upper() for axis in axis_input.split(",")]
        if len(axis_list) == 0:
            print("Not enough axes supplied.")
            continue
    # Step size for each axis
    for axis in axis_list:
        current_step = scan_set.step_size.get(axis, 0.0)
        step_input = input(f"Enter step size for axis {axis} in metres (current: {current_step}): ")
        if step_input.strip():
            scan_set.step_size[axis] = float(step_input)

    for axis in scan_set.step_size.keys():
        if axis not in axis_list:
            scan_set.step_size[axis] = 0

    # Resolution for each axis
    for axis in axis_list:
        current_res = scan_set.resolution.get(axis, 0)
        res_input = input(f"Enter resolution (number of steps) for axis {axis} (current: {current_res}): ")
        if res_input.strip():
            scan_set.resolution[axis] = int(res_input)

    for axis in scan_set.resolution.keys():
        if axis not in axis_list:
            scan_set.resolution[axis] = 0

    # Counter integration time
    cit_input = input(f"Enter counter integration time in ms (current: {scan_set.counter_integration_time}): ")
    if cit_input.strip():
        scan_set.counter_integration_time = int(cit_input)

    # Tolerances
    acq_time_input = input(f"Enter time-of-life acquisition time in seconds (current: {scan_set.tol_acquisition_time}): ")
    if acq_time_input.strip():
        scan_set.tol_acquisition_time = int(acq_time_input)

    bcount_input = input(f"Enter time-of-life bin count (current: {scan_set.tol_bcount}): ")
    if bcount_input.strip():
        scan_set.tol_bcount = int(bcount_input)

    bwidth_input = input(f"Enter time-of-life bin width in ps (current: {scan_set.tol_bwidth}): ")
    if bwidth_input.strip():
        scan_set.tol_bwidth = int(bwidth_input)

    delay_input = input(f"Enter time-of-life bin delay in ps (current: {scan_set.tol_delay}): ")
    if delay_input.strip():
        scan_set.tol_delay = int(delay_input)

    # Sleep time
    sleep_input = input(f"Enter additional sleep time for each step in seconds (current: {scan_set.sleep_time}): ")
    if sleep_input.strip():
        scan_set.sleep_time = float(sleep_input)

    threshold_input = input(f"Enter voltage threshold for input signal detection on START (current: {start_threshold}): ")
    try:
        if threshold_input != '':
            start_threshold = float(threshold_input.strip())
    except Exception as e:
        print(f"Input is not a number. More details: {e}\n Try Again later.")
    
    threshold_input = input(f"Enter voltage threshold for input signal detection on channel 1 (current: {input1_threshold}): ") 
    try:
        if threshold_input != '':
            input1_threshold = float(threshold_input.strip())
    except Exception as e:
        print(f"Input is not a number. More details: {e}\n Try Again later.")

    # Final confirmation
    print("\nUpdated scan settings:")
    print(f"  Axes: {axis_list}")
    for axis in axis_list:
        print(f"  Step size {axis}: {scan_set.step_size} m")
        print(f"  Resolution {axis}: {scan_set.resolution}")
    print(f"  Counter integration time: {scan_set.counter_integration_time} ms")
    print(f"  Acquisition time tolerance: {scan_set.tol_acquisition_time} s")
    print(f"  Beam count tolerance: {scan_set.tol_bcount}")
    print(f"  Beam width tolerance: {scan_set.tol_bwidth}")
    print(f"  Delay tolerance: {scan_set.tol_delay} ms")
    print(f"  Sleep time: {scan_set.sleep_time} s")
    print(f"  Thresholds for START and INPUT1: {start_threshold} V - {input1_threshold} V")
    print("\n\n")
    
    while True:
        final_confirmation = input("Do these settings look good? y/n/abort\n")
        if final_confirmation in ['y','Y','yes','si']:
            settings_not_applied = False
            break
        elif final_confirmation in ['n', 'N', 'no']:
            break
        elif final_confirmation in ['abort', 'ABORT']:
            exit()
        else:
            print(f"What do you mean by {final_confirmation}?\nLet's try again:")


# Applying some settings here.
while not timecontroller.threshold(1, input1_threshold) or not timecontroller.threshold("start", start_threshold):
    print("Could not set voltage threshold. Retrying")
    time.sleep(0.5)

for i in ["start", 1]:
    timecontroller.enable_input(i)

print(f'Threshold on Start: {timecontroller.threshold("start")}\nThreshold on Input 1: {timecontroller.threshold(1)}\n')

input1_counter.set_integration_time(scan_set.counter_integration_time)
if input1_tol.set_bwidth(scan_set.tol_bwidth):
    print(f"Set bin width to {scan_set.tol_bwidth}")
if input1_tol.set_bcount(scan_set.tol_bcount):
    print(f"Set bin count to {scan_set.tol_bcount}")
if timecontroller.delay(1, scan_set.tol_delay):
    print(f"Set historgram delay for TOL to {scan_set.tol_delay}")



scan_sequencer = scan_set.initialize_step_sequencer()       # Initializes the sequencer, which is the object calculating the next movement of the positioner.

scan_res = scan_set.initialize_results()                    # Initializes the results, the object in chrge of storing data and saving/loading it to/from file.


## defining some functions for the main routine later:

############################## SCAN ROUTINE DEFINITION ###############################

def scan_motion(position_instruction: dict[str, float], scan_settings: ScanParameters, positioner: Positioner):


    actual_position=positioner.get_position(position_instruction["axis"])
    
    try_count=1
    while position_instruction["position"] != actual_position:
        positioner.move_to_position(position_instruction["axis"], position_instruction["position"])

        positioner.wait_end_motion(position_instruction["axis"], scan_settings.polling_frequency)
        #time.sleep(0.25) # safety sleep
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

############################### ToL MEASUREMENT FUNCTION ###############################
def measure_tol(step_index_vector: dict, scan_results: ScanResults, acquisition_time: int, tol: TCToL):
    data_obj = tol.acquire(acquisition_time)                                # Hangs for X seconds.
    scan_results.input_data(step_index_vector, data_obj)                    # Inputs the diagram and proceeds

############################### EXIT function, for when things go wrong ################

def exit(signum, frame):
    print(f"Received signal {signum} to stop.")
    if scan_started:
        for axis in axis_list:
            print(f"Stopping positioner {axis}")
            positioner.stop(axis)
        for i in ["start", 1]:
            print(f"Disabling timecontroller input {i}")
            timecontroller.disable_input(i)
        
    sys.exit(0)



# Installing Emergency Exit:

signal.signal(signal.SIGINT, exit)   # Ctrl+C
signal.signal(signal.SIGTERM, exit)  # kill <pid>


################################################ SCAN SECTION ####################################################

print(f"Tempo presvisto per scansione: {round(time_calculator(scan_set, count=True)/60, 1)} minuti.")
print("Tutto pronto. Premi invio...")
input()


scan_started = True
start_time = time.time()

## ZEROING ALL POSITIONER AXES 
for axis in axis_list:
    while not positioner.zero_position(axis):
        positioner.zero_position(axis)
        time.sleep(0.25)

    print(f"Zeroed {axis} axis.")
    time.sleep(0.25)


# here i initialise the index vector first so the first zeroeth step is registered correctly.
# this will be then ovveridden by the next_step_in_Sequence method by
# the sequencer each new iteration.

index_vector = {axis: 0 for axis in axis_list}

################################################### MAIN LOOP LOGIC ####################################################
while True:
    
    print(f"Current Position Index: {index_vector}")

    # Measurement stage:
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

    # Motion stage: the scan motion receives an instruction list from the sequencer. It moves the positioners to the correct positions and updates it's 
    # internal records.

    for instruction in motion_instructions:
        print(f"Moving Positioner to: {instruction}")
        
        scan_motion(instruction, scan_set, positioner)

    time.sleep(scan_set.sleep_time)   # Another optional sleep margin, although not necessary.

end_time=time.time()
print(f"Time Elapsed for Scan: {end_time-start_time} S")
##############################################################################################################################


scan_res.save(results_filepath)
scan_set.save(parameters_filepath)

print("Premi invio per uscire...")
input()
exit()

