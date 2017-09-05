import typing
from abc import ABCMeta, abstractmethod
from typing import Dict

from sorsched import db, models
from sorsched.data import Student, Show, SlotAssignment, Slot, Instrument, ShowImp, SlotImp, StudentImp


class Config(metaclass=ABCMeta):
    @abstractmethod
    def shows(self)-> typing.List[Show]:
        pass

    @abstractmethod
    def slots(self)-> typing.List[Slot]:
        pass

    @abstractmethod
    def students(self)-> typing.List[Student]:
        pass


class ConfigImp(Config):
    """
    Represents the full input
    """
    def __init__(self, shows: typing.List[Show], slots: typing.List[Slot], students: typing.List[Student]):
        self._shows= shows
        self._slots=slots
        self._students=students

    @classmethod
    def load_from_db(cls):
        shows  = cls.load_shows()
        slots = cls.load_slots()
        students = cls.load_students()
        return ConfigImp(shows=shows,slots=slots,students=students)

    def students(self) -> typing.List[Student]:
        return self._students

    def shows(self):
        return self._shows

    def slots(self) -> typing.List[Slot]:
        return self._slots

    @classmethod
    def load_shows(cls):
        """
        Load show information into list of show objects
        :return:
        """
        x = []
        for show_obj in db.session.query(models.Show).all():
            x.append(ShowImp(model=show_obj))
        return x

    @classmethod
    def load_slots(cls):
        """
        Load slot information into dict
        :return:
        """
        x = []
        for slot in db.session.query(models.Slot).all():
            x.append(SlotImp(model=slot))
        return x

    @classmethod
    def load_students(cls):
        """
        Load student info and their preferences into dict
        :return:
        """
        x = []
        for student in db.session.query(models.Student).all():
            x.append(StudentImp(model=student))
        return x


class FixedDayConf(object):
    def __init__(self, shows: Dict[str, Show], students: Dict[str, Student], day_assignment: SlotAssignment = None):
        self._shows = shows
        self._students = students
        self._day_assignment = day_assignment

    def __repr__(self):
        return '<FixedDayConf(assignment={})>'.format(self._day_assignment)

    def show_slots(self):
        """
        Get a dictionary of show_name -> slot_name mapping
        :return:
        """
        return self._day_assignment.d

    def is_available(self, student, show):
        return show in self._students[student].shows()

    def students(self):
        return list(self._students.keys())

    def shows(self):
        return list(self._shows.keys())

    def min_students(self, show):
        return self._shows[show].min_students

    def max_students(self, show):
        return self._shows[show].max_students

    def utility(self, student, show):
        assert student in self._students
        x = self._students[student]
        return x.utility(show)