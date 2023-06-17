from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class KeyPointController(QWidget):
    keypoint_selected = Signal(int)
    keypoint_visibility_toggled = Signal(int)

    def __init__(self, id, name, color):
        super().__init__()
        self.id = id
        self.name = name
        self.first_click = True
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.annotation_radio_button = QRadioButton(self)
        self.annotation_radio_button.setObjectName(u"isSelected")
        self.annotation_radio_button.setEnabled(True)
        self.annotation_radio_button.setAutoExclusive(False)
        self.horizontalLayout.addWidget(self.annotation_radio_button)

        self.label = QLabel(self)
        self.label.setText(f'<html><b>{self.name}</b></html>')
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.label)

        self.visibility_checkbox = QCheckBox(self)
        self.visibility_checkbox.setObjectName(u"isChecked")
        self.visibility_checkbox.setLayoutDirection(Qt.RightToLeft)
        self.horizontalLayout.addWidget(self.visibility_checkbox)

        self.horizontalLayout.setStretch(1, 1)

        self.setStyleSheet(f"""QCheckBox::indicator::checked{{
                                background-color:rgb({color[0]},{color[1]},{color[2]});
                                }}
                           QCheckBox::indicator{{
                           border:2px solid rgb({max(10, color[0] - 30)},{max(10, color[1] - 30)},{max(10, color[2] - 30)});
                           }}""")
        self.show()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.annotation_radio_button.setChecked(True)
            self.keypoint_selected.emit(self.id)
            if self.first_click:
                self.visibility_checkbox.setChecked(True)
