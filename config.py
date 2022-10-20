import os

from OptiPose.config import OptiPoseConfig


class PlotConfig:
    def __init__(self, data_dictionary):
        self.type = data_dictionary['type']
        self.size = data_dictionary['size']
        self.is_static = data_dictionary['static']
        self.annotation_file = data_dictionary['annotation_file']
        self.annotation_file_flavor = data_dictionary['annotation_file_flavor']
        self.annotation_columns = data_dictionary['annotation_columns']

    def export_dict(self):
        return {
            'type': self.type,
            'size': self.size,
            'static': self.is_static,
            'annotation_file': self.annotation_file,
            'annotation_file_flavor': self.annotation_file_flavor,
            'annotation_columns': self.annotation_columns
        }


class ReconstructionPlotConfig(PlotConfig):
    def __init__(self, data_dictionary):
        super(ReconstructionPlotConfig, self).__init__(data_dictionary)
        self.normalization_max_limit = data_dictionary['normalization_max_limit']
        self.normalization_min_limit = data_dictionary['normalization_min_limit']
        self.color = data_dictionary['color']
        self.environment = data_dictionary['environment']

    def export_dict(self):
        data_dictionary = super(ReconstructionPlotConfig, self).export_dict()
        data_dictionary['normalization_max_limit'] = self.normalization_max_limit
        data_dictionary['normalization_min_limit'] = self.normalization_min_limit
        data_dictionary['color'] = self.color
        data_dictionary['environment'] = self.environment
        return data_dictionary


class AnnotationConfig:
    def __init__(self, data_dictionary):
        self.view = data_dictionary.get('view', None)
        self.annotation_file = data_dictionary['annotation_file']
        self.annotation_file_flavor = data_dictionary['annotation_file_flavor']
        self.video_file = data_dictionary['video_file']
        assert os.path.isfile(self.video_file)
        self.video_reader = data_dictionary['video_reader']

    def export_dict(self):
        return {'view': self.view,
                'annotation_file': self.annotation_file,
                'annotation_file_flavor': self.annotation_file_flavor,
                'video_file': self.video_file,
                'video_reader': self.video_reader
                }


class MuSeqPoseConfig(OptiPoseConfig):

    def __init__(self, path):
        super(MuSeqPoseConfig, self).__init__(path)
        self.annotation_views = {}
        if 'annotation' in self.data_dictionary:
            for annotation_view in self.data_dictionary['annotation']:
                assert annotation_view != 'OptiPose' and annotation_view != 'Sync'
                data = self.data_dictionary['annotation'][annotation_view]
                self.annotation_views[annotation_view] = AnnotationConfig(data)
        self.sync_views = self.data_dictionary['sync_views']
        self.reprojection_toolbox_enabled = self.data_dictionary['reprojection_toolbox'] and all(
            [self.annotation_views[annotation].view is not None for annotation in self.annotation_views])
        self.behaviours = self.data_dictionary['behaviours']
        if len(self.behaviours)==0:
            self.behaviours.append("NA")
        self.plots = {}
        if 'plots' in self.data_dictionary:
            for plot in self.data_dictionary['plots']:
                if self.data_dictionary['plots'][plot]['type'] == 'Reconstruction':
                    self.plots[plot] = ReconstructionPlotConfig(self.data_dictionary['plots'][plot])

    def get_dlt_coefficients(self, view_name):
        if view_name in self.views:
            return self.views[view_name].dlt_coefficients
        else:
            return None

    def export_dict(self):
        data_dict = super(MuSeqPoseConfig, self).export_dict()
        data_dict['annotation'] = {view: self.annotation_views[view].export_dict() for view in self.annotation_views}
        data_dict['sync_views'] = self.sync_views
        data_dict['reprojection_toolbox'] = self.reprojection_toolbox_enabled
        data_dict['behaviours'] = self.behaviours
        data_dict['plots'] = {plot: self.plots[plot].export_dict() for plot in self.plots}
        return data_dict
