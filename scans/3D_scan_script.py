# Local dependencies
from devices.idq_tc1000_device import TimeController
from devices.montana_cryoadvance_controls import Positioner
from scans.scan_data_structures import ScanParameters, ScanResults, TCCounter, TCToL
from components.service_config.argparser import build_arg_parser
from components.service_config.service_config import ServiceConfig

# Packaged Dependencies 
import tkinter as tk
from tkinter import filedialog  # File selection prompts.
import time
import signal
import sys
import os
import builtins
from datetime import datetime
now = datetime.now() # current date and time



DEFAULT_IDQ_IP="169.254.207.101"
DEFAULT_MONTANA_IP="192.168.1.2"
results_filepath = None
parameters_filepath = None

allowed_filetype_extensions = [("JSON", "*.json")]

## some util functions for the scan routine.

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


def select_directory(msg: str = "Select a directory") -> str:
    # Hide the root window
    root = tk.Tk()
    root.withdraw()

    try:
        # Open directory selection dialog
        directory = filedialog.askdirectory(
            title=msg
        )

        if directory:
            root.destroy()
            return directory

        else:
            print("No directory selected.")
            root.destroy()
            return ""
        
    except Exception as e:
        print(e)
        root.destroy()

    

def select_file(msg: str = "Select a file") -> str:
    root = tk.Tk()
    root.withdraw()  # Hide the main window


    try:
        file_path = filedialog.askopenfilename(
            title=msg,
            filetypes=allowed_filetype_extensions
        )

        if file_path:
            root.destroy()
            return file_path
        else:
            print("No file selected.")
            root.destroy()
            return ""
    
    except Exception as e:
        print(e)
        root.destroy()

    
def new_file(msg: str = "Choose new file") -> str:
    root = tk.Tk()
    root.withdraw()  # Hide the main window


    try:
        file_path = filedialog.asksaveasfilename(
            title=msg,
            filetypes=allowed_filetype_extensions
        )

        if file_path:
            root.destroy()
            return file_path
        else:
            print("No file selected.")
            root.destroy()
            return ""
    
    except Exception as e:
        print(e)
        root.destroy()

    
# Function which emits a tuple of strings representing respectively the results save file path and the parameters save file path from a base save directory.
# It interactively asks for a save dir if none is given.
# It returns None if the directory cannot be written to or the files in the dir already exist.

def results_file_path(save_config_path: str = None, msg: str = "Select Directory to Save Results") -> str | None:
    
    save_name = now.strftime("%m-%d-%Y--%H-%M-%S") + "-PLMap"
    
    if save_config_path is None:
        while True:
            save_config_path = select_directory(msg=msg)
            if os.access(save_config_path, os.W_OK):
                break
            print("Directory not accessible, try again.")

    if save_name.strip():          ## Also checks if the name string is nonempty
        base_dir = os.path.dirname(os.path.abspath(save_config_path)) or '.'

        if not os.path.isdir(base_dir) or not os.access(base_dir, os.W_OK):
            print(f"Filepath '{save_config_path}' invalid (not accessible or non-existent)")
            sys.exit(1)

        results_filename = os.path.join(save_config_path, save_name + "_results.json")
        
    
        if os.path.exists(results_filename):
            print(f"The file {results_filename} already exists.")
            return None

        
        return results_filename
    

    


