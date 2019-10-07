import numpy as np
import os
from os.path import sep, dirname, realpath
import pyqtgraph as pg
from pyqtgraph import opengl as gl
from pyqtgraph.Qt import QtCore, QtGui
import sys
import scipy.optimize as optimize

path = os.path.dirname(os.path.abspath(__file__))
path = path.split("throttle")[0]
sys.path.insert(0, path)
import analisis_functions as af  # They are good AF


# Get the directory for the data
data_dir = dirname(realpath(__file__)) + r"\data\regular"
# Initiate the data array
full_data = np.ndarray
# iterating through all files and adding them to a huge array
for filename in os.listdir(data_dir):
    # Getting the float value from the filename
    try:
        throttle = float(filename.split(".")[0].replace("_", "."))
    except ValueError:
        continue
    # Getting the whole file path
    filepath = data_dir + sep + filename
    # Loading data
    data = np.load(filepath)
    data = data[2:, :]
    data = np.nan_to_num(data, nan=0, posinf=0, neginf=0)
    # Getting data size
    size = int(data.size / 2)
    # Creating a table with throttle value
    throttle_array = np.full((size, 1), throttle)
    # Mashing the throttle table with the rest, so it becomes a 3D point.
    data = np.hstack((throttle_array, data))

    # We cant stack with an empty array
    try:
        full_data = np.vstack((full_data, data))
    except:
        full_data = data

full_data_path = data_dir + os.path.sep + "full_data_path" + ".npy"
np.save(full_data_path, full_data)

acc_mask = (
    (full_data[:, 0] * full_data[:, 2] > 0)
    & (abs(full_data[:, 0]) > af.coast_limit)
    & (abs(full_data[:, 0]) <= 1)
)
acc_data = full_data[acc_mask]
acc_data_path = data_dir + os.path.sep + "acc_data_path" + ".npy"
np.save(acc_data_path, acc_data)

boost_mask = abs(full_data[:, 0]) > 1
boost_data = full_data[boost_mask]
boost_data_path = data_dir + os.path.sep + "boost_data_path" + ".npy"
np.save(boost_data_path, boost_data)

break_mask = (
    (full_data[:, 0] * full_data[:, 2] < 0)
    & (abs(full_data[:, 0]) > af.coast_limit)
    & (abs(full_data[:, 0]) <= 1)
)
break_data = full_data[break_mask]
break_data_path = data_dir + os.path.sep + "break_data_path" + ".npy"
np.save(break_data_path, break_data)

coast_mask = abs(full_data[:, 0]) < af.coast_limit
coast_data = full_data[coast_mask]
coast_data_path = data_dir + os.path.sep + "coast_data_path" + ".npy"
np.save(coast_data_path, coast_data)
