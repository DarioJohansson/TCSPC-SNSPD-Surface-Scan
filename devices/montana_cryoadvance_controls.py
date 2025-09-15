'''
Dario Johansson - Tesi in Automazione e Interconnessione di dispositivi volti all'esperimento di Mappatura di Superfici

Questo modulo è incentrato sulla dichiarazione delle variabili funzionali e la definizione degli oggetti utilizzati per connettersi
e prendere il controllo del CrioGeneratore Monana CryoAdvance-50.


'''

import requests
import json
import time


def string_or_json(data, string: bool):
    if string:
        return json.dumps(data, indent=4)
    else:
        return data

############################################## Main CryoController Functions ############################################

class CryoController:

    def __init__(controller, IPaddress):
        
        if not IPaddress or type(IPaddress) is not str:
            raise ValueError("CryoController.__init__(): IP address must be provided")
            
        controller.IPaddress = IPaddress
        controller.base_url = f"http://{IPaddress}:47101/v1"
        controller.url = f"http://{IPaddress}:47101/v1/controller"
        controller.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        controller.vacuum_pump_url = controller.base_url + "/vacuumSystem"
        controller.raffreddatore_url = controller.base_url + "/cooler"
        controller.sample_chamber_url = controller.base_url + "/sampleChamber" 
    
    def get_status(controller, string: bool = False):
        response = requests.get(f"{controller.url}/properties/systemState")
        response_json = response.json()
        if string:
            return json.dumps(response_json, indent=4)
        else: 
            return response_json
    
    def get_goal(controller, string: bool = False):
        response = requests.get(f"{controller.url}/properties/systemGoal")
        response_json = response.json()
        if string:
            return json.dumps(response_json, indent=4)
        else: 
            return response_json

    def abort_goal(controller):
        response = requests.post(f"{controller.url}/methods/abortGoal()")
        return response.status_code == 200

    
############################################## vacuum system functions #################################################

    def get_target_pressure(controller):
        response = requests.get(f"{controller.url}/properties/pullVacuumTargetPressure")
        response_json = response.json()
        
        return response_json['pullVacuumTargetPressure']

    def get_pressure(controller, string: bool = False):
        response = requests.get(f"{controller.vacuum_pump_url}/vacuumGauges/sampleChamberPressure/properties/pressureSample")
        response_json = response.json()
        return response_json['pressureSample']

    def pull_vacuum(controller):
        response = requests.post(f"{controller.url}/methods/pullVacuum()")
        return response.status_code == 200
    
    def vent(controller):
        response = requests.post(f"{controller.url}/methods/vent()")
        return response.status_code == 200


################################################ cooler functions #####################################################

    def get_target_temperature(controller):
        response = requests.get(f"{controller.url}/properties/platformTargetTemperature")
        response_json = response.json()
        return response_json["platformTargetTemperature"]
    
    def set_target_temperature(controller, temperature):
        data = {"platformTargetTemperature": temperature}
        response = requests.put(f"{controller.url}/properties/platformTargetTemperature", json=data)
        return response.status_code == 200

    def cooldown(controller):
        response = requests.post(f"{controller.url}/methods/cooldown()")
        return response.status_code == 200
    
    def warmup(controller):
        response = requests.post(f"{controller.url}/methods/warmup()")
        return response.status_code == 200


#####################################################################################################################




######################################### Rookie Nanopositioner Functions ###########################################

class Positioner:
    def __init__(self, IPaddress: str, step_vel: float = 1.0):
        step_vel = float(step_vel)
        self.base_url = f"http://{IPaddress}:47171/v1"
        self.axes_base_url = f"{self.base_url}/stacks/stack1/axes"
        self.axis_url = {'X': f"{self.axes_base_url}/axis2", 'Y': f"{self.axes_base_url}/axis1", 'Z': f"{self.axes_base_url}/axis3"}
        self.velocity = {'X': step_vel, 'Y': step_vel, 'Z': step_vel}

    @staticmethod
    def __validate_axis(axis):
        if axis not in ['X', 'Y', 'Z']:
            raise ValueError("Axis must be 'X', 'Y', or 'Z'")
        return axis


    def status(self, axis: str = '') -> dict:
        axis = self.__validate_axis(axis)
        
        response = requests.get(f"{self.axis_url[axis]}/properties/status")
        response_json = response.json()
        return response_json['status']

    def is_connected(self) -> bool:
        response = requests.get(f"{self.base_url}/motionController/properties/deviceConnected")
        response_json = response.json()
        return response_json["deviceConnected"]
    
    def get_position(self, axis: str = "") -> float:
        axis = self.__validate_axis(axis)
        
        return round(self.status(axis)["theoreticalPosition"], 9)
    
    def get_velocity(self, axis: str = '') -> list:
        axis = self.__validate_axis(axis)
        
        response = requests.get(f"{self.axis_url[axis]}/properties/velocity")
        response_json = response.json()
        return response_json["velocity"]


    def stop(self, axis: str = '') -> bool:
        axis = self.__validate_axis(axis)
        
        response = requests.post(f"{self.axis_url[axis]}/methods/stop()")
        return response.status_code == 200
    
    
    def move_to_position(self, axis: str = '', position: int|float = None) -> bool:
        axis = self.__validate_axis(axis)

        if not isinstance(position, (int, float)):
            raise ValueError("Position must be a numeric value")
        # Assuming we have a method to set the position on the device
        # Set position on the device for the specified axis
        position = format(position, '.17f')
        response = requests.post(f"{self.axis_url[axis]}/methods/moveAbsolute(double:pos)", data=position, headers={"Content-Type": "text/plain"})
                
        return response.status_code == 200

    def zero_position(self, axis: str = '') -> bool:
        axis = self.__validate_axis(axis)

        response = requests.post(f"{self.axis_url[axis]}/methods/zero()")
        return response.status_code == 200

    def move_to_limit(self, axis: str = '', direction: str = 'positive') -> bool:
        axis = self.__validate_axis(axis)

        if direction not in ['positive', 'negative']:
            raise ValueError("Direction must be 'positive' or 'negative'")
        
        method = "moveToPositiveLimit()" if direction == 'positive' else "moveToNegativeLimit()"
        response = requests.post(f"{self.axis_url[axis]}/methods/{method}")
        return response.status_code == 200

    def set_velocity(self, axis: str = '', velocity: int|float = None) -> bool:
        axis = self.__validate_axis(axis)

        if not isinstance(velocity, (int, float)):
            raise ValueError("Position must be a numeric value")
        pass                
        # Set velocity on the device

    def wait_end_motion(self, axis: str = '', polling_frequency = 100):

        start=time.time()
        
        while self.status(axis)["moving"]:
            time.sleep(1/polling_frequency)

        end=time.time()

        return {round(end-start, 6)}