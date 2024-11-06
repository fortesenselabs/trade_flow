import uuid
from abc import ABCMeta


class Identifiable(object, metaclass=ABCMeta):
    """Identifiable mixin for adding a unique `id` property to instances of a class."""

    @property
    def id(self) -> str:
        """Gets the identifier for the object.

        Returns
        -------
        str
           The identifier for the object.
        """
        if not hasattr(self, "_id"):
            self._id = str(uuid.uuid4())
        return self._id

    @id.setter
    def id(self, identifier: str) -> None:
        """Sets the identifier for the object

        Parameters
        ----------
        identifier : str
            The identifier to set for the object.
        """
        self._id = identifier
