from utils.common import zmq_exec, connect
from devices.idq_tc1000_counter import *
from devices.idq_tc1000_tol import *

class TimeController:
    def __init__(self, machine_ip = None, verbose: bool = False):
        if machine_ip == None or type(machine_ip) != str:
            raise ValueError("TimeController: need to provide me with a valid zmq connection context object.")
        
        self.verbose = verbose
        self.connection = connect(machine_ip)
        self.devices = []
        self.status = {}

        
    def get_status(self) -> dict:
        
        blob = zmq_exec(self.connection, "STAT?").upper()
        result = {}

        lines = blob.strip().split('\n')

        for line in lines:
            if not line.strip():
                continue

            parts = line.strip().split(':')

            base_path = []
            kv_tokens = []

            # Split line into path + last token (which contains key-value pairs)
            for i, part in enumerate(parts):
                if ' ' in part or ';' in part:
                    base_path = parts[:i]
                    kv_tokens = ':'.join(parts[i:]).split(';')
                    break
            else:
                base_path = parts
                kv_tokens = []

            prefix = ':'.join(base_path).strip().upper()

            for token in kv_tokens:
                token = token.strip()
                if not token:
                    continue

                if ' ' in token:
                    key, value = token.split(' ', 1)
                    full_key = f"{prefix}:{key.strip().upper()}"
                    result[full_key] = value.strip()
                else:
                    # single flag token like "ENAB"
                    full_key = f"{prefix}:{token.strip().upper()}"
                    result[full_key] = True

        return result

    def get_counter(self, input: int|str = None):
        if input == None:
            raise ValueError("TimeController.get_counter(): did not supply an input channel.")
        
        self.devices.append(TCCounter(self.connection, input))
        return self.devices[-1]
    
    def get_tol(self, input: 1|2|3|4 = None):
        if input == None:
            raise ValueError("TimeController.get_tol(): did not supply an input channel.")
        self.devices.append(TCToL(self.connection, input))
        return self.devices[-1]

    def remove_device(self, device):
        if device in self.devices:
            self.devices.remove(device)
            return True
        return False
    
    @staticmethod
    def _input_channel_parser(input):
        if not input or (type(input) != int and type(input) != str):
            raise ValueError("TimeController._input_channel_parser(): invalid input type supplied.")
        elif type(input) == int and input not in range(1,5):
            raise ValueError(f"TimeController._input_channel_parser(): input channel \"{input}\" outside of bounds.")
        elif type(input) == str and input.upper() == "START":
            return "STAR"
        elif type(input) == str and input.upper() != "START":
            raise ValueError(f"TimeController._input_channel_parser(): \"{input}\" is not a valid input channel.")
        else:
            return f"INPU{input}"
        
        '''
    def set_delay(self, delay: int):
        if delay:
            response = zmq_exec(self.connection, f"HIST{self.input}: {delay}")
            if response.upper().strip() == f"VALUE SET TO {delay}":
                return True
            if self.verbose:
                print(f"TCToL.set_bcount(): Error from device -> {response}")
            return False
        
        else:
            raise ValueError(f"TCToL.set_bcount(): invalid bin count supplied: {delay}")
    '''
            
    def threshold(self, input: int|str, threshold: int|float = None) -> str|bool:
        if type(threshold) not in [float, int] and threshold != None:
            raise ValueError("TimeController.set_threshold(): invalid threshold type supplied.")
        
        elif threshold == None:
            input = self._input_channel_parser(input)
            response = zmq_exec(self.connection, f"{input}:THRE?")
            try:
                response = float(response.replace("V", ""))
                return response
            except Exception:
                return None
        else:
            input = self._input_channel_parser(input)
            response = zmq_exec(self.connection, f"{input}:THRE {threshold}")
            if "VALUE SET TO" in response.upper():
                return True
            else:
                return False
            
    def _enabled(self, input: str|int) -> bool:
        if zmq_exec(self.connection, f"{input}:ENAB?") == 'ON':
            return True
        
        return False
                

    def enable_input(self, input: str|int) -> bool:
        input = self._input_channel_parser(input)
        if self._enabled(input):
            return True
        else:
            response = zmq_exec(self.connection, f"{input}:ENAB")
            if response.strip().upper() == 'VALUE SET TO ON':
                return True
            else:
                if self.verbose:
                    print(response)
                return False
        
    def disable_input(self, input: str|int) -> bool:
        input = self._input_channel_parser(input)
        if not self._enabled(input):
            return True
        else:
            response = zmq_exec(self.connection, f"{input}:ENAB OFF")
        if response.strip().upper() == 'VALUE SET TO OFF':
            return True
        else:
            if self.verbose:
                print(response)
            return False
    
