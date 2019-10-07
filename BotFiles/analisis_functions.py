import numpy as np
from rlbot.utils.structures.game_data_struct import GameTickPacket
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import OpenGL.GL as ogl

coast_limit = 0.0117647058823529


def float_range(pos_only=False, add_boost=False):
    if not pos_only:
        throttle_list = np.interp(
            list(np.arange(255)), [0, 254], [-1 + 1 / 256, 1 - 1 / 256]
        )
        # throttle_list = (np.interp(list(np.arange(256)), [0, 255], [-1, 1]))
    else:
        # fix so it uses a non boundary function
        throttle_list = np.interp(
            list(np.arange(start=256 / 2 - 1, stop=256, step=1)), [255 / 2, 255], [0, 1]
        )
    if add_boost:
        throttle_list_b = np.append(throttle_list, 1 + 1 / 255)
        return throttle_list_b
    return throttle_list


class Stagnation:
    def __init__(self, stagnation_threshold=10):
        self.stagnating_value = None
        self.stagnating_counter = 0
        self.stagnation_list = []
        self.stagnation_threshold = stagnation_threshold

    def stagnated(self, stagnating_value):
        self.stagnating_counter += 1
        self.stagnation_list.append(stagnating_value)
        if len(self.stagnation_list) > self.stagnation_threshold:
            self.stagnation_list.pop(0)
        if len(self.stagnation_list) < self.stagnation_threshold:
            return False
        else:
            stagnated = True
            for index in range(len(self.stagnation_list) - 1):
                if self.stagnation_list[index] != self.stagnation_list[index + 1]:
                    stagnated = False
            return stagnated

    def reset(self):
        self.stagnating_value = None
        self.stagnating_counter = 0
        self.stagnation_list = []


class GatherStatus:
    def __init__(self):
        self.status_list = [
            "Idle",
            "Set-State",
            "Set-State Idle",
            "Recording",
            "Non-Initialized",
        ]
        self.status = 5
        self.delay = [5, 0, 1, 0]
        self.time = [1000000, 10000000, 10000000, 10000000]

    def stat(self, packet: GameTickPacket):
        time = packet.game_info.seconds_elapsed
        if packet.game_info.is_kickoff_pause:
            self.reset(packet)
        else:
            if self.status == 0 and time > (
                self.time[self.status] + self.delay[self.status]
            ):
                self.status = 1
                self.time[self.status] = time
            elif self.status == 1 and time > (
                self.time[self.status] + self.delay[self.status]
            ):
                self.status = 2
                self.time[self.status] = time
            elif self.status == 2 and time > (
                self.time[self.status] + self.delay[self.status]
            ):
                self.status = 3
                self.time[self.status] = time

    def reset(self, packet: GameTickPacket):
        time = packet.game_info.seconds_elapsed
        self.status = 0
        self.time[self.status] = time


class CustomTextItem(gl.GLGraphicsItem.GLGraphicsItem):
    def __init__(self, X, Y, Z, text):
        gl.GLGraphicsItem.GLGraphicsItem.__init__(self)
        self.text = text
        self.X = X
        self.Y = Y
        self.Z = Z

    def setGLViewWidget(self, GLViewWidget):
        self.GLViewWidget = GLViewWidget

    def setText(self, text):
        self.text = text
        self.update()

    def setX(self, X):
        self.X = X
        self.update()

    def setY(self, Y):
        self.Y = Y
        self.update()

    def setZ(self, Z):
        self.Z = Z
        self.update()

    def paint(self):
        self.GLViewWidget.qglColor(QtCore.Qt.white)
        self.GLViewWidget.renderText(self.X, self.Y, self.Z, self.text)


class Custom3DAxis(gl.GLAxisItem):
    """Class defined to extend 'gl.GLAxisItem'."""

    def __init__(self, parent, color=(0, 0, 0, 0.6)):
        gl.GLAxisItem.__init__(self)
        self.parent = parent
        self.c = color

    def add_labels(self):
        """Adds axes labels."""
        x, y, z = self.size()
        # X label
        self.xLabel = CustomTextItem(X=x / 2, Y=-y / 20, Z=-z / 20, text="X")
        self.xLabel.setGLViewWidget(self.parent)
        self.parent.addItem(self.xLabel)
        # Y label
        self.yLabel = CustomTextItem(X=-x / 20, Y=y / 2, Z=-z / 20, text="Y")
        self.yLabel.setGLViewWidget(self.parent)
        self.parent.addItem(self.yLabel)
        # Z label
        self.zLabel = CustomTextItem(X=-x / 20, Y=-y / 20, Z=z / 2, text="Z")
        self.zLabel.setGLViewWidget(self.parent)
        self.parent.addItem(self.zLabel)

    def add_tick_values(self, xticks=[], yticks=[], zticks=[]):
        """Adds ticks values."""
        x, y, z = self.size()
        xtpos = np.linspace(0, x, len(xticks))
        ytpos = np.linspace(0, y, len(yticks))
        ztpos = np.linspace(0, z, len(zticks))
        # X label
        for i, xt in enumerate(xticks):
            val = CustomTextItem(X=xtpos[i], Y=-y / 200, Z=-z / 200, text=str(xt))
            val.setGLViewWidget(self.parent)
            self.parent.addItem(val)
        # Y label
        for i, yt in enumerate(yticks):
            val = CustomTextItem(X=-x / 200, Y=ytpos[i], Z=-z / 200, text=str(yt))
            val.setGLViewWidget(self.parent)
            self.parent.addItem(val)
        # Z label
        for i, zt in enumerate(zticks):
            val = CustomTextItem(X=-x / 200, Y=-y / 200, Z=ztpos[i], text=str(zt))
            val.setGLViewWidget(self.parent)
            self.parent.addItem(val)

    def paint(self):
        self.setupGLState()
        if self.antialias:
            ogl.glEnable(ogl.GL_LINE_SMOOTH)
            ogl.glHint(ogl.GL_LINE_SMOOTH_HINT, ogl.GL_NICEST)
        ogl.glBegin(ogl.GL_LINES)

        x, y, z = self.size()
        # Draw Z
        ogl.glColor4f(self.c[0], self.c[1], self.c[2], self.c[3])
        ogl.glVertex3f(0, 0, 0)
        ogl.glVertex3f(0, 0, z)
        # Draw Y
        ogl.glColor4f(self.c[0], self.c[1], self.c[2], self.c[3])
        ogl.glVertex3f(0, 0, 0)
        ogl.glVertex3f(0, y, 0)
        # Draw X
        ogl.glColor4f(self.c[0], self.c[1], self.c[2], self.c[3])
        ogl.glVertex3f(0, 0, 0)
        ogl.glVertex3f(x, 0, 0)
        ogl.glEnd()
