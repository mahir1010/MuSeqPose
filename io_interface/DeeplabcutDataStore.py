import numpy as np
import pandas as pd

from io_interface.DataStoreInterface import DataStoreInterface
from Keypoint import Keypoint
from Skeleton import Skeleton, Part


class DeeplabcutDataStore(DataStoreInterface):

    def __init__(self, body_parts,path):
        super().__init__(body_parts)
        self.path = path
        self.data = pd.read_csv(path, header=[0, 1, 2], index_col=0)
        self.scorer = self.data.columns[0][0]
        if (self.scorer, 'behaviour', 'name') not in self.data.columns:
            self.data[self.scorer, 'behaviour', 'name'] = ""

    def get_skeleton(self, index) -> Skeleton:
        return self.build_skeleton(self.data.iloc[index])

    def set_skeleton(self, index, skeleton: Skeleton) -> None:
        for part in self.body_parts:
            self.set_marker(index,skeleton[part])
        self.set_behaviour(index,skeleton.behaviour)

    def set_behaviour(self, index, behaviour) -> None:
        self.data.loc[index, (self.scorer, 'behaviour', 'name')] = behaviour

    def get_behaviour(self, index) -> str:
        return self.data.loc[index, (self.scorer, 'behaviour', 'name')]

    def get_marker(self, index,name) -> Part:
        return Part([self.data.loc[index, (self.scorer, name, 'x')],self.data.loc[index, (self.scorer, name, 'y')],0.0],name,self.data.loc[index, (self.scorer, name, 'likelihood')])

    def set_marker(self,index, part: Part) -> None:
        name = part.name
        self.data.loc[index, (self.scorer, name, 'x')] = part[0]
        self.data.loc[index, (self.scorer, name, 'y')] = part[1]
        self.data.loc[index, (self.scorer, name, 'likelihood')] = part.likelihood

    def save_file(self, path: str) -> None:
        self.data.to_csv(path)

    def get_keypoint_slice(self, slice_indices: list, name: str) -> np.ndarray:
        return self.data.loc[slice_indices[0]:slice_indices[1], (self.scorer, name, ('x', 'y'))].to_numpy()

    def set_keypoint_slice(self, slice_indices: list, name: str, data: np.ndarray) -> None:
        self.data.loc[slice_indices[0]:slice_indices[1], (self.scorer, name, 'x')] = data[:, 0]
        self.data.loc[slice_indices[0]:slice_indices[1], (self.scorer, name, 'y')] = data[:, 1]

    def build_skeleton(self, row) -> Skeleton:
        part_map = {}
        likelihood_map = {}
        for name in self.body_parts:
            part_map[name] = [float(row[(self.scorer,name, 'x')]), float(row[(self.scorer,name, 'y')]), 0.0]
            likelihood_map[name] = float(row[(self.scorer,name, 'likelihood')])
        return Skeleton(self.body_parts,part_map=part_map,likelihood_map=likelihood_map,behaviour=row[(self.scorer,'behaviour','name')])

    def row_iterator(self):
        for index,row in self.data.iterrows():
            yield self.build_skeleton(row)
