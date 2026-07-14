import os

class QSample:
    def __init__(self, directory: str, sample: str, structure: str):
        self.dir = directory
        self.sample = sample
        self.structure = structure

        self.work_dir = os.path.join(directory, sample, structure)

        if not os.path.isdir(self.work_dir):
            os.makedirs(self.work_dir)
            print(f'Created working directory for sample {sample} - {structure}: {self.work_dir}')