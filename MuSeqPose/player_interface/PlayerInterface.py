from abc import ABC, abstractmethod

from MuSeqPose.utils.session_manager import SessionManager


class PlayerInterface(ABC):

    def __init__(self, session_manager: SessionManager, view_name, view_data):
        self.config = session_manager.config
        self.session_manager = session_manager
        self.view_name = view_name
        self.view_data = view_data
        self.data_store = None
        self.frame_number = 0
        self.is_video_playing = False
        self.data_point = None

    @abstractmethod
    def render_next_frame(self, image_viewer):
        pass

    @abstractmethod
    def render_previous_frame(self):
        pass

    @abstractmethod
    def seek(self, frame_number):
        pass

    @abstractmethod
    def get_number_of_frames(self):
        pass

    @abstractmethod
    def release(self):
        pass
