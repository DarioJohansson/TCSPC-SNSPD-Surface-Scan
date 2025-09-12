import httpx

class CryoController:
    def __init__(self, IPaddress: str):
        self.IPaddress = IPaddress
        self.base_url = f"http://{IPaddress}:47101/v1"
        self.url = f"{self.base_url}/controller"
        self.vacuum_pump_url = f"{self.base_url}/vacuumSystem"
        self.raffreddatore_url = f"{self.base_url}/cooler"
        self.sample_chamber_url = f"{self.base_url}/sampleChamber"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.client = httpx.AsyncClient()

    async def get_status(self):
        response = await self.client.get(f"{self.url}/properties/systemState")
        return response.json()

    async def get_goal(self):
        response = await self.client.get(f"{self.url}/properties/systemGoal")
        return response.json()

    async def abort_goal(self) -> bool:
        response = await self.client.post(f"{self.url}/methods/abortGoal()")
        return response.status_code == 200

    async def get_pressure(self):
        response = await self.client.get(
            f"{self.vacuum_pump_url}/vacuumGauges/sampleChamberPressure/properties/pressureSample"
        )
        return response.json()["pressureSample"]

    async def pull_vacuum(self) -> bool:
        response = await self.client.post(f"{self.url}/methods/pullVacuum()")
        return response.status_code == 200

    async def vent(self) -> bool:
        response = await self.client.post(f"{self.url}/methods/vent()")
        return response.status_code == 200

    async def get_target_temperature(self):
        response = await self.client.get(f"{self.url}/properties/platformTargetTemperature")
        return response.json()["platformTargetTemperature"]

    async def set_target_temperature(self, temperature: float):
        data = {"platformTargetTemperature": temperature}
        response = await self.client.put(
            f"{self.url}/properties/platformTargetTemperature", json=data
        )
        return response.status_code == 200

    async def cooldown(self) -> bool:
        response = await self.client.post(f"{self.url}/methods/cooldown()")
        return response.status_code == 200

    async def warmup(self) -> bool:
        response = await self.client.post(f"{self.url}/methods/warmup()")
        return response.status_code == 200

    async def close(self):
        await self.client.aclose()



class Positioner:
    def __init__(self, IPaddress: str, step_vel: float = 1.0):
        self.base_url = f"http://{IPaddress}:47171/v1"
        self.axes_base_url = f"{self.base_url}/stacks/stack1/axes"
        self.axis_url = {
            'X': f"{self.axes_base_url}/axis2",
            'Y': f"{self.axes_base_url}/axis1",
            'Z': f"{self.axes_base_url}/axis3"
        }
        self.velocity = {'X': step_vel, 'Y': step_vel, 'Z': step_vel}
        self.client = httpx.AsyncClient()

    def _validate_axis(self, axis: str):
        if axis not in ['X', 'Y', 'Z']:
            raise ValueError("Axis must be 'X', 'Y', or 'Z'")

    async def status(self, axis: str) -> str:
        self._validate_axis(axis)
        response = await self.client.get(f"{self.axis_url[axis]}/properties/status")
        return response.json()['status']

    async def is_connected(self) -> bool:
        response = await self.client.get(f"{self.base_url}/motionController/properties/deviceConnected")
        return response.json()["deviceConnected"]

    async def get_velocity(self, axis: str) -> float:
        self._validate_axis(axis)
        response = await self.client.get(f"{self.axis_url[axis]}/properties/velocity")
        return response.json()["velocity"]

    async def stop(self, axis: str) -> bool:
        self._validate_axis(axis)
        response = await self.client.post(f"{self.axis_url[axis]}/methods/stop()")
        return response.status_code == 200

    async def move_to_position(self, axis: str, position: float) -> bool:
        self._validate_axis(axis)
        if not isinstance(position, (int, float)):
            raise ValueError("Position must be a numeric value")

        pos_str = format(position, '.17f')
        response = await self.client.post(
            f"{self.axis_url[axis]}/methods/moveAbsolute(double:pos)",
            content=pos_str,
            headers={"Content-Type": "text/plain"}
        )
        return response.status_code == 200

    async def zero_position(self, axis: str) -> bool:
        self._validate_axis(axis)
        response = await self.client.post(f"{self.axis_url[axis]}/methods/zero()")
        return response.status_code == 200

    async def move_to_limit(self, axis: str, direction: str = 'positive') -> bool:
        self._validate_axis(axis)
        if direction not in ['positive', 'negative']:
            raise ValueError("Direction must be 'positive' or 'negative'")

        method = "moveToPositiveLimit()" if direction == 'positive' else "moveToNegativeLimit()"
        response = await self.client.post(f"{self.axis_url[axis]}/methods/{method}")
        return response.status_code == 200

    async def set_velocity(self, axis: str, velocity: float) -> bool:
        self._validate_axis(axis)
        if not isinstance(velocity, (int, float)):
            raise ValueError("Velocity must be a numeric value")

        data = {"velocity": velocity}
        response = await self.client.put(f"{self.axis_url[axis]}/properties/velocity", json=data)
        return response.status_code == 200

    async def close(self):
        await self.client.aclose()
