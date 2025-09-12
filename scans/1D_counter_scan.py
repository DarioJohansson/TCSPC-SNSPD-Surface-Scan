

'''

First iteration of scan on a sample. This scan's structure must be something of the kind:
- Initiate necessary devices in correct order with hardcoded addresses
- Create data structure for measurements, which is a list with positions and counts

- Create a step list in sequence, which means a list populated by the values in which the nanopositioner will have to step on.
- The nanopositioner then zeroes it's position
- Sets a velocity
- The timecontroller records count and DataCount object has a time and frequency information.

'''
from devices.idq_tc1000_counter import *
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

tc = connect("149.132.99.103")   # Connection for IDQ
montana_ip = "149.132.99.104"


# Preparation of IDQ TC
try:
    timecontroller = TimeController(tc)
    start_counter = TCCounter(tc, "start")
    input1_counter = TCCounter(tc, 1)
    if not timecontroller.threshold(1, -0.1):
        print("could not set threshold")
        exit()

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

# Operational Parameters:

scan_set = ScanParameters()
axis='Z'
scan_set.step_size["Z"]=0.000005   # metres
scan_set.step_velocity=50 * 1e-6    # meters/sec  ##IMPLEMENT THIS IN THE POSITIONER CLASS. doing it manually from screen
scan_set.resolution["Z"]=200
scan_set.create_step_sequence()


#Preparation of Data Structures 

scan_res = ScanResults({"X": 0, "Y": 0, "Z": scan_set.resolution["Z"]})

############################## SCAN ROUTINE DEFINITION ###############################

def scan_routine(position, scan_settings, results, counter, positioner, axis):

    def wait_end_motion():
        start=time.time()
        
        while True:
            if positioner.status(axis)["moving"] == False:
                break
            time.sleep(1/scan_settings.polling_frequency)
        
        end=time.time()
        print(f"Waited for motion {(end-start)*1000} mS")
        return

    print(f"Step: {position[axis]}")    
    
    actual_position=round(positioner.status(axis)["theoreticalPosition"], 9)
    try_count=1
    
    while scan_settings.step_matrix[axis][position[axis]] != actual_position:
        positioner.move_to_position(axis, scan_settings.step_matrix[axis][position[axis]])
        wait_end_motion()
        time.sleep(0.5) # safety sleep
        actual_position=round(positioner.status(axis)["theoreticalPosition"], 9)
        print(f"Try: {try_count}\nTheoretical Position: {scan_settings.step_matrix[axis][position[axis]]}\nActual reported position: {actual_position}")
        try_count+=1

    pos = tuple(value for value in position.values())
    results.input_data(pos, [counter.count()])                 # Record Y value from counter frequency




    time.sleep(scan_settings.sleep_time)

########################################################################################




def exit():
    print("Received signal to stop.")
    positioner.stop(axis)
    for i in ["start", 1]:
        timecontroller.disable_input(i)
    
    sys.exit(0)


# Emergency Exit:
signal.signal(signal.SIGINT, exit)   # Ctrl+C
signal.signal(signal.SIGTERM, exit)  # kill <pid>


# Main logic:
try:

    print("Tutto pronto. Premi invio...")
    input()

    start_time = time.time()
    positioner.zero_position(axis)

    for step_index in range(0, scan_set.resolution["Z"]):
        
        position = {"Z": step_index}
        scan_routine(position, scan_set, scan_res, input1_counter, positioner, "Z")

    end_time=time.time()
    print(f"Time Elapsed for Scan: {end_time-start_time} S")

    X_DATA = [x * 1e6 for x in scan_set.step_matrix["Z"]]
    Y_DATA = []

    for i in range(0, scan_set.resolution["Z"]):
        pos = (i,)
        frequency = scan_res.get_data(pos)[0].frequency()
        Y_DATA.append(frequency)

    fig, ax = plt.subplots()
    ax.plot(X_DATA, Y_DATA)
    ax.set_title("1D Scan - 200 x 5 Micrometer Steps", fontsize=14, fontweight="bold")
    ax.set_xlabel("Position (microM)", fontsize=10)
    ax.set_ylabel("Photon incidence frequency (Hz)", fontsize=9)
    ax.xaxis.set_major_locator(MultipleLocator(100))
    ax.yaxis.set_major_locator(MultipleLocator(300))
    ax.grid(True, linestyle="--", alpha=0.6)
    
    plt.savefig("1D-sweep-100microns-sec-2.png", dpi=500)

    scan_res.save("/home/dario/Temp/scan-dump.json")
    scan_set.save("/home/dario/Temp/scan-settings.json")

    print("Premi invio per uscire...")
    input()

except Exception as e:
    print(e)
    exit()