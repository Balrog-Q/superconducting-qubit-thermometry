import numpy as np
import pyvisa

class KeysightDMM34465A:
    def __init__(self, address):
        self.address = address
        self.id = None
        self.instrument = None
        self.nplc = 10.0
        self.trigger_sourse = None
        self.sample_count = None
        self.range = None
        self.level = None
#Base    
    def open_inst(self):
        self.instrument = pyvisa.ResourceManager().open_resource(self.address)
        self.instrument.read_termination = '\n'
        self.instrument.write_termination = '\n'
        
    def close_inst(self): 
        self.instrument = pyvisa.ResourceManager().close()
#ID
    def get_id(self):
        self.open_inst()
        self.id = self.instrument.query(f'*IDN?')
        print(f"DMM: {self.id}")  
        self.close_inst()    
#NPLC    
    def get_nplc(self):
        self.open_inst()
        self.nplc = self.instrument.query(f'voltage:dc:nplcycles?') 
        self.close_inst()
    
    def set_nplc(self, nplc):
        self.open_inst()
        self.instrument.write(f'voltage:dc:nplcycles {nplc}') 
        self.close_inst()
#Range    
    def get_range(self):
        self.open_inst()
        self.range = self.instrument.query(f'VOLT:RANG?') 
        self.close_inst()
    
    def set_range(self, value):
        self.open_inst()
        self.instrument.write(f'VOLT:RANG {value}') 
        self.close_inst()
#Scan    
    def scan(self):
        self.open_inst()
        self.level = self.instrument.query(f'READ?') 
        self.close_inst()
        return self.level
#Trigger
    def conf_trig(self):
        self.open_inst()
        self.instrument.write(f'TRIG:SOUR BUS') 
        self.close_inst()

    def get_trig(self):
        self.open_inst()
        self.trigger_sourse = self.instrument.query(f'TRIG:SOUR?') 
        self.close_inst()
    
    def set_trig(self, value):
        self.open_inst()
        self.instrument.write(f'TRIG:SOUR {value}') 
        self.close_inst()
        
    def init_trig(self):
        self.open_inst()
        self.instrument.write(f'INIT') 
        self.close_inst()
        
    def bus_trig(self):
        self.open_inst()
        self.instrument.write(f'*TRG') 
        self.close_inst()   
#Sample count
    def get_sample_count(self):
        self.open_inst()
        self.sample_count = self.instrument.query(f'SAMP:COUN?') 
        self.close_inst()

#Local and reset
    def local(self):
        self.open_inst()
        self.instrument.write(f'SYST:LOC') 
        self.close_inst()

    def reset(self):
        self.open_inst()
        self.instrument.write(f'*CLS')
        self.instrument.write(f'*RST')
        self.close_inst()
        self.local()
