
import requests # type: ignore
import json

class InformazioniMontana:
    def __init__(self, IPaddress: str) -> str:
        self.controller_url = f"http://{IPaddress}:47101/v1"
        self.positioner_url = f"http://{IPaddress}:47171/v1"

    def informazioni_pompa_raffreddatrice(self, format: bool = False) -> dict:
        """
        Queries all GET /properties endpoints and returns a full snapshot of cryocooler data.
        
        Args:
            controller_url (str): Base URL like 'http://ipaddress:port/v1/cooler/cryocooler'
        
        Returns:
            dict: Aggregated JSON with all machine info from GET requests
        """
        endpoints = {
            "cryocoolerRunning": "/properties/cryocoolerRunning",
            "deviceConnected": "/properties/deviceConnected",
            "compressorHours": "/properties/compressorHours",
            "cryocoolerSpeed": "/properties/cryocoolerSpeed",
            "compressorSpeed": "/properties/compressorSpeed",
            "minAllowedCompressorSpeed": "/properties/minAllowedCompressorSpeed",
            "maxAllowedCompressorSpeed": "/properties/maxAllowedCompressorSpeed",
            "targetCompressorSpeed": "/properties/targetCompressorSpeed",
            "minAllowedCryocoolerSpeed": "/properties/minAllowedCryocoolerSpeed",
            "maxAllowedCryocoolerSpeed": "/properties/maxAllowedCryocoolerSpeed",
            "targetCryocoolerSpeed": "/properties/targetCryocoolerSpeed",
            "returnPressure": "/properties/returnPressure",
            "supplyPressure": "/properties/supplyPressure",
            "alarms": "/properties/alarms",
            "compressorDischargeTemperature": "/properties/compressorDischargeTemperature",
            "firmwareVersion": "/properties/firmwareVersion",
            "operatingHours": "/properties/operatingHours",
            "operationState": "/properties/operationState",
            "waterInletTemperature": "/properties/waterInletTemperature",
            "waterOutletTemperature": "/properties/waterOutletTemperature"
        }

        result = {}

        for key, path in endpoints.items():
            try:
                response = requests.get(f"{self.controller_url}{path}", timeout=5)
                response.raise_for_status()
                result[key] = response.json()
            except requests.RequestException as e:
                result[key] = {"error": str(e)}
        if format:
            return json.dumps(result, indent=4)
        else:
            return result


    def informazioni_controllore(self, format: bool = False) -> str:
        """
        Collects all available GET /controller/properties/* values from the CryoAdvance/CryoCore system.
        
        Args:
            controller_url (str): Base API URL (e.g., 'http://ipaddress:47101/v1')
        
        Returns:
            dict: Aggregated JSON with all controller data
        """
        endpoints = {
            "canAbortGoal": "/controller/properties/canAbortGoal",
            "canCooldown": "/controller/properties/canCooldown",
            "canPullVacuum": "/controller/properties/canPullVacuum",
            "canVent": "/controller/properties/canVent",
            "canWarmup": "/controller/properties/canWarmup",
            "cryoOpticTargetTemperature": "/controller/properties/cryoOpticTargetTemperature",
            "dryNitrogenPurgeEnabled": "/controller/properties/dryNitrogenPurgeEnabled",
            "dryNitrogenPurgeNumTimes": "/controller/properties/dryNitrogenPurgeNumTimes",
            "maxPlatformTargetTemperature": "/controller/properties/maxPlatformTargetTemperature",
            "platformBakeoutEnabled": "/controller/properties/platformBakeoutEnabled",
            "platformBakeoutTemperature": "/controller/properties/platformBakeoutTemperature",
            "platformBakeoutTemperatureLimit": "/controller/properties/platformBakeoutTemperatureLimit",
            "platformBakeoutTime": "/controller/properties/platformBakeoutTime",
            "platformTargetTemperature": "/controller/properties/platformTargetTemperature",
            "pullVacuumTargetPressure": "/controller/properties/pullVacuumTargetPressure",
            "runTurbopumpContinuouslyDuringCooldown": "/controller/properties/runTurbopumpContinuouslyDuringCooldown",
            "systemGoal": "/controller/properties/systemGoal",
            "systemState": "/controller/properties/systemState",
            "turbopumpPreCoolingTargetPressure": "/controller/properties/turbopumpPreCoolingTargetPressure",
            "turbopumpPreCoolingTimeLimit": "/controller/properties/turbopumpPreCoolingTimeLimit",
            "ventContinuouslyEnabled": "/controller/properties/ventContinuouslyEnabled"
        }

        result = {}
        
        for key, path in endpoints.items():
            try:
                response = requests.get(f"{self.controller_url}{path}", timeout=5)
                response.raise_for_status()
                result[key] = response.json()
            except requests.RequestException as e:
                result[key] = {"error": str(e)}
        
        if format:
            return json.dumps(result, indent=4)
        else:
            return result

    def informazioni_posizionatore(self, format: bool = False) -> str:
        """
        Collects all available GET /controller/properties/* values from the Rook Nanopositioner system.
        
        Args:
            positioner_url (str): Base API URL (e.g., 'http://ipaddress:47171/v1')
        
        Returns:
            dict: Aggregated JSON with all controller data
        """
        endpoints = {
            "canAbortGoal": "/controller/properties/canAbortGoal",
            "status - axisX": "/stacks/stack1/axes/axis1/properties/status",
            "status - axisY": "/stacks/stack1/axes/axis2/properties/status",
            "status - axisZ": "/stacks/stack1/axes/axis3/properties/status",
            "velocity - axisX": "/stacks/stack1/axes/axis1/properties/velocity",
            "velocity - axisY": "/stacks/stack1/axes/axis2/properties/velocity",
            "velocity - axisZ": "/stacks/stack1/axes/axis3/properties/velocity"
        }

        result = {}
        
        for key, path in endpoints.items():
            try:
                response = requests.get(f"{self.positioner_url}{path}", timeout=5)
                response.raise_for_status()
                result[key] = response.json()
            except requests.RequestException as e:
                result[key] = {"error": str(e)}
        
        if format:
            return json.dumps(result, indent=4)
        else:
            return result