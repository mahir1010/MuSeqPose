from PySide2.QtCore import Signal, QTimer, QObject, QRunnable

from OptiPose.post_processor_interface import PostProcessor


class Thread(QRunnable):

    def __init__(self, index, post_processor: PostProcessor):
        super(Thread, self).__init__()
        self.index = index
        self.post_processor = post_processor
        self.label = post_processor.PROCESS_NAME if post_processor.target_column is None else post_processor.target_column
        self.process_name = post_processor.PROCESS_NAME
        self.signals=ProcessSignals(self.update_progress)
        self.args=None
        self.isRunning = False

    def run(self) -> None:
        try:
            self.isRunning=True
            self.post_processor.process(self.args)
        except Exception as ex:
            self.signals.process_complete.emit(self.index,str(ex))
        self.signals.process_complete.emit(self.index,'')

    def update_progress(self):
        if self.isRunning:
            self.signals.progress_update.emit(self.post_processor.progress)

    def set_args(self,args):
        self.args=args

    def get_output(self):
        return self.post_processor.get_output()

class ProcessSignals(QObject):
    progress_update = Signal(int)
    process_complete = Signal(int,str)

    def __init__(self,update_fn):
        super(ProcessSignals, self).__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(update_fn)
        self.timer.start(1000)
