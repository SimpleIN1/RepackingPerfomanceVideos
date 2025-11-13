import os
import shutil
import zipfile


class Archiving:
    def __init__(self, path, expansion, filename=None):
        self.filename = filename
        self.path = path
        self.expansion = expansion

    def make_archive(self) -> str:
        path = self.path
        if self.filename:
            path = self.path+self.filename

        shutil.make_archive(path, self.expansion, self.path)

        return f"{path}.{self.expansion}"


class ArchivingUnpack:
    def __init__(self, path):
        self.path = path

    def unpack_archive(self) -> None:
        extract_dir = os.path.basename(self.path).split('.')[0]
        path_save = os.path.join(os.path.dirname(self.path), extract_dir)

        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            zip_ref.extractall(path_save)
        # shutil.unpack_archive(self.path, path_save)
