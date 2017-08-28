import copy
import tempfile
import typing
import unittest
from itertools import product
from typing import Dict, Tuple, Iterable

import yaml
from pulp import LpVariable, LpInteger, LpProblem, LpMinimize, lpSum, LpStatus, value

from assign_shows.data import Student, Show, Day, DayAssignment
from assign_shows.input_config import Config, FixedDayConf


class Solution(object):
    def __init__(self, utility: float, solution_vector: Dict[Tuple, LpVariable], config: FixedDayConf = None):
        self.utility = utility
        self.solution_vector = solution_vector
        self.config = config

    def __repr__(self):
        return '<Solution(utility={utility})>\n{optimal_solution}'.format(utility=self.utility,
                                                                          optimal_solution=self.solution_vector)

    def assignments(self) -> typing.List[Tuple]:
        return [pair for pair, var in self.solution_vector.items() if var.value() == 1]

    @classmethod
    def sort(cls, solutions: Iterable):
        return sorted(solutions, key=lambda x: -x.utility)

    def show_slots(self):
        """
        Get a dictionary of show_name -> slot_name assignments
        :return:
        """
        return self.config.show_slots()


class TestSolution(unittest.TestCase):
    def test_sort(self):
        v = {('1',): LpVariable(name='a')}
        solutions = [
            Solution(utility=3, solution_vector=v),
            Solution(utility=2, solution_vector=v),
        ]
        result = Solution.sort(solutions)
        assert result[0].utility == 3, result


def solve_fixed_days(fixed_day_confs: typing.Iterable[FixedDayConf]) -> typing.Iterable[Solution]:
    solutions = []
    for conf in fixed_day_confs:
        solutions.append(solved_fixed_day(conf))
    return iter(Solution.sort(solutions))


def load_yaml(pref_file):
    with open(pref_file, 'r') as f:
        return yaml.load(f)


def get_categories(conf: Config):
    students = conf.students()
    days = conf.days()
    shows = conf.shows()
    return students, days, shows


def lookup_utility(conf: FixedDayConf, a: Tuple[str, str]):
    student, show = a
    return conf.utility(student=student, show=show)


def solved_fixed_day(conf: FixedDayConf) -> Solution:
    students = conf.students()
    shows = conf.shows()

    possible_assignments = [x for x in product(*[students, shows])]
    x = LpVariable.dicts("Assignment", possible_assignments, 0, 1, LpInteger)
    prob = LpProblem("Show Assignment Problem", LpMinimize)
    # objective -- maximize utility
    prob += sum([-lookup_utility(conf, a) * x[a] for a in possible_assignments])
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

    return Solution(utility=-value(prob.objective), solution_vector=x, config=conf)


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


def create_fixed_day_config(conf: Config, day_assignment: DayAssignment):
    students = {}
    for student in conf.students():
        s = copy.deepcopy(student)
        for show in conf.shows().values():
            day = day_assignment.day(show=show.name)
            if day not in student.days():
                s.show_utilities.pop(show.name)
        students[s.name] = s
    return FixedDayConf(shows=conf.shows(), students=students, day_assignment=day_assignment)


def enumerate_day_assignments(days: typing.List[Day], shows: typing.List[Show],
                              initial_assignment: DayAssignment = DayAssignment()) -> typing.Iterable[DayAssignment]:
    """
    Assign days to shows. Obey max shows for each day.
    :param initial_assignment:
    :param days:
    :param shows:
    :return:
    """
    if len(shows) == 0:
        yield initial_assignment
        return
    show = shows[0]
    other_shows = shows[1:] if len(shows) > 1 else []
    for day in days:
        if initial_assignment.num_shows(day_name=day.name) >= day.max_shows:
            continue
        assignment = copy.deepcopy(initial_assignment)
        assignment.add(day_name=day.name, show_name=show.name)
        yield from enumerate_day_assignments(days=days, shows=other_shows, initial_assignment=assignment)


def test_enumerate_day_assignments_1():
    days = [Day('Mon', 3), Day('Wed', 3)]
    shows = [Show('Led', 1, 2), Show('Met', 2, 3), Show('GNR', 1, 1)]
    result = [x for x in enumerate_day_assignments(days, shows)]
    assert len(result) == 8


def test_enumerate_day_assignments_2():
    days = [Day('Mon', 1), Day('Wed', 1)]
    shows = [Show('Led', 1, 2), Show('Met', 2, 3)]
    result = [x for x in enumerate_day_assignments(days, shows)]
    assert len(result) == 2
    assert result[0].day('Led') == 'Mon', result
    assert result[0].day('Met') == 'Wed', result


def get_fixed_day_configs(conf: Config) -> typing.Iterable[FixedDayConf]:
    assignments = enumerate_day_assignments(days=list(conf.days().values()), shows=list(conf.shows().values()))
    for day_assignment in assignments:
        yield create_fixed_day_config(conf=conf, day_assignment=day_assignment)
