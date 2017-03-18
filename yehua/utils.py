import os


def get_resource_dir(folder):
    current_path = os.path.dirname(__file__)
    resource_path = os.path.join(current_path, folder)
    return resource_path
