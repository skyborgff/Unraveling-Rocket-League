import numpy as np
import os
from os.path import sep, dirname, realpath
import pyqtgraph as pg
from pyqtgraph import opengl as gl
from pyqtgraph.Qt import QtCore, QtGui
import sys
import scipy.optimize as optimize


class Visualizer(object):
    def __init__(self):

        # Get the directory for the data
        data_dir = dirname(realpath(__file__)) + r'\data'
        # Initiate the data array
        neg_full_data = np.ndarray
        pos_full_data = np.ndarray
        # we cant vstack an empty array so this is needed
        neg_first = True
        pos_first = True
        #iterating through all files and adding them to a huge array
        for filename in os.listdir(data_dir):
            # Getting the float value from the filename
            throttle = float(filename.split('.')[0].replace('_', '.'))
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

            # Scaling for prettier visualization
            data[:, 0] = data[:, 0]#*1000#/1*10
            data[:, 1] = data[:, 1]#/120*200
            data[:, 2] = data[:, 2]#/1400*5

            # We cant stack with an empty array
            if throttle <= 0:
                if not neg_first:
                    neg_full_data = np.vstack((neg_full_data, data))
                else:
                    neg_full_data = data
                    neg_first = False
            if throttle >= 0:
                if not pos_first:
                    pos_full_data = np.vstack((pos_full_data, data))
                else:
                    pos_full_data = data
                    pos_first = False


        print(f'The total ammount of points is: {int((neg_full_data.size + pos_full_data.size) /3)}')

        self.neg_data = neg_full_data
        self.pos_data = pos_full_data

        #get the acceleration
        self.neg_data_grad = np.gradient(self.neg_data[:, 2], self.neg_data[:, 1])
        self.neg_data_grad = np.nan_to_num(self.neg_data_grad, nan=0, posinf=0, neginf=0)
        self.neg_data_grad = np.hstack((np.transpose(self.neg_data[:, 0][np.newaxis]),
                                        np.transpose(self.neg_data[:, 2][np.newaxis]),
                                        np.transpose(self.neg_data_grad[np.newaxis])))



        self.pos_data_grad = np.gradient(self.pos_data[:, 2], self.pos_data[:, 1])
        self.pos_data_grad = np.nan_to_num(self.pos_data_grad, nan=0, posinf=0, neginf=0)
        self.pos_data_grad = np.hstack((np.transpose(self.pos_data[:, 0][np.newaxis]),
                                        np.transpose(self.pos_data[:, 2][np.newaxis]),
                                        np.transpose(self.pos_data_grad[np.newaxis])))

        self.full_data_grad = np.vstack((self.neg_data_grad, self.pos_data_grad))

        # Function that defines the acceleration depending on current speed, and current throttle
        def acc_function(data, a=16.8361251, b=1.03569487, c=10, d=1400):
            # Thanks to @Hytak#5125 for giving me a TON of help getting this function
            # data[:, 0] = throttle
            # data[:, 1] = current speed
            sign = np.sign(data[:, 0])
            x = d + c - abs(data[:, 1])
            mask = x < c
            small = x * a * abs(data[:, 0])  # tiny surface
            big = ((x - c) * b + c * a) * abs(data[:, 0])  # big surface
            smooth_function = np.where(mask, small, big)*sign
            delta_accel = 1.233333333
            stepped_func = np.round(np.array(smooth_function, dtype=float) / delta_accel) * delta_accel
            return stepped_func

        # guess = (2, 1, 0.01, 1)
        # par, pcov = optimize.curve_fit(acc_function, self.full_data_grad[:, :2], self.full_data_grad[:, 2], guess)

        self.pos_data_grad_func = np.hstack((np.transpose(self.pos_data_grad[:, 0][np.newaxis]),
                                             np.transpose(self.pos_data_grad[:, 1][np.newaxis]),
                                             np.transpose(acc_function(self.pos_data_grad[:, :2],)[np.newaxis])))
        self.neg_data_grad_func = np.hstack((np.transpose(self.neg_data_grad[:, 0][np.newaxis]),
                                             np.transpose(self.neg_data_grad[:, 1][np.newaxis]),
                                             np.transpose(acc_function(self.neg_data_grad[:, :2],)[np.newaxis])))


        # PyQtGraph stuff
        self.app = QtGui.QApplication(sys.argv)
        self.w = gl.GLViewWidget()
        self.w.opts['distance'] = 40
        self.w.setWindowTitle('RL Throttle Visualized')
        self.w.setGeometry(0, 30, 1920, 1080)
        self.w.show()

        # Adding a grid
        gz = gl.GLGridItem(QtGui.QVector3D(20, 10, 1))
        gz.translate(0, 5, 0)
        self.w.addItem(gz)

        # Create the scatter plot
        blue_color = [0.1, 0.5, 1, 1]
        red_color = [1, 0.3, 0.05, 0.65]
        white_color = [1.0, 1.0, 1.0, 0.6]

        scatter = gl.GLScatterPlotItem(pos=self.pos_data_grad, size=1, color=blue_color)
        self.w.addItem(scatter)
        scatter = gl.GLScatterPlotItem(pos=self.neg_data_grad, size=1, color=blue_color)
        self.w.addItem(scatter)

        scatter = gl.GLScatterPlotItem(pos=self.pos_data_grad_func, size=1, color=red_color)
        self.w.addItem(scatter)
        scatter = gl.GLScatterPlotItem(pos=self.neg_data_grad_func, size=1, color=red_color)
        self.w.addItem(scatter)



    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    def update(self):
        pass

    def animation(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(20)
        self.start()

if __name__ == '__main__':
    v = Visualizer()
    v.animation()
