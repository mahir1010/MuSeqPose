

from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore

from Keypoint import Keypoint


class KeyPointUI(QWidget):

    keypoint_selected = Signal(int)
    keypoint_deleted = Signal()

    def __init__(self,id,keypoint:Keypoint):
        super().__init__()
        self.id=id
        self.data_point=keypoint
        self.marker = QGraphicsEllipseItem(keypoint.x_loc,keypoint.y_loc,5,5)
        # self.marker.setFlag(QGraphicsItem.ItemIsMovable)
        self.color=QColor.fromRgb(*keypoint.color)
        self.brush=QBrush(self.color)
        self.marker.setBrush(QBrush(self.color))
        self.marker.setVisible(False)
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.annotation_radio_button = QRadioButton(self)
        self.annotation_radio_button.setObjectName(u"isSelected")
        self.annotation_radio_button.setEnabled(True)
        self.annotation_radio_button.setAutoExclusive(False)

        self.horizontalLayout.addWidget(self.annotation_radio_button)

        self.label = QLabel(self)
        self.label.setText(f'<html><b>{keypoint.name}</b></html>')
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.label)

        self.visibility_checkbox = QCheckBox(self)
        self.visibility_checkbox.setObjectName(u"isChecked")
        self.visibility_checkbox.setLayoutDirection(Qt.RightToLeft)

        self.horizontalLayout.addWidget(self.visibility_checkbox)

        self.horizontalLayout.setStretch(1, 1)
        palette = self.palette()
        palette.setColor(self.backgroundRole(),self.color)
        self.setPalette(palette)
        self.show()

    def mousePressEvent(self, event:QMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.annotation_radio_button.setChecked(True)
            self.keypoint_selected.emit(self.id)
        elif event.button() == Qt.MidButton:
            self.visibility_checkbox.toggle()
            self.keypoint_deleted.emit(None)
