from MuSeqPose.config import MuSeqPoseConfig


class SessionManager:

    def __init__(self, config: MuSeqPoseConfig):
        self.config = config
        self.session_video_readers = {}
        self.session_data_readers = {}
        for view in config.views:
            self.session_data_readers[view] = None
            self.session_video_readers[view] = None
        self.session_data_readers['CVKit'] = None
        self.session_video_readers['CVKit'] = None

    def register_video_reader(self, view, reader):
        if view in self.session_video_readers:
            self.session_video_readers[view] = reader

    def register_data_reader(self, view, reader):
        if view in self.session_data_readers:
            self.session_data_readers[view] = reader

    def get_2D_data_readers(self):
        return [self.session_data_readers[val] for val in self.session_data_readers if val != 'CVKit']
