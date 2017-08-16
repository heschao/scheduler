import tempfile
import typing
import unittest
from itertools import product
from typing import Dict, Tuple, Iterable

import click
import copy
import yaml
from pulp import *

DEFAULT_PREF_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'show-preferences.yml')


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


class Config(object):
    def __init__(self, d: dict):
        self.d = d

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

    def days(self):
        return self.d['days']

    def test(self):
        print('students:')
        print(self.students())
        print('shows:')
        print(self.shows())
        print('days:')
        print(self.days())


def load_yaml(pref_file):
    with open(pref_file, 'r') as f:
        return yaml.load(f)


def get_categories(conf: Config):
    students = conf.students()
    days = conf.days()
    shows = conf.shows()
    return students, days, shows


class FixedDayConf(object):
    def __init__(self, shows: Dict[str, Show], students: Dict[str, Student]):
        self._shows = shows
        self._students = students

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


def utility(conf: FixedDayConf, a: Tuple[str, str]):
    student, show = a
    return conf.utility(student=student, show=show)


class Solution(object):
    def __init__(self, utility: float, solution_vector: Dict[Tuple, LpVariable]):
        self.utility = utility
        self.solution_vector = solution_vector

    def __repr__(self):
        return '<Solution(utility={utility})>\n{optimal_solution}'.format(utility=self.utility,
                                                                          optimal_solution=self.solution_vector)

    @classmethod
    def sort(cls, solutions: Iterable):
        return sorted(solutions, key=lambda x: -x.utility)


class TestSolution(unittest.TestCase):
    def test_sort(self):
        v = {('1',): LpVariable(name='a')}
        solutions = [
            Solution(utility=3, solution_vector=v),
            Solution(utility=2, solution_vector=v),
        ]
        result = Solution.sort(solutions)
        assert result[0].utility == 3, result


def solved_fixed_day(conf: FixedDayConf) -> Solution:
    students = conf.students()
    shows = conf.shows()

    possible_assignments = [x for x in product(*[students, shows])]
    x = LpVariable.dicts("Assignment", possible_assignments, 0, 1, LpInteger)
    prob = LpProblem("Show Assignment Problem", LpMinimize)
    # objective -- maximize utility
    prob += sum([-utility(conf, a) * x[a] for a in possible_assignments])
    # constraint -- each student can have only one show
    for student in students:
        hits = [x[(student, show)] for show in shows]
        prob += lpSum(hits) == 1, ""

    # constraint -- show min max students
    for show in shows:
        is_in_show = [x[(student, show)] for student in students]
        prob += lpSum(is_in_show) >= conf.min_students(show)
        prob += lpSum(is_in_show) <= conf.max_students(show)

    # constraint -- restricted shows
    for show in shows:
        is_not_available = [x[(student, show)] * (1 - int(conf.is_available(student=student, show=show))) for student in
                            students]
        prob += lpSum(is_not_available) == 0, ""

    # The problem data is written to an .lp file
    with tempfile.NamedTemporaryFile() as f:
        prob.writeLP(f.name)
        prob.solve()
        print("Status:", LpStatus[prob.status])

    return Solution(utility=-value(prob.objective), solution_vector=x)


def test_solve_fixed_day():
    shows = {
        'LedZeppelin': Show('LedZeppelin', 0, 4),
        'Metallica': Show('Metallica', 1, 5)
    }
    students = {
        'Jennifer': Student(name='Jennifer', show_utilities={
            'LedZeppelin': 3, 'Metallica': 0
        }),
        'Chao': Student(name='Chao', show_utilities={
            'LedZeppelin': 0, 'Metallica': 3
        }),
    }
    conf = FixedDayConf(shows=shows, students=students)
    result = solved_fixed_day(conf)
    assert result.utility == 6, result


def solve_fixed_days(fixed_day_confs: typing.Iterable[FixedDayConf]) -> typing.Iterable[Solution]:
    solutions = []
    for conf in fixed_day_confs:
        solutions.append(solved_fixed_day(conf))
    return Solution.sort(solutions)


class DayAssignment(object):
    def __init__(self, d: Dict[str, str]):
        self.d = d

    def day(self, show: str) -> str:
        return self.d[show]


def create_fixed_day_config(conf: Config, day_assignment: DayAssignment):
    students = {}
    for student in conf.students():
        s = copy.deepcopy(student)
        for show in conf.shows():
            day = day_assignment.day(show=show.name)
            if day not in student.days():
                s.show_utilities.pop(show.name)
        students[s.name] = s
    return FixedDayConf(shows=conf.shows(), students=students)


def enumerage_day_assignments(conf: Config) -> typing.Iterable[DayAssignment]:
    pass


def get_fixed_day_configs(conf: Config) -> typing.Iterable[FixedDayConf]:
    for day_assignment in enumerage_day_assignments(conf=conf):
        yield create_fixed_day_config(conf=conf, day_assignment=day_assignment)


@click.command()
@click.option('--pref-file', '-p', default=DEFAULT_PREF_FILE)
@click.option('--test-config', '-t', is_flag=True)
def main(pref_file, test_config):
    conf = Config(d=load_yaml(pref_file))
    if test_config:
        conf.test()
        return

    solutions = solve_fixed_days(fixed_day_confs=get_fixed_day_configs(conf))
    print('solution')
    print(next(solutions))


if __name__ == "__main__":
    main()
