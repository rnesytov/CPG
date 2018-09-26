from bson.objectid import ObjectId
from typing import get_type_hints, cast


class classproperty(property):  # pylint: disable=invalid-name, too-few-public-methods
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, owner):
        return self.func(owner)


class Struct:
    _id: ObjectId

    @classproperty
    def _annotations(self):
        return get_type_hints(self)

    @classproperty
    def fields(self):
        return self._annotations.keys()

    @classmethod
    def load(cls, attributes):
        return cls(attributes=attributes)

    @classmethod
    def from_kwargs(cls, **kwargs):
        return cls(attributes=kwargs)

    def __init__(self, attributes):
        self._attributes = attributes

        self._fill_attrs()

    def _fill_attrs(self):
        for k, v in self._annotations.items():
            setattr(self, k, cast(v, self._attributes.get(k)))

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def serialize(self):
        return {
            attr: getattr(self, attr)
            for attr in self.fields
        }

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value: ObjectId) -> None:
        self._id = value

    def merge(self, new_attributes):
        data = self.serialize()
        data.update(new_attributes)

        return self.__class__(attributes=data)

    def __setattr__(self, key, value) -> None:
        if key in self.fields:
            self._attributes[key] = value

        super().__setattr__(key, value)

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__, self.id)

    def __eq__(self, other):
        if isinstance(other, dict):
            return self._attributes == other
        elif isinstance(other, self.__class__):
            return self._attributes == other._attributes  # pylint: disable=protected-access
        else:
            raise TypeError

    __repr__ = __str__
