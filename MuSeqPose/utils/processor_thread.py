from PySide2.QtCore import Signal, QTimer, QObject, QRunnable

from cvkit.pose_estimation.processors.processor_interface import Processor


class ProcessorThread(QRunnable):

    def __init__(self, index, processor: Processor):
        super(ProcessorThread, self).__init__()
        self.index = index
        self.processor = processor
        self.label = getattr(processor, 'target_column', None)
        self.process_name = processor.PROCESSOR_NAME
        self.signals = ProcessSignals(self.update_progress)
        self.args = None
        self.isRunning = False
        self.setAutoDelete(False)

    def run(self) -> None:
        try:
            self.isRunning = True
            self.processor.process(self.args)
        except Exception as ex:
            self.signals.process_complete.emit(self.index, str(ex))
        self.signals.process_complete.emit(self.index, '')

    def update_progress(self):
        if self.isRunning:
            self.signals.progress_update.emit(self.processor._progress)

    def set_args(self, args):
        self.args = args

    def get_output(self):
        return self.processor.get_output()


class ProcessSignals(QObject):
    progress_update = Signal(int)
    process_complete = Signal(int, str)

    def __init__(self, update_fn):
        super(ProcessSignals, self).__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(update_fn)
        self.timer.start(1000)
