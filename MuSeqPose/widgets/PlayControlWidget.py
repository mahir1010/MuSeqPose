from abc import ABC, abstractmethod

from PySide2.QtCore import QFile, QTimer, Signal
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QWidget

from MuSeqPose.utils.session_manager import SessionManager


class MetaClass(type(QWidget), type(ABC)):
    pass


class PlayControlWidget(QWidget, ABC, metaclass=MetaClass):
    update_status = Signal(str)

    def __init__(self, session_manager: SessionManager, ui_file, threshold=0.6, parent=None):
        super(PlayControlWidget, self).__init__(parent)
        self.config = session_manager.config
        self.session_manager = session_manager
        self.threshold = threshold
        self.frame_number = 0
        self.is_video_playing = False
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
        self.ui = QUiLoader().load(ui_file)
        self.ui.resetViewButton.clicked.connect(self.reset_view)
        self.ui.nextFrameButton.clicked.connect(self.render_next_frame)
        self.ui.prevFrameButton.clicked.connect(self.prev_button_pressed)
        self.ui.playPauseButton.clicked.connect(self.play_video)
        self.ui.seekButton.clicked.connect(self.seek_ui_input)
        self.ui.seekBar.setMinimum(0)
        self.ui.seekBar.setTracking(False)
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.print_fps)
        self.fps_last_frame_number = 0

    def print_fps(self):
        self.update_status.emit(f'FPS: {self.frame_number - self.fps_last_frame_number}')
        self.fps_last_frame_number = self.frame_number

    @abstractmethod
    def update_frame_number(self):
        pass

    @abstractmethod
    def render_next_frame(self, event=None):
        pass

    @abstractmethod
    def seek(self, frame_number):
        pass

    @abstractmethod
    def reset_view(self, event=None):
        pass

    def seek_ui_input(self, event=None):
        if type(event) != int:
            try:
                frame_number = int(self.ui.seekValue.text())
            except ValueError:
                return
        else:
            frame_number = event
        self.seek(frame_number)

    @abstractmethod
    def play_video(self, event):
        pass

    def prev_button_pressed(self, event):
        if self.frame_number != 0:
            self.seek(self.frame_number - 1)

    def reset_current_view(self, event):
        self.reset_view()
