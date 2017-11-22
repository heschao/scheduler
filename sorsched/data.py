from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Dict, List, Tuple

from sorsched import models


class SlotAssignmentException(Exception):
    pass


class SlotAssignment(object):
    """
    Represents mapping from show to day
    """

    def __init__(self, d: Dict[str, str] = None):
        self.d = d if d else {}

    def __repr__(self):
        return '<DayAssignment({})>'.format(self.d)

    def show_slot(self, show: str) -> str:
        return self.d[show]

    def show_slots(self) -> Dict[str, str]:
        return self.d

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
            raise SlotAssignmentException(
                'show {} is already assigned to day {}, but you are asking me to assign it to {}'.format(
                    show_name, self.d[show_name], day_name
                ))
        self.d[show_name] = day_name


class Instrument(Enum):
    Guitar = 'guitar'
    Vocals = 'vocals'
    Drums = 'drums'
    Bass = 'bass'
    Keys = 'keys'


class Slot(metaclass=ABCMeta):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def max_shows(self) -> int:
        pass


class SlotImp(Slot):
    def __init__(self, model: models.Slot = None):
        self.model = model

    def name(self) -> str:
        return self.model.name

    def max_shows(self) -> int:
        return self.model.max_shows


class Student(metaclass=ABCMeta):
    """
    Represents student data object, with some convenience methods
    """

    @abstractmethod
    def show_preferences(self) -> Dict[str, float]:
        pass

    @abstractmethod
    def available_slots(self) -> List[str]:
        pass

    @abstractmethod
    def instruments(self) -> Tuple[Instrument]:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class StudentImp(Student):
    def show_preferences(self) -> Dict[str, float]:
        return self._show_preferences

    def available_slots(self) -> List[str]:
        return self._available_slots

    def __init__(self, model: models.Student):
        self.model = model
        self._show_preferences = dict([(p.show_name, p.preference) for p in self.model.show_preferences])
        self._available_slots = [s.slot_name for s in self.model.available_slots]

    def name(self) -> str:
        return self.model.name

    def is_available_for_slot(self, slot_name) -> bool:
        pass

    def instruments(self) -> List[Instrument]:
        return [Instrument(x.instrument_name) for x in self.model.instruments]

    def show_preference(self, show_name) -> float:
        pass


class Show(metaclass=ABCMeta):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def student_min_max(self) -> Tuple[int, int]:
        pass

    @abstractmethod
    def instrument_min_max(self) -> dict:
        pass


class ShowImp(Show):
    def __init__(self, model: models.Show):
        self.model = model
        self._instrument_min_max = self.build_instrument_min_max(model)

    def student_min_max(self) -> Tuple[int, int]:
        return self.model.min_students, self.model.max_students

    def name(self) -> str:
        return self.model.name

    def instrument_min_max(self) -> dict:
        return self._instrument_min_max

    @classmethod
    def build_instrument_min_max(cls, model: models.Show):
        x = {}
        for imm in model.instrument_min_max:
            x[imm.instrument_name] = (imm.min_instruments, imm.max_instruments)
        return x


class FixedSlotSolution(metaclass=ABCMeta):
    """
    Represents solution of optimization. Specifies show-slot assignments and student-show assignments
    """

    @abstractmethod
    def utility(self) -> float:
        pass

    @abstractmethod
    def student_show_assignment(self) -> Dict[str, str]:
        pass


class ShowAssignmentsImp(FixedSlotSolution):
    def student_show_assignment(self) -> Dict[str, str]:
        return self._assignments

    def utility(self) -> float:
        return self._utility

    def __init__(self, utility=None, assignments: Dict[str, str] = None):
        self._utility = utility
        self._assignments = assignments

    def __repr__(self):
        return '<ShowAssigmentsImp: utility={:.1f}, assignments={}>'.format(self._utility, self._assignments)


class FixedDayInput(metaclass=ABCMeta):
    """
    Input config for when show are already allocated a slot
    """

    def students(self) -> List[Student]:
        pass

    def shows(self) -> List[Show]:
        pass

    def utility(self, student_index, show_index) -> float:
        pass

    def is_available(self, student_index, show_index) -> bool:
        pass