def interactive_prompt() -> ScanParameters:
    interactive_prompt = True
    parameters = ScanParameters()
    
    while interactive_prompt:

        # Device IP Addresses:
        idq_ip_input = input(f"Input the IP address of the IDQ Time Tagger device or press Enter to keep {DEFAULT_IDQ_IP}: ")
        montaina_ip_input = input(f"Input the IP address of the Montana CryoAdvance device or press Enter to keep {DEFAULT_MONTANA_IP}: ")

        if idq_ip_input.strip():
            parameters.idq_timetagger_ip = idq_ip_input
        else:
            parameters.idq_timetagger_ip = DEFAULT_IDQ_IP

        if montaina_ip_input.strip():
             parameters.montana_cryoadvance_ip = montaina_ip_input
        else:
            parameters.montana_cryoadvance_ip = DEFAULT_MONTANA_IP

        # Resolution for each axis              
        for axis in ["X", "Y", "Z"]:
            res_input = input(f"Enter resolution (number of steps) for axis {axis}. Set to 0 to disable axis:  ")
            if res_input.strip():
                parameters.resolution[axis] = int(res_input)

        print(f"DEBUG: axes: {parameters.resolution}")

        # Step size for each axis
        for axis in parameters.axis_list():
            current_step = parameters.step_size.get(axis, 0.0)
            step_input = input(f"Enter step size for axis {axis} in metres (current: {current_step}): ")
            if step_input.strip():
                parameters.step_size[axis] = float(step_input)

        # Counter integration time
        cit_input = input(f"Enter counter integration time in ms (current: {parameters.counter_integration_time}): ")
        if cit_input.strip():
            parameters.counter_integration_time = int(cit_input)

        # Tolerances
        acq_time_input = input(f"Enter TRPL acquisition time in seconds  (set to 0 to disable TRPL) (current: {parameters.tol_acquisition_time}): ")
        if acq_time_input.strip():
            parameters.tol_acquisition_time = int(acq_time_input)

        if parameters.tol_acquisition_time > 0:
            bcount_input = input(f"Enter TRPL bin count (current: {parameters.tol_bcount}): ")
            if bcount_input.strip():
                parameters.tol_bcount = int(bcount_input)

            bwidth_input = input(f"Enter TRPL bin width in ps (current: {parameters.tol_bwidth}): ")
            if bwidth_input.strip():
                parameters.tol_bwidth = int(bwidth_input)

            delay_input = input(f"Enter TRPL bin delay in ps (current: {parameters.tol_delay}): ")
            if delay_input.strip():
                parameters.tol_delay = int(delay_input)

        # Sleep time
        sleep_input = input(f"Enter additional sleep time for each step in seconds (current: {parameters.sleep_time}): ")
        if sleep_input.strip():
            parameters.sleep_time = float(sleep_input)

        
        # Input list. Defines which input is active in the receptikon of photons from the samples. START trigger channel is on by default with a threshold of -0.3.
        # The user can select the remaining input channel or leave default at "1"

        tagger_input = input(f"Enter the input channel number (default: 1): ")
        
        if tagger_input.strip():
            if tagger_input in parameters.input_thresholds.keys() and tagger_input != "start":
                
                # Zeroing the values
                for channel in parameters.input_thresholds.keys():
                    if channel != "start":
                        parameters.input_thresholds[channel] = None
                
                # Setting the value at the determined input channel.
                parameters.input_thresholds[tagger_input] = -0.1

            else:
                print("Input channel invalid.") # Case where the channel string is not an expected value.
        
        
        for channel,value in parameters.input_list().items():

            threshold_input = input(f"Enter voltage threshold for input signal detection on channel {channel} (current: {value}): ")
            try:
                if threshold_input.strip():
                    parameters.input_thresholds[channel] = float(threshold_input.strip())
            except Exception as e:
                print(f"Input is invalid. More details: {e}\n Try Again.")
            

        # Final confirmation
        print("\nUpdated scan settings:")
        
        print(f"  Time Tagger IP Address: {parameters.idq_timetagger_ip}")
        print(f"  Montana CryoAdvance IP Address: {parameters.montana_cryoadvance_ip}")
        print(f"  Active Axes: {parameters.axis_list()}")
        print(f"  Step size {axis}: {parameters.step_size} m")
        print(f"  Resolution {axis}: {parameters.resolution}")
        print(f"  Counter integration time: {parameters.counter_integration_time} ms")
        print(f"  TRPL Acquisition time (s): {parameters.tol_acquisition_time}")
        print(f"  TRPL Bin count: {parameters.tol_bcount}")
        print(f"  TRPL Bin width (ps): {parameters.tol_bwidth}")
        print(f"  TRPL Delay (ps): {parameters.tol_delay}")
        print(f"  Sleep time (s): {parameters.sleep_time}")
        
        for channel,value in parameters.input_list().items():
            print(f"  Voltage Threshold on Time Tagger for channel {channel}: {value} V")

        print("\n\n")
        
        while True:
            final_confirmation = input("Do these settings look good? y/n/abort\n")
            if final_confirmation in ['y','Y','yes','si']:
                interactive_prompt = False
                break
            elif final_confirmation in ['n', 'N', 'no']:
                break
            elif final_confirmation in ['abort', 'ABORT']:
                exit()
            else:
                print(f"What do you mean by {final_confirmation}?\nLet's try again:")

    return parameters



#################################################################################

###################### Case Switch for User Interaction #########################



parser = build_arg_parser()
args = parser.parse_args()
scan_set = None


if args.config_from_file is not None:

    if args.config_from_file is not False:
        path = args.config_from_file
        if not os.access(path, os.R_OK):
            print(f"Error: filepath {path} doesn't exist or unreadable.")
            sys.exit(1)

    else:
        input("Press enter to select configuration file interactively...")
        path = select_file()
    
    scan_set = ScanParameters.from_json(path=path)
    


