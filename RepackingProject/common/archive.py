import shutil


class Archiving:
    def __init__(self, path, expansion, filename=None):
        self.filename = filename
        self.path = path
        self.expansion = expansion

    def make_archive(self):
        path = self.path
        if self.filename:
            path = self.path+self.filename

        shutil.make_archive(path, self.expansion, self.path)

        return f"{path}.{self.expansion}"
