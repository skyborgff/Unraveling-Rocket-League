import numpy as np
import os
from os.path import sep, dirname, realpath
import pyqtgraph as pg
from pyqtgraph import opengl as gl
from pyqtgraph.Qt import QtCore, QtGui
import sys

path = os.path.dirname(os.path.abspath(__file__))
path = path.split("throttle")[0]
sys.path.insert(0, path)
import analisis_functions as af  # They are good AF


class Visualizer(object):
    def __init__(self):
        visual_multiplier = [10, 200 / 120, 5 / 1400]
        # Get the directory for the data
        data_dir = dirname(realpath(__file__)) + r"\data\regular"
        data_file_name = [
            "#full_data_path.npy",
            "#acc_data_path.npy",
            "break_data_path.npy",
            "#coast_data_path.npy",
        ]
        # Initiate the data array
        full_data = np.empty((3,))
        # iterating through all files and adding them to a huge array
        for filename in os.listdir(data_dir):
            if filename not in data_file_name:
                continue
            filepath = data_dir + sep + filename
            # Loading data
            data = np.load(filepath)
            full_data = np.vstack((full_data, data))

        pos_data_mask = full_data[:, 0] >= 0
        self.pos_data = full_data[pos_data_mask]
        neg_data_mask = full_data[:, 0] < 0
        self.neg_data = full_data[neg_data_mask]

        # PyQtGraph stuff
        self.app = QtGui.QApplication(sys.argv)
        self.w = gl.GLViewWidget()
        self.w.opts["distance"] = 40
        self.w.setWindowTitle("RL Throttle Visualized")
        self.w.setGeometry(0, 30, 1920, 1080)
        self.w.show()

        # Adding a grid
        gz = gl.GLGridItem(QtGui.QVector3D(20, 10, 1))
        gz.translate(0, 5, 0)
        self.w.addItem(gz)

        gz = gl.GLGridItem(QtGui.QVector3D(10, 20, 1))
        gz.rotate(90, 0, 1, 0)
        gz.rotate(90, 0, 0, 1)
        gz.translate(0, 0, 0)
        self.w.addItem(gz)

        # Create the scatter plot
        blue_color = [0.1, 0.5, 1, 0.9]
        self.pos_data[:, 0] = self.pos_data[:, 0] * visual_multiplier[0]
        self.pos_data[:, 1] = self.pos_data[:, 1] * visual_multiplier[1]
        self.pos_data[:, 2] = self.pos_data[:, 2] * visual_multiplier[2]
        scatter = gl.GLScatterPlotItem(pos=self.pos_data, size=1, color=blue_color)
        self.w.addItem(scatter)

        red_color = [1, 0.3, 0.05, 0.9]
        self.neg_data[:, 0] = self.neg_data[:, 0] * visual_multiplier[0]
        self.neg_data[:, 1] = self.neg_data[:, 1] * visual_multiplier[1]
        self.neg_data[:, 2] = self.neg_data[:, 2] * visual_multiplier[2]
        scatter = gl.GLScatterPlotItem(pos=self.neg_data, size=1, color=red_color)
        self.w.addItem(scatter)

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
            QtGui.QApplication.instance().exec_()

    def update(self):
        pass

    def animation(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(20)
        self.start()


if __name__ == "__main__":
    v = Visualizer()
    v.animation()
