import typing
from abc import ABCMeta, abstractmethod

from sorsched import models
from sorsched.data import Student, Show, Slot, ShowImp, SlotImp, StudentImp


class Config(metaclass=ABCMeta):
    @abstractmethod
    def shows(self) -> typing.List[Show]:
        pass

    @abstractmethod
    def slots(self) -> typing.List[Slot]:
        pass

    @abstractmethod
    def students(self) -> typing.List[Student]:
        pass


class ConfigImp(Config):
    """
    Represents the full input
    """

    def __init__(self, shows: typing.List[Show], slots: typing.List[Slot], students: typing.List[Student]):
        self._shows = shows
        self._slots = slots
        self._students = students

    @classmethod
    def load_from_db(cls, session):
        shows = cls.load_shows(session)
        slots = cls.load_slots(session)
        students = cls.load_students(session)
        return ConfigImp(shows=shows, slots=slots, students=students)

    def students(self) -> typing.List[Student]:
        return self._students

    def shows(self):
        return self._shows

    def slots(self) -> typing.List[Slot]:
        return self._slots

    @classmethod
    def load_shows(cls, session):
        """
        Load show information into list of show objects
        :return:
        """
        x = []
        for show_obj in session.query(models.Show).all():
            x.append(ShowImp(model=show_obj))
        return x

    @classmethod
    def load_slots(cls, session):
        """
        Load slot information into dict
        :return:
        """
        x = []
        for slot in session.query(models.Slot).all():
            x.append(SlotImp(model=slot))
        return x

    @classmethod
    def load_students(cls, session):
        """
        Load student info and their preferences into dict
        :return:
        """
        x = []
        for student in session.query(models.Student).all():
            x.append(StudentImp(model=student))
        return x
