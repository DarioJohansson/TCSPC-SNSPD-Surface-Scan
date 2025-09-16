from utils.common import zmq_exec
import time
from typing import Literal

# La classe Time Controller Counter:
'''
Questa classe definisce un oggetto che può essere richiamato per rappresentare la funzionalità di conteggio del TC1000 all'interno di un codice in esecuzione.
Può essere usato così:
counter = TCCounter(tc)

"counter" è ora un oggetto inizializzato che ha tutte le funzionalità rilevanti per contare i fotoni in arrivo nei canali di input.
Inizializzando solo con tc;  i parametri di tempo di integrazione, canale di input, modalità e verbose rimangono quelli predefiniti.

tc è un parametro necessario e rappresenta anch’esso un oggetto: in questo caso è un oggetto di connessione generato da una funzione del modulo utils.common.
La funzione connect() accetta un indirizzo IP e una porta, e restituisce un oggetto contesto di connessione, se la connessione ha successo. Questo oggetto viene poi passato al costruttore del counter per poter funzionare.
È il riferimento fisico usato per comunicare tra il codice e il dispositivo TC.

Un esempio di codice pienamente funzionante è il seguente:

##INIZIO

from utils.common import zmq_exec, connect

tc = connect('169.254.207.101', port=5555)      # Crea l'oggetto di connessione tc specificando l'ip e la porta SCPI del TC IDQ
counter = TCCounter(tc)                         # Crea un counter utilizzando la connessione esistente.

if counter.enabled():                           # Controlla se è abilitato.
    count = counter.count()                     # Restituisce il numero di fotoni misurati nella finestra di integrazione, che di default è 1000ms.
    print(count)                                # Stampa il conteggio sulla console.
else:
    counter.enable_input()                 
    count = counter.count()                 
    print(count) 

counter.disable_input()                         # Disabilita la routine di conteggio sul controller.

##FINE

È uno snippet stupido ma serve solo a dimostrare il concetto.
In Python, gli oggetti possono memorizzare variabili uniche, che sono utili per contestualizzare ogni oggetto in base al suo stato.
Questo oggetto verrà usato per fare una mappa d’intensità sul campione, dato che l’operazione è rapidissima e non richiede particolare precisione.
'''

class CountData:
    def __init__(self, count: int = None, integration_time_s: int = None, time_created: float = None):
        
        if count != None and type(count) == int:
            self.count = count
        else:
            raise ValueError("Count Class: count needs to be of integer type and needs to be specified.")
        
        if integration_time_s:
            self.integration_time_s = integration_time_s
        
        if not time_created:
            self.time_created = time.time()
        else:
            self.time_created = time_created

    def frequency(self):
        return self.count/self.integration_time_s
    
    def out(self) -> dict:
        data={"count": self.count, "integration-time-s": self.integration_time_s, "counter-timestamp": self.time_created}
        return data

    @staticmethod 
    def input(data: dict) -> bool:
        try:
            if data.get("count") and data.get("integration-time-s") and data.get("counter-timestamp"):
                obj = CountData(count=data.get("count"), integration_time_s=data.get("integration-time-s"), time_created=data.get("counter-timestamp"))
                return obj
            else:
                return None
        except:
            print("Counter object failed to load.")
            return None
       
class TCCounter:
    def __init__(
                self, 
                tc,
                input: int|str,  
                int_time_ms: int = 1000,
                mode: Literal["cycle", "accum"] = "cycle", 
                verbose: bool = False
                ):
        
        self.tc = tc
        self.verbose = verbose
        self.input = None
        self.integration_time_ms = None

        input = self._input_channel_parser(input)
        if input:
            self.input = input
            self.set_integration_time(int_time_ms)
            self.set_count_mode(mode)


    ################################################ FUNCTIONS ###########################################################
    
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

    def set_integration_time(self, int_time_ms: int = None):
        if int_time_ms == None:
            raise ValueError("TCCounter.set_integration_time(): no integration time specified.")

        int_time_response = zmq_exec(self.tc, f"{self.input}:COUN:INTE {int_time_ms}")
        
        if int_time_response.strip() == f'Value set to {int_time_ms}':
            self.integration_time_ms = int_time_ms
            return True
        
        return False
        
   
    def set_count_mode(self, mode: str):
        if mode.upper() not in ["CYCLE", "ACCUM"]:
            raise ValueError(f"TCCounter.set_count_mode(): {mode} not a valid count mode.") 

        mode_response = zmq_exec(self.tc, f"{self.input}:COUN:MODE {mode.upper()}")
        if mode_response.upper().strip() == f'VALUE SET TO {mode.upper()}':
            return True
            
        return False


    def reset(self, input: str|int):
        input = self._input_channel_parser(input)        
        response = zmq_exec(self.tc, f"{input}:COUN:RESE")
        if response.upper().strip() == 'COUNTER VALUE SET TO 0':
            return True
        
        return False
    
    def count(self) -> int|None:
        try:
            time.sleep(self.integration_time_ms*1e-3)               # Forcing sleep time (converted to seconds) here to avoid having to do it elsewhere. 
            value = int(zmq_exec(self.tc, f'{self.input}:COUN?'))
            data = CountData(value, self.integration_time_ms * 1e-3)
            return data
        except ValueError as e:
            print(f"Counter is throwing errors: {e}")
    
    

        