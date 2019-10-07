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


class Visualizer(object):
    def __init__(self):

        # Get the directory for the data
        data_dir = dirname(realpath(__file__)) + r"\data\regular"
        data_file_name = [
            "#full_data_path.npy",
            "acc_data_path.npy",
            "#break_data_path.npy",
            "#boost_data_path.npy",
            "#coast_data_path.npy",
        ]
        # Initiate the data array
        full_data = np.ndarray
        # iterating through all files and adding them to a huge array
        for filename in os.listdir(data_dir):
            if filename not in data_file_name:
                continue
            filepath = data_dir + sep + filename
            # Loading data
            data = np.load(filepath)

            try:
                full_data = np.vstack((full_data, data))
            except:
                full_data = data

        self.full_data = full_data

        # get the acceleration
        self.full_data_grad = np.gradient(self.full_data[:, 2], self.full_data[:, 1])
        self.full_data_grad = np.nan_to_num(
            self.full_data_grad, nan=0, posinf=0, neginf=0
        )
        self.full_data_grad = np.hstack(
            (
                np.transpose(self.full_data[:, 0][np.newaxis]),
                np.transpose(self.full_data[:, 2][np.newaxis]),
                np.transpose(self.full_data_grad[np.newaxis]),
            )
        )

        # Function that defines the acceleration depending on current speed, and current throttle
        def acc_function(data, a=16.8361251, b=1.03569487, c=10, d=1400):
            # Thanks to @Hytak#5125 for giving me a TON of help getting this function
            # data[:, 0] = throttle
            # data[:, 1] = current speed
            pos_throttle = af.float_range()
            sign = np.sign(data[:, 0])
            sign = np.where(sign == 0, 1, sign)
            x = d + c - abs(data[:, 1])
            mask = x < c
            small = x * a * abs(data[:, 0]) - 1 / 255  # tiny surface
            big = ((x - c) * b + c * a) * (abs(data[:, 0]))  # big surface
            # big = (20-1.6*abs(data[:, 1])) * (abs(data[:, 0]-1 / 255*throttle_multiplier)/throttle_multiplier) # big surface
            break_func = 3510 * sign
            break_mask = data[:, 0] * data[:, 1] <= 0
            coast_func = 525 * sign
            coast_throttle = [
                pos_throttle[int(256 / 2 - 1)],
                pos_throttle[int(256 / 2)],
                pos_throttle[int(256 / 2 + 1)],
            ]
            coast_mask = (
                (data[:, 0] == coast_throttle[0])
                | (data[:, 0] == coast_throttle[1])
                | (data[:, 0] == coast_throttle[2])
            )
            boost_mask = abs(data[:, 0]) > 1
            boost_linear_func = 991.667
            boost_linear_mask = abs(data[:, 1]) > d + c + b

            smooth_function = np.where(mask, small, big) * sign
            smooth_function = np.where(break_mask, break_func, smooth_function)
            smooth_function = np.where(coast_mask, coast_func, smooth_function)
            boost_function = np.where(
                boost_linear_mask, boost_linear_func, smooth_function + 991.667
            )
            smooth_function = np.where(boost_mask, boost_function, smooth_function)
            delta_accel = 1.233333333
            stepped_func = (
                np.round(np.array(smooth_function, dtype=float) / delta_accel)
                * delta_accel
            )
            return stepped_func

        def chip_function(data):
            # data[:, 0] = throttle
            # data[:, 1] = current speed

            mask = abs(data[:, 1]) < 1400

            small = ((data[:, 0]) - 1 / 255) * (
                1600 - ((1600 - 160) * data[:, 1]) / 1400
            )

            big = data[:, 0] * (160 - (160 * (data[:, 1] - 1400) / 10))

            smooth_function = np.where(mask, small, big)

            delta_accel = 1.233
            stepped_func = (
                np.round(np.array(smooth_function, dtype=float) / delta_accel)
                * delta_accel
            )
            return stepped_func

        def RLfunction(data):
            return

        # guess = (2, 1, 0.01, 1)
        # par, pcov = optimize.curve_fit(acc_function, self.full_data_grad[:, :2], self.full_data_grad[:, 2], guess)

        self.full_data_grad_func = np.hstack(
            (
                np.transpose(self.full_data_grad[:, 0][np.newaxis]),
                np.transpose(self.full_data_grad[:, 1][np.newaxis]),
                np.transpose(acc_function(self.full_data_grad[:, :2])[np.newaxis]),
            )
        )

        # PyQtGraph stuff
        self.app = QtGui.QApplication(sys.argv)
        self.w = gl.GLViewWidget()
        self.w.opts["distance"] = 1000
        self.w.setWindowTitle("RL Throttle Visualized")
        self.w.setGeometry(0, 30, 1920, 1080)
        self.w.show()

        # Adding a grid
        gz = gl.GLGridItem(QtGui.QVector3D(1000, 1500, 1))
        gz.translate(500, 1500 / 2, 0)
        self.w.addItem(gz)
        # pos_throttle2 = af.float_range()
        # for index in range(5):
        #     index = 127 + index
        #     th = pos_throttle2[index]
        #     gz = gl.GLGridItem(QtGui.QVector3D(1200, 40, 1))
        #     gz.rotate(90, 0, 1, 0)
        #     gz.translate(th, 0, 0)
        #     self.w.addItem(gz)

        # Create the scatter plot
        blue_color = [0.1, 0.5, 1, 0.65]
        red_color = [1, 0.3, 0.05, 0.65]
        white_color = [1.0, 1.0, 1.0, 0.6]

        self.full_data_grad[:, 0] = self.full_data_grad[:, 0] * 1000
        scatter = gl.GLScatterPlotItem(
            pos=self.full_data_grad, size=1, color=blue_color
        )
        self.w.addItem(scatter)

        self.full_data_grad_func[:, 0] = self.full_data_grad_func[:, 0] * 1000

        scatter = gl.GLScatterPlotItem(
            pos=self.full_data_grad_func, size=1, color=red_color
        )
        # self.w.addItem(scatter)

        # https://stackoverflow.com/questions/56890547/how-to-add-axis-features-labels-ticks-values-to-a-3d-plot-with-glviewwidget
        axis = af.Custom3DAxis(self.w, color=[1.0, 1.0, 1.0, 1.0])
        axis.setSize(x=1100, y=1600, z=3800)
        # Add axes labels
        axis.add_labels()
        # Add axes tick values
        axis.add_tick_values(
            xticks=list(range(0, 11, 1)) + ["Throttle"],
            yticks=list(range(0, 1600, 100)) + ["Current Speed"],
            zticks=list(range(0, 3800, 100)) + ["Acceleration"],
        )
        self.w.addItem(axis)

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
