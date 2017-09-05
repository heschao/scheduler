import tempfile
import typing
from itertools import product
from typing import Tuple
from unittest.mock import MagicMock

import numpy as np
from pulp import LpVariable, LpInteger, LpProblem, LpMinimize, lpSum, LpStatus, value

from sorsched.data import SlotAssignment, Instrument, Slot, Student, Show, ShowAssignmentsImp, FixedDayInput, \
    FixedSlotSolution
from sorsched.fixed_day_input import FixedDayInputImp
from sorsched.input_config import Config, ConfigImp
from sorsched.assign_slots_to_shows import enumerate_slot_assignments


def solve_fixed_day(conf: FixedDayInput) -> FixedSlotSolution:
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
    # prob += sum([x[(i, j)] for i, j in possible_assignments])
    # constraint -- each student can have only one show
    for student_index in student_indexs:
        hits = [x[(student_index, show_index)] for show_index in show_indexes]
        prob += lpSum(hits) == 1, ""

    # constraint -- min max for each instrument
    for show_index in show_indexes:
        show = conf.shows()[show_index]
        is_in_show = [x[(student_index, show_index)] for student_index in student_indexs]
        min_students, max_students = show.student_min_max()
        prob += lpSum(is_in_show) >= min_students
        prob += lpSum(is_in_show) <= max_students
        for instrument in Instrument:
            min_students, max_students = show.instrument_min_max()[instrument] if instrument in show.instrument_min_max() else (0,9999)
            is_in_show_and_instrument = [x[(student_index, show_index)] for student_index in student_indexs if
                                         instrument in conf.students()[student_index].instruments()]
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

    student_show_assignments = dict(
        [(conf.students()[student_index].name(), conf.shows()[show_index].name()) for student_index, show_index in
         possible_assignments
         if x[(student_index, show_index)].value() == 1])

    return ShowAssignmentsImp(utility=value(prob.objective), assignments=student_show_assignments)


def test_solve_fixed_day_instruments():
    Show.__abstractmethods__ = frozenset()
    metallica = Show()
    metallica.name = MagicMock(return_value='Metallica')
    metallica.instrument_min_max = MagicMock(return_value={
        Instrument.Guitar: (1, 1),
        Instrument.Drums: (1, 1),
    })
    metallica.student_min_max = MagicMock(return_value=(0, 5))
    gaga = Show()
    gaga.name = MagicMock(return_value='Lady Gaga')
    gaga.instrument_min_max = MagicMock(return_value={Instrument.Vocals: (1, 1)})
    gaga.student_min_max = MagicMock(return_value=(0, 5))
    shows = [metallica, gaga]

    Slot.__abstractmethods__ = frozenset()
    mon = Slot()
    mon.name = MagicMock(return_value='Mon')
    tue = Slot()
    tue.name = MagicMock(return_value='Tue')

    slots = [mon, tue]
    Student.__abstractmethods__ = frozenset()
    ramona = Student()
    ramona.name = MagicMock(return_value='Ramona')
    ramona.instruments = MagicMock(return_value=[Instrument.Vocals])
    ramona.show_preferences = MagicMock(return_value={'Metallica': 0, 'Lady Gaga': 10, })
    ramona.available_slots = MagicMock(return_value=['Mon','Tue'])
    jennifer = Student()
    jennifer.name = MagicMock(return_value='Jennifer')
    jennifer.instruments = MagicMock(return_value=[Instrument.Drums])
    jennifer.show_preferences = MagicMock(return_value={'Metallica': 0, 'Lady Gaga': 0, })
    jennifer.available_slots = MagicMock(return_value=['Mon','Tue'])
    chao = Student()
    chao.name = MagicMock(return_value='Chao')
    chao.instruments = MagicMock(return_value=[Instrument.Guitar])
    chao.show_preferences = MagicMock(return_value={'Metallica': 0, 'Lady Gaga': 0, })
    chao.available_slots = MagicMock(return_value=['Mon','Tue'])

    students = [ramona, jennifer, chao]

    conf = ConfigImp(shows=shows, slots=slots, students=students)
    slot_assignment = SlotAssignment(d={'Metallica': 'Mon', 'Lady Gaga': 'Tue'})

    fixed_day_input = FixedDayInputImp(conf=conf, slot_assignment=slot_assignment)
    result = solve_fixed_day(fixed_day_input)
    assert result.student_show_assignment()['Ramona'] == 'Lady Gaga'
    assert result.student_show_assignment()['Jennifer'] == 'Metallica'
    assert result.student_show_assignment()['Chao'] == 'Metallica'


