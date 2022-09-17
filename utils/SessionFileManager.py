
class SessionFileManager:

    def __init__(self,config):
        self.session_video_readers = {}
        self.session_data_readers = {}
        for view in config['views']:
            self.session_data_readers[view]=None
            self.session_video_readers[view]=None
        if config.get('OptiPose',{}).get('enabled',False):
            self.session_data_readers['OptiPose'] = None
            self.session_video_readers['OptiPose'] = None

    def register_video_reader(self,view,reader):
        if view in self.session_video_readers:
            self.session_video_readers[view]=reader

    def register_data_reader(self,view,reader):
        if view in self.session_data_readers:
            self.session_data_readers[view]=reader
