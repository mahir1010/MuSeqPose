from PySide2.QtCore import Signal
from PySide2.QtGui import Qt, QColor, QBrush, QPen
from PySide2.QtWidgets import QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsItem

from MuSeqPose.utils.session_manager import SessionManager
from cvkit.pose_estimation import Skeleton


class Marker(QGraphicsEllipseItem):
    marker_clicked = Signal(int, bool)

    def __init__(self, idx, x, y, w, h, color):
        super(Marker, self).__init__(x, y, w, h)
        self.idx = idx
        self.color = QColor.fromRgb(*color)
        self.setPen(Qt.NoPen)
        self.setVisible(False)
        self.setBrush(QBrush(self.color))
        self.setAcceptHoverEvents(True)
        # self.setFlag(QGraphicsItem.ItemIsSelectable,True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)


class SkeletonController():

    def __init__(self, session_manager: SessionManager, threshold=0.6, marker_size=4):
        self.markers = {}
        self.lines = []
        self.threshold = threshold
        self.config = session_manager.config
        self.marker_size = marker_size
        self.marker_offset = marker_size // 2
        pen = QPen(Qt.white, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.selected_marker = None
        for lines in self.config.skeleton:
            self.lines.append(QGraphicsLineItem(0, 0, 1, 1))
            self.lines[-1].setPen(pen)
        for idx, (name, color) in enumerate(zip(self.config.body_parts, self.config.colors)):
            marker = Marker(idx, 0, 0, self.marker_size, self.marker_size, color)
            self.markers[name] = marker

    def update_skeleton(self, skeleton: Skeleton):
        for i, part in enumerate(self.config.body_parts):
            if skeleton[part] >= self.threshold:
                self.markers[part].setVisible(True)
                self.markers[part].setX(skeleton[part][0] - self.marker_offset)
                self.markers[part].setY(skeleton[part][1] - self.marker_offset)
                self.markers[part].setToolTip(
                    f'{part:10} ({round(skeleton[part].likelihood, 2)})\n{int(skeleton[part][0]):5},{int(skeleton[part][1]):5}')
            else:
                self.markers[part].setVisible(False)
            self.markers[part].update()

        for line, end_points in zip(self.lines, self.config.skeleton):
            if all([self.markers[point].isVisible() for point in end_points]):
                p1 = skeleton[end_points[0]]
                p2 = skeleton[end_points[1]]
                line.setLine(p1[0], p1[1], p2[0], p2[1])
                line.setVisible(True)
            else:
                line.setVisible(False)
            line.update()

    def mark_selected(self, name, state):
        if state:
            self.markers[name].setPen(Qt.SolidLine)
        else:
            self.markers[name].setPen(Qt.NoPen)
