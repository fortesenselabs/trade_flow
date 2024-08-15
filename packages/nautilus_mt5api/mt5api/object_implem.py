
class Object(object):
    def __str__(self):
        return "Object"

    def __repr__(self):
        return str(id(self)) + ": " + self.__str__()