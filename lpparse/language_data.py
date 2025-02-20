
class LanguageData:
    """Objects of this class hold and maintain language data, which is represented as a list
    of dictionaries, the latter collecting various attributes of the data and the former which
    corresponds to the items in the dataset"""
    def __init__(self):
        self.data = []
        self.index = 1

    def __str__(self):
        stri = ''
        for item in self.data:
            if item.get('index', 0) > 0:
                stri += f"{item.get('index', 0)}. {item.get('expression','')}\n{self.print_attributes(item)}"
        return stri

    def print_attributes(self, items):
        stri = ''
        for key in items.keys():
            stri += f'\t{key}: {items[key]}\n'
        return stri + '\n'

    def reset(self):
        self.data = [{}]
        self.index = 1

    def get_all(self):
        return [dict for dict in self.data[1:]]

    def get(self, i):
        return self.data[i]

    def add(self, dict):
        self.data.append(dict)

    # Finds data dict with index i and adds info_dict into it
    # Used to add attributes from the dataset file

    def update(self, i, info_dict):
        for data_dict in self.data:
            if data_dict.get('index', 0) == i:
                data_dict.update(info_dict)
