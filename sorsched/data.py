import typing
from typing import Dict


class Student(object):
    def __init__(self, name: str = None, show_utilities: Dict[str, float] = None,
                 available_days: typing.List[str] = None):
        self.name = name
        self.show_utilities = show_utilities
        self.available_days = available_days

    def __repr__(self):
        return '<Student(name={name}, show_utilities={show_utilities}, available_days={available_days})>'.format(
            name=self.name, show_utilities=self.show_utilities, available_days=self.available_days
        )

    def shows(self):
        return self.show_utilities.keys()

    def days(self):
        return self.available_days

    def utility(self, show):
        if show in self.show_utilities:
            return self.show_utilities[show]
        else:
            return 0


class Show(object):
    def __init__(self, name: str = None, min_students: int = None, max_students: int = None):
        self.name = name
        self.min_students = min_students
        self.max_students = max_students

    def __repr__(self):
        return '<Show(name={name}, min_students={min_students}, max_students={max_students})>'.format(
            name=self.name, min_students=self.min_students, max_students=self.max_students
        )


class Day(object):
    def __init__(self, name: str = None, max_shows: int = None, ):
        self.max_shows = max_shows
        self.name = name


class DayAssignmentException(Exception):
    pass


class DayAssignment(object):
    def __init__(self, d: Dict[str, str] = None):
        self.d = d if d else {}

    def __repr__(self):
        return '<DayAssignment({})>'.format(self.d)

    def day(self, show: str) -> str:
        return self.d[show]

    def num_shows(self, day_name):
        """
        Get the number of shows assigned to the day
        :param day_name:
        :return:
        """
        return len([x for x in self.d.values() if x == day_name])

    def add(self, day_name, show_name):
        """
        Assign a day to a show
        Make sure show isn't already assigned to another day
        :param day_name:
        :param show_name:
        :return:
        """
        if show_name in self.d:
            raise DayAssignmentException(
                'show {} is already assigned to day {}, but you are asking me to assign it to {}'.format(
                    show_name, self.d[show_name], day_name
                ))
        self.d[show_name] = day_name