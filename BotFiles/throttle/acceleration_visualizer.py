import numpy as np
import os
from os.path import sep, dirname, realpath
import pyqtgraph as pg
from pyqtgraph import opengl as gl
from pyqtgraph.Qt import QtCore, QtGui
import sys
import scipy.optimize as optimize
import matplotlib.pyplot as plt

path = os.path.dirname(os.path.abspath(__file__))
path = path.split("throttle")[0]
sys.path.insert(0, path)
import analisis_functions as af  # They are good AF


class Visualizer(object):
    def __init__(self):

        find_braking_values = False
        find_coast_values = False
        find_acceleration_values = False
        # Get the directory for the data
        data_dir = dirname(realpath(__file__)) + r"\data\regular"
        data_file_name = [
            "full_data_path.npy",
            "#acc_data_path.npy",
            "#break_data_path.npy",
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

        if find_braking_values:
            acceleration = abs(self.full_data_grad[:, 2])
            acceleration = np.sort(acceleration)
            acceleration = np.around(acceleration, decimals=3)
            normal_mask = (acceleration > 3498) & (acceleration < 3502)
            boost_mask = (
                (self.full_data_grad[:, 0] > 1)
                & (acceleration > 4491)
                & (acceleration < 4492)
            )
            normal_acceleration = acceleration[normal_mask]
            boost_acceleration = acceleration[boost_mask]
            print(f"Normal braking force = {np.median(normal_acceleration)}")
            print(f"Boost braking force = {np.median(boost_acceleration)}")
            print(
                f"Boost braking dif = {np.median(boost_acceleration)-np.median(normal_acceleration)}"
            )

        if find_coast_values:
            acceleration = abs(self.full_data_grad[:, 2])
            acceleration = np.sort(acceleration)
            acceleration = np.around(acceleration, decimals=4)
            normal_mask = (acceleration > 527.661) & (acceleration < 527.663)
            normal_acceleration = acceleration[normal_mask]
            hist = np.histogram(normal_acceleration, bins=100)
            print(f"Coasting force = {np.median(normal_acceleration)}")

        if find_acceleration_values:
            acceleration = abs(self.full_data_grad[:, 2])
            acceleration = np.around(acceleration, decimals=5)
            normal_mask = (
                (acceleration > 0)
                & (acceleration < 3500)
                & (self.full_data_grad[:, 0] <= 1)
            )
            normal_acceleration = acceleration[normal_mask]
            normal_acceleration = np.sort(normal_acceleration)

            stable_acceleration = acceleration / self.full_data_grad[:, 0]
            stable_func_grad = np.gradient(
                stable_acceleration, self.full_data_grad[:, 1]
            )
            stable_func_grad = np.nan_to_num(
                stable_func_grad, nan=0, posinf=0, neginf=0
            )

            close_to_transition_mask = (
                (abs(self.full_data_grad[:, 1]) > 1390)
                & (abs(self.full_data_grad[:, 1]) < 1500)
                & (abs(stable_func_grad) > 50)
            )
            speed_transition = self.full_data_grad[close_to_transition_mask, 1]

            plt.scatter(
                abs(self.full_data_grad[:, 1]), abs(stable_acceleration), marker="."
            )
            plt.title("Scatter plot pythonspot.com")
            plt.xlabel("x")
            plt.ylabel("y")
            # plt.show()

            print(
                f"Max acceleration force = {(np.max(acceleration)-990.413) / 0.99609375}"
            )
            print(f"Normal acceleration force = {np.median(normal_acceleration)}")
            print(f"Acceleration transition (speed) = {np.min(abs(speed_transition))}")
            print(f"Max normal speed = {np.max(abs(speed_transition))}")
            print(f"Max boost speed = {np.max(abs(self.full_data_grad[:, 1]))}")

        def array_to_onebyone(array1, array2, function):
            if array1.size != array2.size:
                raise ValueError(
                    "all the input arrays must have same number of dimensions"
                )
            total_result = np.empty((0,))
            for index in range(array1.size):
                result = function(array1[index], array2[index])
                total_result = np.hstack((total_result, result))
            return total_result

        def tick_acceleration(
            throttle,
            speed,
            BRAKING_ACCELERATION=3501.255,
            BOOST_IMPULSE=990.413,
            COASTING_FORCE=527.6618,
            MAX_NORMAL_ACCELERATION=1610.733,
            ACCELERATION_TRANSITION_POINT=[1400.55, 160],
            MAX_NORMAL_SPEED=1409.99,
            MAX_BOOST_SPEED=2300.001,
        ):

            coast_limit = 0.0117647058823529
            sign_throttle = np.sign(throttle)
            sign_speed = np.sign(speed)
            fase = sign_speed * sign_throttle
            if abs(throttle) < coast_limit:
                mode = "coast"
            elif fase > 0:
                mode = "accelerating"
            else:
                mode = "braking"

            if abs(throttle) > 1:
                boost = True
            else:
                boost = False
            if mode == "braking":
                current_acceleration = BRAKING_ACCELERATION * sign_throttle
            if mode == "coast":
                current_acceleration = COASTING_FORCE * -1 * sign_speed
            if mode == "accelerating":
                if abs(speed) < ACCELERATION_TRANSITION_POINT[0]:
                    gradient = (
                        ACCELERATION_TRANSITION_POINT[1] - MAX_NORMAL_ACCELERATION
                    ) / (ACCELERATION_TRANSITION_POINT[0])

                    current_acceleration = (
                        (gradient * speed + MAX_NORMAL_ACCELERATION * sign_speed)
                        * throttle
                        * sign_speed
                    )

                elif abs(speed) < MAX_NORMAL_SPEED:
                    gradient = (-ACCELERATION_TRANSITION_POINT[1]) / (
                        MAX_NORMAL_SPEED - ACCELERATION_TRANSITION_POINT[0]
                    )

                    current_acceleration = (
                        (gradient * speed + 23898.1355932202 * sign_speed)
                        * throttle
                        * sign_speed
                    )
                else:
                    gradient = 0
                    current_acceleration = 0

            if boost:
                if speed >= MAX_BOOST_SPEED:
                    current_acceleration = 0
                else:
                    current_acceleration = tick_acceleration(
                        1, speed
                    ) + BOOST_IMPULSE * np.where(
                        np.sign(current_acceleration) == 0,
                        1,
                        np.sign(current_acceleration),
                    )
            return current_acceleration

        self.full_data_grad_func = np.hstack(
            (
                np.transpose(self.full_data_grad[:, 0][np.newaxis]),
                np.transpose(self.full_data_grad[:, 1][np.newaxis]),
                np.transpose(
                    array_to_onebyone(
                        self.full_data_grad[:, 0],
                        self.full_data_grad[:, 1],
                        tick_acceleration,
                    )[np.newaxis]
                ),
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
        # self.w.addItem(gz)

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
        self.w.addItem(scatter)

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
