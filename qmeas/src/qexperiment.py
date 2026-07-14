from abc import ABC, abstractmethod
from qmeas.qsample import QSample
from laboneq.dsl.session import Session

class QExperiment(ABC):
    def __init__(self, session: Session, name: str, sample: QSample, result_keys: list[str], plot: bool = True, analyze: bool = True):
        self.session = session
        self.name = name
        self.sample = sample
        self.defined_exp = None
        self.compiled_exp = None
        self.full_result = None
        self.results = None
        self.result_keys = None
        self.figax = None

    @abstractmethod
    def define_experiment(self):
        pass

    @abstractmethod
    def setup(self):
        pass

    def compile(self):
        if self.defined_exp is not None:
            self.session.compile(self.defined_exp)
        
        else:
            raise Exception("Experiment not yet defined.")
        
    def run_exp(self):
        if self.compiled_exp is not None:
            self.full_result = self.session.run(self.compiled_exp)

        else:
            raise Exception("Experiment not yet compiled.")
        
    def analyze(self):
        pass

    def plot(self):
        pass

    def run_all(self):
        self.define_experiment()
        self.setup()
        self.compile()
        self.run_exp()
        self.analyze()
        self.plot()