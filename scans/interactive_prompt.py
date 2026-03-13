
from scans.scan_data_structures import ScanParameters, AVAILABLE_SCAN_TYPES
from scans.values import DEFAULT_IDQ_IP, DEFAULT_MONTANA_IP, SOFTWARE_VERSION


def print_banner():
    print(f"------------------ Welcome to the AutoPL Mapping Software - Version {SOFTWARE_VERSION} ----------------")
    print("Made By:     Dario Johansson - Scienze dei Materiali - Via Roberto Cozzi, 55 - 20126 Milano")
    print("Email:       dario.johansson@outlook.com\nGitHub:      https://github.com/DarioJohansson/TCSPC-SNSPD-Surface-Scan\n\n\n")



def interactive_prompt() -> ScanParameters:
    interactive_prompt = True
    parameters = ScanParameters()
    
    print_banner()

    while interactive_prompt:

        print("\n - DEVICE IPs:\n")

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

        
        print("\n\n - MONTANA SETTINGS:")
        print("\n1) Axis Settings:\n")

        # Resolution for each axis              
        for axis in ["X", "Y", "Z"]:
            res_input = input(f"Enter resolution (number of steps) for axis {axis}. Set to 0 to disable axis:  ")
            if res_input.strip():
                parameters.resolution[axis] = int(res_input)


        # Step size for each axis
        for axis in parameters.axis_list():
            current_step = parameters.step_size.get(axis, 0.0)
            step_input = input(f"Enter step size for axis {axis} in metres (current: {current_step})\n(use scientific notation if needed: '10e-5' equals 10 microns): ")
            if step_input.strip():
                parameters.step_size[axis] = float(step_input)

        print("\n2) Scan Motion Algorithm Selection:\n")
        
        while True:
            # Scan type
            type_input = input(f"Enter scan motion type (available: {AVAILABLE_SCAN_TYPES}) (current: {parameters.scan_type}): ")
            if type_input.strip():
                if type_input in AVAILABLE_SCAN_TYPES:    
                    parameters.scan_type = type_input
                    break
                else:
                    print("Entered invalid type. Try again.")
            else:
                print(f"defaulting to {parameters.scan_type}")
                break
            
        print("\n\n - IDQ (Time Tagger) DETECTOR SETTINGS:")
        print("\n1) Time Tagger Counter Settings:\n")


        while True:
            # Counter integration time
            cit_input = input(f"Enter counter integration time in ms (current: {parameters.counter_integration_time}): ")
            if cit_input.strip():
                try:
                    parameters.counter_integration_time = int(cit_input)
                    break
                except:
                    print("Value incompatible. Retry.")
            else:
                print(f"defaulting to {parameters.counter_integration_time}")
                break

        print("\n2) Time Tagger TRPL Settings:\n")
        
        while True:   
            # TRPL Settings
            acq_time_input = input(f"Enter TRPL acquisition time in seconds  (set to 0 to disable TRPL) (current: {parameters.tol_acquisition_time}): ")
            if acq_time_input.strip():
                try:
                    parameters.tol_acquisition_time = int(acq_time_input)
                    break
                except:
                    print("Value incompatible. Retry.")
            else:
                print(f"defaulting to {parameters.tol_acquisition_time}")
                break


        if parameters.tol_acquisition_time > 0:
            
            while True:
                bcount_input = input(f"Enter TRPL bin count (current: {parameters.tol_bcount}): ")
                if bcount_input.strip():
                    try:
                        parameters.tol_bcount = int(bcount_input)
                        break
                    except:
                        print("Value incompatible. Retry.")
                else:
                    print(f"defaulting to {parameters.tol_bcount}")
                    break

            while True:
                bwidth_input = input(f"Enter TRPL bin width in ps (current: {parameters.tol_bwidth}): ")
                if bwidth_input.strip():
                    try:
                        parameters.tol_bwidth = int(bwidth_input)
                        break
                    except:
                        print("Value incompatible. Retry.")
                else:
                    print(f"defaulting to {parameters.tol_bwidth}")
                    break

            
            while True:
                delay_input = input(f"Enter TRPL bin delay in ps (current: {parameters.tol_delay}): ")
                if delay_input.strip():
                    try: 
                        parameters.tol_delay = int(delay_input)
                        break
                    except:
                        print("Value incompatible. Retry.")
                else:
                    print(f"defaulting to {parameters.tol_delay}")
                    break

        print("\n3) Additional Device Stabilization Delay:\n")

        # Sleep time
        sleep_input = input(f"Enter additional sleep time for each step in seconds (current: {parameters.sleep_time}): ")
        if sleep_input.strip():
            parameters.sleep_time = float(sleep_input)

        
        # Input list. Defines which input is active in the receptikon of photons from the samples. START trigger channel is on by default with a threshold of -0.3.
        # The user can select the remaining input channel or leave default at "1"

        print("\n4) Low Level Parameters for Detection (leave unchanged if unsure):\n")
        
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
        print(f"  Scan Algorithm: {parameters.scan_type}")
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
