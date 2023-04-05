import os

from PySide2.QtCore import Signal, QFile, QThreadPool, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget, QVBoxLayout

from MuSeqPose import get_resource


class OptiPoseCard(QWidget):
    delete_operation = Signal()
    execution_completed = Signal()

    def __init__(self, post_processors: list):
        super(OptiPoseCard, self).__init__()
        file = QFile(get_resource('OperationCard.ui'))
        file.open(QFile.ReadOnly)
        base_layout = QVBoxLayout()
        base_layout.setMargin(0)
        self.ui = QUiLoader().load(file)
        base_layout.addWidget(self.ui)
        # self.ui.move_up.setVisible(False)
        # self.ui.move_down.setVisible(False)
        self.ui.delete_op.clicked.connect(self.delete_operation_clicked)
        self.progress = [False] * len(post_processors)
        self.post_processors = post_processors
        self.exception_occurred = False
        self.exception_message = ''
        self.ui.title.setText(post_processors[0].process_name)
        self.progress_bars = []
        for post_processor in post_processors:
            layout = QHBoxLayout()
            layout.setMargin(0)
            label = QLabel(post_processor.label)
            layout.addWidget(label, 1)
            label.setFixedHeight(30)
            bar = QProgressBar()
            bar.setFixedHeight(30)
            bar.setValue(0)
            bar.setAlignment(Qt.AlignCenter)
            bar.setMaximum(100)
            self.progress_bars.append(bar)
            post_processor.signals.progress_update.connect(bar.setValue)
            post_processor.signals.process_complete.connect(self.sub_process_completed)
            layout.addWidget(bar, 1)
            self.ui.progress_container.addLayout(layout)
        self.threadpool = QThreadPool()
        self.setLayout(base_layout)
        self.adjustSize()
        # self.show()

    def execute(self):
        self.ui.delete_op.setEnabled(False)
        for post_processor in self.post_processors:
            self.threadpool.start(post_processor)

    def sub_process_completed(self, index, status):
        if status != '' and not self.exception_occurred:
            self.exception_occurred = True
            self.exception_message = status
        self.post_processors[index].signals.timer.stop()
        self.progress[index] = True
        self.progress_bars[index].setValue(100)
        if all(self.progress):
            self.execution_completed.emit()

    def set_args(self, arg):
        for post_processor in self.post_processors:
            post_processor.set_args(arg)

    def get_output(self):
        return self.post_processors[0].get_output()

    def delete_operation_clicked(self, event):
        self.delete_operation.emit()
