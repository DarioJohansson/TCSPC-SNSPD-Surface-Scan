from utils.common import zmq_exec


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
    def __init__(self, count: int = None, integration_time_ms: int = None, input: str = None):
        
        if count != None and type(count) == int:
            self.count = count
        else:
            raise ValueError("Count Class: count needs to be of integer type and needs to be specified.")
        
        if integration_time_ms:
            self.integration_time_ms = integration_time_ms
        
        if input:
            self.input = input
        
        self.time_created = time.time()

        iobuiobb
        '''
        ADD LOCAL VARIABLE STORAGE OF DEVICE SETTINGS IN TCCOUNTER CLASS SO THAT IT CAN BE EXPORTED WITH NO COMM OVERHEAD FOR EACH MEASUREMENT STEP
        '''


class TCCounter:
    def __init__(self, tc, int_time_ms: int = 1000, input: int|str = 'start', mode: str = "cycle", verbose: bool = False):
        self.tc = tc
        self.verbose = verbose

        if input.upper() == 'START':
            self.input='STAR'
        elif type(input) == int and input in range(1,4):
            self.input=f'INPU{input}'
        else:
            raise ValueError(f'Input needs to be "start" or an integer number from 1 to 4')
        # add sanity checks for god's sake.

        int_time_response = zmq_exec(self.tc, f"{self.input}:COUN:INTE {int_time_ms}")
        mode_response = zmq_exec(self.tc, f"{self.input}:COUN:MODE {mode.upper()}")

        if self.verbose:
            print(f"Integration Time Response: {int_time_response}\nCounter Mode Response: {mode_response}")

        self.integration_time_ms = zmq_exec(self.tc, f"{self.input}:COUN:INTE?")

    def enabled(self) -> bool:
        if zmq_exec(self.tc, f"{self.input}:ENAB?") == 'ON':
            return True
        else:
            return False
    
    def reset(self):
        response = zmq_exec(self.tc, f"{self.input}:COUN:RESE")
        if self.verbose:
            print(response)
    
    def enable_input(self) -> bool:
        if self.enabled():
            return True
        else:
            response = zmq_exec(self.tc, f"{self.input}:ENAB")
            if response == 'Value set to ON':
                return True
            else:
                if self.verbose:
                    print(response)
                return False
        
    def disable_input(self) -> bool:
        if not self.enabled():
            return True
        else:
            response = zmq_exec(self.tc, f"{self.input}:ENAB OFF")
        if response == 'Value set to OFF':
            return True
        else:
            if self.verbose:
                print(response)
            return False
        
    def mode(self, mode: str|None = None) -> str|bool:
        if not mode:
            return zmq_exec(self.tc, f'{self.input}:COUN:MODE?').lower()
        else:
            mode = mode.upper()
            if mode == 'CYCLE':
                mode = 'CYCLe'
            elif mode == 'ACCUM':
                mode = 'ACCUm'
            else:
                raise ValueError(f"Mode {mode} not supported.")
            
            response = zmq_exec(self.tc, f'{self.input}:COUN:MODE {mode}')
            
            if response == f'Value set to {mode}':
                return True
            else:
                if self.verbose:
                    print(response)
                return False
    
    def count(self) -> int|None:
        try:
            value = int(zmq_exec(self.tc, f'{self.input}:COUN?'))
            data = CountData(value, self.int)
            return value
        except ValueError as e:
            print(f"Counter is throwing errors: {e}")
    
    

        