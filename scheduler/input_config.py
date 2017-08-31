import typing
from typing import Dict

from scheduler import db, models
from scheduler.models import ShowPreference, Slot
from scheduler.data import Student, Show, Day, DayAssignment


class Config(object):
    def __init__(self, d: dict):
        self.d = d

    @classmethod
    def load_from_db(cls):
        d = {}
        d['shows'] = cls.load_shows()
        d['days'] = cls.load_slots()
        d['students'] = cls.load_students()
        return Config(d=d)

    def students(self) -> typing.Iterable[Student]:
        x = []
        for name, d in self.d['students'].items():
            x.append(Student(name=name,
                             show_utilities=d['show-utilities'],
                             available_days=d['available-days'])
                     )
        return x

    def shows(self):
        x = {}
        for name, d in self.d['shows'].items():
            x[name] = Show(name=name, min_students=d['min-students'], max_students=d['max-students'], )
        return x

    def days(self) -> typing.Dict[str, Day]:
        days = {}
        for name, x in self.d['days'].items():
            days[name] = Day(name=name, max_shows=x['max-shows'])
        return days

    def test(self):
        print('students:')
        print(self.students())
        print('shows:')
        print(self.shows())
        print('days:')
        print(self.days())

    @classmethod
    def load_shows(cls):
        """
        Load show information into dict
        :return:
        """
        x = {}
        for show in db.session.query(models.Show).all():
            x[show.name] = {
                'min-students':show.min_students,
                'max-students':show.max_students,
            }
        return x

    @classmethod
    def load_slots(cls):
        """
        Load slot information into dict
        :return:
        """
        x = {}
        for slot in db.session.query(models.Slot).all():
            x[slot.name] = {'max-shows':slot.max_shows}
        return x

    @classmethod
    def load_students(cls):
        """
        Load student info and their preferences into dict
        :return:
        """
        x = {}
        for student in db.session.query(models.Student).all():
            x[student.name] = cls.get_student_dict(student=student)
        return x

    @classmethod
    def get_student_dict(cls, student):
        """
        Get student preferences into a dict
        :param student:
        :return:
        """
        x = {'show-utilities': {}, 'available-days': []}
        for p in db.session.query(ShowPreference).filter(ShowPreference.student_name == student.name):
            x['show-utilities'][p.show_name] = p.preference
        for slot in db.session.query(Slot).all():
            x['available-days'].append(slot.name)
        return x


class FixedDayConf(object):
    def __init__(self, shows: Dict[str, Show], students: Dict[str, Student], day_assignment: DayAssignment = None):
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