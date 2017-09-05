from typing import List

from sorsched.data import FixedDayInput, SlotAssignment, Student, Show
from sorsched.input_config import Config


class FixedDayInputImp(FixedDayInput):
    """
    Represents student/show availability. This is a subset of the original config that is consistent with
    students' day availabilities
    """

    def __init__(self, conf: Config, slot_assignment: SlotAssignment):
        self._shows = conf.shows()
        self._students = conf.students()
        self.slot_assignment = slot_assignment

    def students(self) -> List[Student]:
        return self._students

    def shows(self) -> List[Show]:
        return self._shows

    def utility(self, student_index, show_index):
        show_name = self.shows()[show_index].name()
        return self.students()[student_index].show_preferences()[show_name]

    def is_available(self, student_index, show_index) -> bool:
        """
        Returns whether a student is available for a show
        :param student_index:
        :param show_index:
        :return:
        """
        show_name = self.shows()[show_index].name()
        slot_name = self.slot_assignment.show_slot(show=show_name)
        return slot_name in self.students()[student_index].available_slots()