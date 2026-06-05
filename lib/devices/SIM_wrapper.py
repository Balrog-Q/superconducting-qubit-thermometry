import numpy as np
import pyvisa
import time

class SIM900:
    def __init__(self, address):
        self.address = address
        self.instrument = None
        self.id = None
        self.sims = [0]*8
    
    def open_inst(self):
        self.instrument = pyvisa.ResourceManager().open_resource(self.address)
        
    def write_inst(self, cmd):
        self.instrument.write(cmd)
        
    def query_inst(self, qry):
        return self.instrument.query(qry)
        
    def close_inst(self): 
        self.instrument = pyvisa.ResourceManager().close()
    
    def get_sim(self, port):
        if self.sims[port-1]:
            print(f'Port {port} was alredy connected.')
            return self.sims[port-1]
        else:
            self.sims[port-1] = SIM928(self, port)
            print(f'Port {port} is connected.')
            return self.sims[port-1]
                
class SIM928:
    def __init__(self, frame, port):
        self.frame = frame
        self.port = port
        self.vlimit = 20
        self.ramprate = 0.1
        self.output = None
        self.level = None
    
    def open_sim(self):
        self.frame.open_inst()
        self.frame.write_inst(f'CONN {self.port},"OFF"')
        self.frame.write_inst(f'*RST')
        
    def close_sim(self): 
        self.frame.write_inst('"OFF"')
        self.frame.close_inst()

 #Output settings       
        
    def set_output(self, state):
        self.open_sim()
        self.output = state
        if self.output:
            self.frame.write_inst('OPON') 
        elif not self.output:
            self.frame.write_inst('OPOF') 
        else:
            self.close_sim()
            raise ValueError(f'Variable state {self.output} is not defined!')
        self.close_sim()
    
    def get_output(self):
        self.open_sim()
        self.output = self.frame.query_inst('EXON?')
        print(f"instrument output state: {self.output}")
        self.close_sim()
    
  #Level and ramp settings
    
    def set_level(self, level):
        if np.absolute(level)>self.vlimit:
            print(f'WARNING! SIM voltage overflow: SIM{self.port}, VOLT {level}!')
        else:
            self.level = round(level,3)
            self.open_sim()
            self.frame.write_inst(f'VOLT {self.level}')
            self.close_sim()
    
    def get_level(self, only_number = False):
        self.open_sim()
        if only_number:
            self.level = float(self.frame.query_inst('VOLT?'))
            self.close_sim()
            return self.level
        elif not only_number:
            self.level = float(self.frame.query_inst('VOLT?'))
            print(f"SIM{self.port} level: {self.level}")
            self.close_sim()
            return self.level
        
    def ramp(self, value, N_steps = 1e3):
        level_start = self.get_level(only_number = True)
        level_stop = value
        step = (level_stop - level_start) / N_steps
        if level_start != level_stop:
            for level in np.arange(level_start, level_stop + step / 2, step):
                self.set_level(level)
                
    def rampto(self, val):
        dt = 0.1
        dvmax = self.ramprate*dt
    
        vnow = self.get_level(only_number = True)
    
        while(np.absolute(vnow-val) >= dvmax):
            dv = val - vnow
            dv = np.sign(dv)*min(np.absolute(vnow-val), dvmax)
            vnow = vnow + dv
            self.set_level(vnow)
            time.sleep(dt)
        
        self.set_level(val)