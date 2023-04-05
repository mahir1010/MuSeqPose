from importlib.resources import files, as_file

import MuSeqPose.Resources


def get_resource(name):
    with as_file(files(MuSeqPose.Resources).joinpath(name)) as file:
        return str(file)
