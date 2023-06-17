from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QWidget

from MuSeqPose import get_resource
from MuSeqPose.config import MuSeqPoseConfig
from MuSeqPose.utils.ui_generators import generate_radio_buttons, generate_checkboxes


class HeadingAnalysisWidget(QWidget):

    def __init__(self, config: MuSeqPoseConfig):
        super(HeadingAnalysisWidget, self).__init__()
        file = QFile(get_resource('HeadingAnalysis.ui'))
        file.open(QFile.ReadOnly)
        self.ui = QUiLoader().load(file)
        self.hd_v1_buttons = generate_radio_buttons(config.body_parts)
        for btn in self.hd_v1_buttons:
            self.ui.hd_v1.layout().addWidget(btn)
        self.hd_v2_buttons = generate_radio_buttons(config.body_parts)
        for btn in self.hd_v2_buttons:
            self.ui.hd_v2.layout().addWidget(btn)

        self.bd_v1_buttons = generate_radio_buttons(config.body_parts)
        for btn in self.bd_v1_buttons:
            self.ui.bd_v1.layout().addWidget(btn)
        self.bd_v2_buttons = generate_radio_buttons(config.body_parts)
        for btn in self.bd_v2_buttons:
            self.ui.bd_v2.layout().addWidget(btn)
        self.md_v1_buttons = generate_checkboxes(config.body_parts)
        for btn in self.md_v1_buttons:
            self.ui.md_v1.layout().addWidget(btn)