def test_solve_fixed_day_students():
    Show.__abstractmethods__ = frozenset()
    metallica = Show()
    metallica.name = MagicMock(return_value='Metallica')
    metallica.instrument_min_max = MagicMock(return_value={
        Instrument.Guitar: (0, 100),
    })
    metallica.student_min_max = MagicMock(return_value=(1, 1))
    gaga = Show()
    gaga.name = MagicMock(return_value='Lady Gaga')
    gaga.instrument_min_max = MagicMock(return_value={Instrument.Vocals: (0, 100)})
    gaga.student_min_max = MagicMock(return_value=(2, 2))
    shows = [metallica, gaga]

    Slot.__abstractmethods__ = frozenset()
    mon = Slot()
    mon.name = MagicMock(return_value='Mon')
    tue = Slot()
    tue.name = MagicMock(return_value='Tue')

    slots = [mon, tue]
    Student.__abstractmethods__ = frozenset()
    ramona = Student()
    ramona.name = MagicMock(return_value='Ramona')
    ramona.instruments = MagicMock(return_value=[Instrument.Vocals])
    ramona.show_preferences = MagicMock(return_value={'Metallica': 0, 'Lady Gaga': 2, })
    ramona.available_slots = MagicMock(return_value=['Mon','Tue'])
    jennifer = Student()
    jennifer.name = MagicMock(return_value='Jennifer')
    jennifer.instruments = MagicMock(return_value=[Instrument.Drums])
    jennifer.show_preferences = MagicMock(return_value={'Metallica': 1, 'Lady Gaga': 1, })
    jennifer.available_slots = MagicMock(return_value=['Mon','Tue'])
    chao = Student()
    chao.name = MagicMock(return_value='Chao')
    chao.instruments = MagicMock(return_value=[Instrument.Guitar])
    chao.show_preferences = MagicMock(return_value={'Metallica': 2, 'Lady Gaga': 0, })
    chao.available_slots = MagicMock(return_value=['Mon','Tue'])

    students = [ramona, jennifer, chao]

    conf = ConfigImp(shows=shows, slots=slots, students=students)

    slot_assignment = SlotAssignment(d={'Metallica': 'Mon', 'Lady Gaga': 'Tue'})

    fixed_day_input = FixedDayInputImp(conf=conf, slot_assignment=slot_assignment)
    result = solve_fixed_day(fixed_day_input)
    assert result.student_show_assignment()['Ramona'] == 'Lady Gaga'
    assert result.student_show_assignment()['Jennifer'] == 'Lady Gaga'
    assert result.student_show_assignment()['Chao'] == 'Metallica'


def solve(conf):
    best_solution = ShowAssignmentsImp(utility=-np.inf)
    best_slot_assignments = None
    for slot_assignments, fixed_day_config in get_fixed_day_configs(conf):
        solution = solve_fixed_day(fixed_day_config)
        if solution.utility() > best_solution.utility():
            best_solution = solution
            best_slot_assignments = slot_assignments
    return best_slot_assignments, best_solution


def get_fixed_day_configs(conf: Config) -> typing.Iterable[Tuple[SlotAssignment, FixedDayInput]]:
    possible_show_slot_assignments = enumerate_slot_assignments(slots=conf.slots(), shows=conf.shows())
    for slot_assignments in possible_show_slot_assignments:
        yield slot_assignments, FixedDayInputImp(conf=conf, slot_assignment=slot_assignments)
