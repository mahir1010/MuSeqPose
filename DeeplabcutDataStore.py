import numpy as np
import pandas as pd

from DataStoreInterface import DataStoreInterface
from Keypoint import Keypoint


class DeeplabcutDataStore(DataStoreInterface):



    def __init__(self, path):
        self.path = path
        self.data = pd.read_csv(path, header=[0, 1, 2], index_col=0)
        self.scorer = self.data.columns[0][0]
        if (self.scorer, 'activity', 'name') not in self.data.columns:
            self.data[self.scorer, 'activity', 'name'] = ""

    def set_activity(self, activity, index) -> None:
        self.data.loc[index,(self.scorer,'activity','name')]=activity

    def get_activity(self, index) -> str:
        return self.data.loc[index,(self.scorer,'activity','name')]

    def get_keypoint_location(self, keypoint: Keypoint, index) -> Keypoint:
        name = keypoint.name
        keypoint.set_location(self.data.loc[index, (self.scorer, name, 'x')],
                              self.data.loc[index, (self.scorer, name, 'y')])
        keypoint.set_likelihood(self.data.loc[index, (self.scorer, name, 'likelihood')])
        return keypoint

    def set_keypoint_location(self, keypoint: Keypoint, index) -> Keypoint:
        name = keypoint.name
        self.data.loc[index, (self.scorer, name, 'x')] = keypoint.x_loc
        self.data.loc[index, (self.scorer, name, 'y')] = keypoint.y_loc
        self.data.loc[index, (self.scorer, name, 'likelihood')] = keypoint.likelihood
        return keypoint

    def save_file(self, path: str) -> None:
        self.data.to_csv(path)

    def get_keypoint_slice(self, name: str, slice_indices: list) -> np.ndarray:
        return self.data.loc[slice_indices[0]:slice_indices[1], (self.scorer, name, ('x', 'y'))].to_numpy()

    def set_keypoint_slice(self, name: str, slice_indices: list, data: np.ndarray) -> None:
        self.data.loc[slice_indices[0]:slice_indices[1], (self.scorer, name, 'x')] = data[:, 0]
        self.data.loc[slice_indices[0]:slice_indices[1], (self.scorer, name, 'y')] = data[:, 1]
