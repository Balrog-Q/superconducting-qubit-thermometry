from scipy.io import savemat
import numpy as np
import matplotlib.pyplot as plt
import os.path
import time

def get_path(sample_parameters):
    day = time.strftime('%Y-%m-%d')
    current_folder_name = day+' Jupiter'
    path = os.path.join(sample_parameters['folder_name'], sample_parameters['sample_name'], sample_parameters['structure_name'], current_folder_name)
    
    if not os.path.isdir(path):
        os.makedirs(path)
        
    return path

def get_path_to_file(name, form, sample_parameters):
    path = get_path(sample_parameters)
    time_now = time.strftime('%H_%M_%S')
    file_name = name + time_now + form
    return os.path.join(path, file_name)

def save_data(data_name, data, sample_parameters, qubit_parameters, lo_settings):
    data_to_save = data.update(sample_parameters)
    data_to_save = data.update(qubit_parameters)
    data_to_save = data.update(lo_settings)
    time = time.strftime('%H_%M_%S')
    file_path = get_path_to_file(data_name, '.mat', sample_parameters)
    savemat(file_path, Data_temp_sweep)
    print('Saved to ', file_path)
    return file_path
