import glob
import json
import os
from pathlib import Path

from cvkit.pose_estimation.config import PoseEstimationConfig


class PlotConfig:
    def __init__(self, data_dictionary):
        self.type = data_dictionary['type']
        self.size = data_dictionary['size']
        self.is_static = data_dictionary['static']
        self.annotation_file = data_dictionary['annotation_file']
        self.annotation_file_flavor = data_dictionary['annotation_file_flavor']
        self.annotation_columns = data_dictionary.get('annotation_columns', None)
        self.normalization_max_limit = data_dictionary['normalization_max_limit']
        self.normalization_min_limit = data_dictionary['normalization_min_limit']

    def export_dict(self):
        return {
            'type': self.type,
            'size': self.size,
            'static': self.is_static,
            'annotation_file': self.annotation_file,
            'annotation_file_flavor': self.annotation_file_flavor,
            'annotation_columns': self.annotation_columns,
            'normalization_max_limit': self.normalization_max_limit,
            'normalization_min_limit': self.normalization_min_limit,
        }


class LinePlotConfig(PlotConfig):
    def __init__(self, data_dictionary):
        super(LinePlotConfig, self).__init__(data_dictionary)
        self.lines = data_dictionary['lines']

    def export_dict(self):
        data_dictionary = super(LinePlotConfig, self).export_dict()
        data_dictionary['lines'] = self.lines
        return data_dictionary


class ReconstructionPlotConfig(PlotConfig):
    def __init__(self, data_dictionary):
        super(ReconstructionPlotConfig, self).__init__(data_dictionary)
        self.color = data_dictionary['color']
        self.environment = data_dictionary['environment']

    def export_dict(self):
        data_dictionary = super(ReconstructionPlotConfig, self).export_dict()
        data_dictionary['color'] = self.color
        data_dictionary['environment'] = self.environment
        return data_dictionary


class MuSeqPoseConfig(PoseEstimationConfig):

    def __init__(self, path):
        super(MuSeqPoseConfig, self).__init__(path)
        self.pipeline_directory = self.data_dictionary.get('pipeline_directory', '')
        if not os.path.exists(self.pipeline_directory):
            self.pipeline_directory = self.output_folder
        self.loaded_pipelines = {}
        pipelines = glob.glob(os.path.join(self.pipeline_directory, '*.pipeline'))
        for pipeline in pipelines:
            try:

                self.loaded_pipelines[Path(pipeline).stem] = json.load(open(pipeline))
            except:
                pass
        self.sync_views = self.data_dictionary.get('sync_views', [])
        self.calibration_toolbox_enabled = self.data_dictionary.get('calibration_toolbox', {}).get('enabled', False)
        self.calibration_static_points = []
        if self.calibration_toolbox_enabled:
            self.calibration_static_points = self.data_dictionary['calibration_toolbox'].get('static_points', [])
            for view in self.views.values():
                if view.f_px == -1 or len(view.principal_point) == 0 or len(view.resolution) == 0:
                    print("Camera information missing. Disabling calibration tool...")
                    self.calibration_toolbox_enabled = False
            self.calibration_static_point_locations = {view: {} for view in self.views}
            for view in self.views:
                for static_point in self.calibration_static_points:
                    self.calibration_static_point_locations[view][static_point] = self.data_dictionary[
                        'calibration_toolbox'].get('views', {}).get(view, {}).get(static_point, [-1, -1])
        self.reprojection_toolbox_enabled = not self.calibration_toolbox_enabled and self.data_dictionary.get(
            'reprojection_toolbox', False) and all(
            [self.annotation_views[annotation].view is not None for annotation in self.annotation_views])
        self.behaviours = self.data_dictionary.get('behaviours', [])
        if len(self.behaviours) == 0:
            self.behaviours.append("NA")
        self.plots = {}
        if 'plots' in self.data_dictionary:
            for plot in self.data_dictionary['plots']:
                if self.data_dictionary['plots'][plot]['type'] == 'Reconstruction':
                    self.plots[plot] = ReconstructionPlotConfig(self.data_dictionary['plots'][plot])
                elif self.data_dictionary['plots'][plot]['type'] == 'Line':
                    self.plots[plot] = LinePlotConfig(self.data_dictionary['plots'][plot])

    def get_dlt_coefficients(self, view_name):
        if view_name in self.views:
            return self.views[view_name].dlt_coefficients
        else:
            return None

    def export_dict(self):
        data_dict = super(MuSeqPoseConfig, self).export_dict()
        data_dict['sync_views'] = self.sync_views
        data_dict['reprojection_toolbox'] = self.reprojection_toolbox_enabled
        data_dict['behaviours'] = self.behaviours
        data_dict['pipeline_directory'] = self.pipeline_directory
        data_dict['calibration_toolbox'] = {'enabled': self.calibration_toolbox_enabled}
        data_dict['calibration_toolbox']['static_points'] = self.calibration_static_points
        data_dict['calibration_toolbox']['views'] = {
            view: {point: self.calibration_static_point_locations[view][point] for point in
                   self.calibration_static_points} for view in self.views}
        data_dict['plots'] = {plot: self.plots[plot].export_dict() for plot in self.plots}
        return data_dict
