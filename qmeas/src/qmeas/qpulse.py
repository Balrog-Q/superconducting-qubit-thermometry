from laboneq.dsl.experiment.pulse import PulseFunctional

import matplotlib.pyplot as plt

class QPulse(PulseFunctional, dict):
    def __init__(self, uid: str, function: callable, length: float, amplitude: float = 1, can_compress: bool = False, pulse_parameters: dict = None):
        if pulse_parameters is None:
            pf = function(uid=uid, length=length, amplitude=amplitude, can_compress=can_compress)
        else:
            pf = function(uid=uid, length=length, amplitude=amplitude, can_compress=can_compress, **pulse_parameters)
        self.uid = pf.uid
        self.function = pf.function
        self.length = pf.length
        self.amplitude = pf.amplitude
        self.can_compress = pf.can_compress
        self.pulse_parameters = pf.pulse_parameters
        dict.__init__(self, uid=self.uid, function=self.function, length=self.length, amplitude=self.amplitude, 
                      can_compress=self.can_compress, pulse_parameters=self.pulse_parameters)
        self.pulse = pf

    def show(self, figax: tuple = None):
        if figax is None:
            fig, ax = plt.subplots(figsize=(8, 6))
        else:
            fig, ax = figax
        
        x, y = self.generate_sampled_pulse()
        ax.plot(x.real, y.real)
        ax.set_xlabel('Time')
        ax.set_ylabel('Relative Amplitude')

        return fig, ax


def show_pulse(pf: PulseFunctional, figax: tuple = None, **kwargs):
    if figax is None:
            fig, ax = plt.subplots(figsize=(8, 6))
    else:
            fig, ax = figax
        
    x, y = pf.generate_sampled_pulse()
    ax.plot(x.real, y.real, **kwargs)
    ax.set_xlabel('Time')
    ax.set_ylabel('Relative Amplitude')

    return fig, ax
