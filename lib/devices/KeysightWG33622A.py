import numpy as np
import pyvisa

class KeysightWG33622A:
    def __init__(self, address):
        self.address = address
        self.instrument = None
        self.protect_func = None
        self.protect_value = None
        self.func = None
        self.output = None
        self.freq = None
        self.range = None
        self.level = None
    
    def open_inst(self):
        self.instrument = pyvisa.ResourceManager().open_resource(self.address)
        self.instrument.read_termination = '\n'
        self.instrument.write_termination = '\n'
        
    def close_inst(self): 
        self.instrument = pyvisa.ResourceManager().close()

    def set_func(self, func):
        self.open_inst()
        func = func.upper()
        if func == 'VOLT':
            self.instrument.write(':SOUR:FUNC VOLT')
            self.func = func
        elif func == 'CURR':
            self.instrument.write(':SOUR:FUNC CURR')
            self.func = func
        else:
            raise ValueError(f"Variable state {self.func} is not defined!")
        self.close_inst()

    def get_func(self):
        self.open_inst()
        self.func = self.instrument.query(f':SOUR:FUNC?')
        print(f"instrument function: {self.func}")  
        self.close_inst()

    def set_output(self, state):
        self.open_inst()
        self.output = state
        if self.output:
            self.instrument.write('OUTP ON') 
        elif not self.output:
            self.instrument.write('OUTP OFF') 
        else:
            self.close_inst()
            raise ValueError(f"Variable state {self.output} is not defined!")
        self.close_inst()

    
    def get_output(self):
        self.open_inst()
        self.output = self.instrument.query('OUTP?')
        print(f"instrument output state: {self.output}")
        self.close_inst()
    
    def set_protect(self, func, rng):
        self.open_inst()
        func = func.upper()
        if func == 'VOLT':
            if (rng > 0) and (rng <= 30): 
                self.instrument.write(f':SOUR:PROT:VOLT {rng}')
                self.protect_func = func
                self.protect_value = rng
            else:
                self.close_inst()
                raise ValueError(f"Variable state {self.protect_rng} is out of range!")
        elif func == 'CURR':
            if (abs(rng) >= 1e-3) and (abs(rng) <= 200e-3): 
                self.instrument.write(f':SOUR:PROT:CURR {rng}')
                self.protect_func = func
                self.protect_value = rng
            else:
                self.close_inst()
                raise ValueError(f"Variable state {self.protect_rng} is out of range!")
        else:
            self.close_inst()
            raise ValueError(f"Variable state {self.func} is not defined!")
        self.close_inst()

    def get_protect(self, func):
        self.open_inst()
        func = func.upper()
        if func == 'VOLT':
            self.protect_value = float(self.instrument.query(':SOUR:PROT:VOLT?'))
            print(f"instrument protection state: {self.protect_value}")
        elif func == 'CURR':    
            self.protect_value = float(self.instrument.query(':SOUR:PROT:CURR?'))
            print(f"instrument protection state: {self.protect_value}")
        else:
            self.close_inst()
            raise ValueError(f"Variable state {func} is not defined!")
        self.close_inst()
    
    def set_level(self, level):
        self.open_inst()
        self.level = level
        self.instrument.write(f':SOUR1:VOLT {level}')
        self.close_inst()
    
    def get_level(self, only_number = False):
        self.open_inst()
        if only_number:
            self.level = float(self.instrument.query('SOUR1:VOLT?'))
            self.close_inst()
            return self.level
        elif not only_number:
            self.level = float(self.instrument.query('SOUR1:VOLT?'))
            print(f"instrument level: {self.level}")
            self.close_inst()
            return self.level
        
    def set_freq(self, freq):
        self.open_inst()
        self.freq = freq
        self.instrument.write(f':SOUR1:FREQ {freq}')
        self.close_inst()
    
    def get_freq(self, only_number = False):
        self.open_inst()
        if only_number:
            self.freq = float(self.instrument.query('SOUR1:FREQ?'))
            self.close_inst()
            return self.freq
        elif not only_number:
            self.freq = float(self.instrument.query('SOUR1:FREQ?'))
            print(f"instrument freq: {self.freq}")
            self.close_inst()
            return self.freq
    
    def set_range(self, rng):
        self.open_inst()
        self.range = rng
        self.instrument.write(f':SOUR:RANG {rng}')
        self.close_inst()

    
    def get_range(self):
        self.open_inst()
        self.range = float(self.instrument.query(':SOUR:RANG?'))
        print(f"instrument range: {self.range}")
        self.close_inst()

    def ramp(self, value, N_steps = 1e3):
        level_start = self.get_level(only_number = True)
        level_stop = value
        step = (level_stop - level_start) / N_steps
        if level_start != level_stop:
            for level in np.arange(level_start, level_stop + step / 2, step):
                self.set_level(level)