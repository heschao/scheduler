from enum import Enum

import numpy as np
import tempfile
from itertools import product
from typing import List, Tuple, Dict

from pulp import LpVariable, LpInteger, LpProblem, LpMinimize, lpSum, LpStatus, value


class Instrument(Enum):
    Guitar = 'guitar'
    Vocals = 'vocals'
    Drums = 'drums'


class Student(object):
    def __init__(self, show_preferences: Dict[str, float] = None, name=None, instruments=Tuple[Instrument]):
        self._show_preferences = show_preferences
        self.name = name
        self.instruments = instruments

    def __repr__(self):
        return "<Student: {name}, instruments {instruments}, preferences {preferences}>".format(
            name=self.name,instruments=self.instruments,preferences=self._show_preferences
        )

    def show_preferences(self, show_name):
        return self._show_preferences[show_name]


class Show(object):
    def __init__(self, name=None, student_min_max: Tuple[int, int] = None,
                 instrument_min_max: Dict[Instrument, Tuple[int, int]] = None):
        self.name = name
        self.student_min_max = student_min_max
        self._instrument_min_max = instrument_min_max

    def __repr__(self):
        instrument_min_max = ''
        for instrument,min_max in self._instrument_min_max.items():
            instrument_min_max += ' {instrument}:{themin}-{themax}'.format(
                instrument=instrument,themin=min_max[0],themax=min_max[1]
            )
        return "<Show: {name}, students: {smin}-{smax}, instruments: {instrument_min_max}>".format(
            name=self.name,smin=self.student_min_max[0],smax=self.student_min_max[1],
            instrument_min_max = instrument_min_max
        )

    def instrument_min_max(self,instrument):
        if instrument in self._instrument_min_max:
            return self._instrument_min_max[instrument]
        else:
            return 0, 0


class FixedDayInput(object):
    def __init__(self, shows=List[Show], students=List[Student], is_available:np.ndarray=None):
        self._shows = shows
        self._students = students
        self._utility = self.create_utility_matrix(students=students, shows=shows)
        self._is_available=is_available

    def students(self) -> List[Student]:
        return self._students

    def shows(self) -> List[Show]:
        return self._shows

    def utility(self, student_index, show_index):
        return self._utility[student_index, show_index]

    def create_utility_matrix(self, students: List[Student], shows: List[Show]) -> np.ndarray:
        n_students = len(students)
        n_shows = len(shows)
        x = np.zeros((n_students, n_shows))
        for i in range(n_students):
            for j in range(n_shows):
                x[i, j] = students[i].show_preferences(show_name=shows[j].name)
        return x

    def is_available(self, student_index, show_index) -> bool:
        """
        Returns whether a student is available for a show
        :param student_index:
        :param show_index:
        :return:
        """
        return self._is_available[student_index,show_index]

    def student(self, student_index):
        return self._students[student_index]

    def show(self, show_index):
        return self._shows[show_index]


class FixedDaySolution(object):
    def __init__(self, utility: float = None, student_show_assignments: Dict[str, str] = None):
        self.utility = utility
        self.student_show_assignments = student_show_assignments

    def assigned_show_name(self, student_name: str) -> str:
        return self.student_show_assignments[student_name]


def solve_fixed_day(conf: FixedDayInput) -> FixedDaySolution:
    """
    Optimizes over student->show assignments given student-show preference scores
    :param conf:
    :return:
    """
    n_students = len(conf.students())
    student_indexs = np.arange(n_students)
    n_shows = len(conf.shows())
    show_indexes = np.arange(n_shows)

    possible_assignments = [x for x in product(*[student_indexs, show_indexes])]
    x = LpVariable.dicts("Assignment", possible_assignments, 0, 1, LpInteger)
    prob = LpProblem("Show Assignment Problem", LpMinimize)
    # objective -- maximize utility
    prob += sum([-conf.utility(student_index=i, show_index=j) * x[(i, j)] for i, j in possible_assignments])
    # constraint -- each student can have only one show
    for student_index in student_indexs:
        hits = [x[(student_index, show_index)] for show_index in show_indexes]
        prob += lpSum(hits) == 1, ""

    # constraint -- min max for each instrument
    for show_index in show_indexes:
        show = conf.shows()[show_index]
        is_in_show = [x[(student_index, show_index)] for student_index in student_indexs]
        min_students, max_students = show.student_min_max
        prob += lpSum(is_in_show) >= min_students
        prob += lpSum(is_in_show) <= max_students
        for instrument in Instrument:
            min_students, max_students = show.instrument_min_max(instrument)
            is_in_show_and_instrument = [x[(student_index, show_index)] for student_index in student_indexs if
                                         instrument in conf.students()[student_index].instruments]
            prob += lpSum(is_in_show_and_instrument) >= min_students
            prob += lpSum(is_in_show_and_instrument) <= max_students

    # constraint -- restricted shows
    for show_index in show_indexes:
        is_not_available = [x[(student_index, show_index)] * (
        1 - int(conf.is_available(student_index=student_index, show_index=show_index))) for student_index in
                            student_indexs]
        prob += lpSum(is_not_available) == 0, ""

    # The problem data is written to an .lp file
    with tempfile.NamedTemporaryFile() as f:
        prob.writeLP(f.name)
        prob.solve()
        print("Status:", LpStatus[prob.status])

    import pdb;pdb.set_trace()

    student_show_assignments = dict(
        [(conf.student(student_index).name, conf.show(show_index).name) for student_index, show_index in possible_assignments
         if x[(student_index, show_index)].value() == 1])
    # import pdb;pdb.set_trace()
    return FixedDaySolution(utility=-value(prob.objective), student_show_assignments=student_show_assignments)


def test_solve_fixed_day_instruments():
    shows = [
        Show(
            name='Metallica',
            instrument_min_max={
                Instrument.Guitar: (1, 1),
                Instrument.Drums: (1, 1),
            },
            student_min_max=(0,5)),
        Show(
            name='Lady Gaga',
            instrument_min_max={
                Instrument.Vocals: (1, 1),
            }
            ,student_min_max=(0,5))
    ]
    students = [
        Student(
            name='Ramona',
            instruments=(Instrument.Vocals,),
            show_preferences={'Metallica': 0, 'Lady Gaga': 10, }
        ),
        Student(
            name='Jennifer',
            instruments=(Instrument.Drums,),
            show_preferences={'Metallica': 0, 'Lady Gaga': 0, }
        ),
        Student(
            name='Chao',
            instruments=(Instrument.Guitar,),
            show_preferences={'Metallica': 0, 'Lady Gaga': 0, }
        ),
    ]
    fixed_day_input = FixedDayInput(shows=shows, students=students, is_available=np.ones((3,2)).astype(bool))
    result = solve_fixed_day(fixed_day_input)
    import pdb;pdb.set_trace()
    assert result.assigned_show_name(student_name='Ramona') == 'Lady Gaga'
    assert result.assigned_show_name(student_name='Jennifer') == 'Metallica'
    assert result.assigned_show_name(student_name='Chao') == 'Metallica'
