import numpy as np
import os
from os.path import sep, dirname, realpath
import pyqtgraph as pg
from pyqtgraph import opengl as gl
from pyqtgraph.Qt import QtCore, QtGui
import sys


class Visualizer(object):
    def __init__(self):

        # Get the directory for the data
        data_dir = dirname(realpath(__file__)) + r'\data'
        # Initiate the data array
        full_data = np.ndarray
        # we cant vstack an empty array so this is needed
        first = True
        #iterating through all files and adding them to a huge array
        for filename in os.listdir(data_dir):
            # Getting the float value from the filename
            throttle = float(filename.split('.')[0].replace('_', '.'))
            # Getting the whole file path
            filepath = data_dir + sep + filename
            # Loading data
            data = np.load(filepath)
            # Getting data size
            size = int(data.size / 2)
            # Creating a table with throttle value
            throttle = np.full((size, 1), throttle)
            # Mashing the throttle table with the rest, so it becomes a 3D point.
            data = np.hstack((throttle, data))

            # Scaling for prettier visualization
            data[:, 0] = data[:, 0]/1*10
            data[:, 1] = data[:, 1]/120*200
            data[:, 2] = data[:, 2]/1400*5

            # We cant stack with an empty array
            if not first:
                full_data = np.vstack((full_data, data))
            else:
                full_data = data
                first = False


        print(f'The total ammount of points is: {int(full_data.size/3)}')

        self.data = full_data

        # PyQtGraph stuff
        self.app = QtGui.QApplication(sys.argv)
        self.w = gl.GLViewWidget()
        self.w.opts['distance'] = 40
        self.w.setWindowTitle('RL Throttle Visualized')
        self.w.setGeometry(0, 110, 1920, 1080)
        self.w.show()

        # Adding a grid
        gz = gl.GLGridItem(QtGui.QVector3D(20,10,1))
        gz.translate(0, 5, 0)
        self.w.addItem(gz)

        # Create the scatter plot
        scatter = gl.GLScatterPlotItem(pos=full_data, size=1)
        self.w.addItem(scatter)

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    def set_plotdata(self, name, points, color, width):
        self.traces[name].setData(pos=points, color=color, width=width)

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