elif args.save_config is not None:
    
    if args.save_config is not False:
        
        try:

            scan_set : ScanParameters = interactive_prompt()
            path = args.save_config
            parent = os.path.dirname(path)
            if os.access(parent, os.W_OK | os.X_OK) and os.path.isdir(parent):
                print("Saving config to following path:")
                print(path)
                scan_set.to_json(path)
                sys.exit(0)
            else:
                print("Path to save configuration is not accessible:")
                print(f"Path: {path}")
                sys.exit(1)
        
        except Exception as e:
            print("Something went wrong while saving config to file. Aborting.")
            print(e)
            sys.exit(1)

    else:

        print("Select path to save configuration...")
        filepath = new_file(msg="Saving configuration file")
        
        try:
            scan_set : ScanParameters = interactive_prompt()
            parent = os.path.dirname(filepath)
            if os.access(parent, os.W_OK | os.X_OK) and os.path.isdir(parent):
                print("Saving config to following path:")
                print(filepath)
                scan_set.to_json(filepath)
                sys.exit(0)
            else:
                print("Path to save configuration is not accessible:")
                print(f"Path: {filepath}")
                sys.exit(1)
        
        except Exception as e:
            print("Something went wrong while saving config to file. Aborting.")
            print(e)
        
else:
    
    scan_set: ScanParameters = interactive_prompt()        


## Defining save path for results:

print("Select a directory to save results:")
results_filepath = results_file_path()

########################## Preparation of IDQ TC ################################

try:
    timecontroller = TimeController(scan_set.idq_timetagger_ip)
    start_counter = timecontroller.get_counter("start")
    input1_counter = timecontroller.get_counter(1)
    input1_tol = timecontroller.get_tol(1)


except Exception as e:
    print(f"Error during preparation of IDQ: {e}")


############################# Preparation of Montana ###############################
try:
    positioner = Positioner(scan_set.montana_cryoadvance_ip)

except Exception as e:
    print(f"Error during preparation of Montana: {e}")





####################################################################################       Configuration stage is over. Now settings will be applied.
############################# Apply Scan Settings ###############################



# Applying some settings here.
for input,value in scan_set.input_list().items():

    while not timecontroller.threshold(input, value):
        print("Could not set voltage threshold. Retrying")
        time.sleep(0.5)
        
    if timecontroller.enable_input(input):
        print(f"Enabled input {input} on timetagger.")
    else:
        print(f"Could not enable input {input} on timetagger. Consider aborting operation.")


print(f'Threshold on Start: {timecontroller.threshold("start")}\nThreshold on Input 1: {timecontroller.threshold(1)}\n')

input1_counter.set_integration_time(scan_set.counter_integration_time)
if input1_tol.set_bwidth(scan_set.tol_bwidth):
    print(f"Set bin width to {scan_set.tol_bwidth}")
if input1_tol.set_bcount(scan_set.tol_bcount):
    print(f"Set bin count to {scan_set.tol_bcount}")
if timecontroller.delay(1, scan_set.tol_delay):
    print(f"Set historgram delay for TOL to {scan_set.tol_delay}")


# More data structure initialization 

scan_sequencer = scan_set.initialize_step_sequencer()       # Initializes the sequencer, which is the object calculating the next movement of the positioner.

scan_res = scan_set.initialize_results()                    # Initializes the results, the object in chrge of storing data and saving/loading it to/from file.


# defining some functions for the main routine later:

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

############################### EXIT function, for when things go wrong or terminate ################

def exit(signum, frame):
    print(f"Received signal {signum} to stop.")

    for axis in scan_set.axis_list():
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
ignore = builtins.input()


scan_started = True
start_time = time.time()

## ZEROING ALL POSITIONER AXES 
for axis in scan_set.axis_list():
    while not positioner.zero_position(axis):
        positioner.zero_position(axis)
        time.sleep(0.25)

    print(f"Zeroed {axis} axis.")
    time.sleep(0.25)


# here i initialise the index vector first so the first zeroeth step is registered correctly.
# this will be then ovveridden by the next_step_in_Sequence method by
# the sequencer each new iteration.

index_vector = {axis: 0 for axis in scan_set.axis_list()}

################################################### MAIN LOOP LOGIC ####################################################
while True:
    
    print(f"Current Position Index: {index_vector}")

    # Measurement stage:
    if scan_set.counter_integration_time > 0:
        print("Measuring photon incidence freq:")
        measure_frequency(index_vector, scan_res, input1_counter)
    if scan_set.tol_acquisition_time > 0:
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
scan_set.to_json(parameters_filepath)

print("Premi invio per uscire...")
builtins.input()
exit()

