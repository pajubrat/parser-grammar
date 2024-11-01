
class LanguageData:
    """Objects of this class hold and maintain language data, which is represented as a list
    of dictionaries, the latter collecting various attributes of the data and the former which
    corresponds to the items in the dataset"""
    def __init__(self):
        self.data = []
        self.index = 1

    def reset(self):
        self.data = [{}]
        self.index = 1

    def get_all(self):
        return [dict for dict in self.data[1:]]

    def get(self, i):
        return self.data[i]

    def add(self, dict):
        self.data.append(dict)

    def update(self, i, dict):
        self.data[i].update(dict)
