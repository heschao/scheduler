import copy
import typing
from unittest.mock import MagicMock

from sorsched.data import Show, SlotAssignment, Slot


def enumerate_slot_assignments(slots: typing.List[Slot], shows: typing.List[Show],
                               initial_assignment: SlotAssignment = SlotAssignment()) -> typing.Iterable[
    SlotAssignment]:
    """
    Assign days to shows. Obey max shows for each day.
    :param initial_assignment:
    :param slots:
    :param shows:
    :return:
    """
    if len(shows) == 0:
        yield initial_assignment
        return
    show = shows[0]
    other_shows = shows[1:] if len(shows) > 1 else []
    for slot in slots:
        if initial_assignment.num_shows(day_name=slot.name()) >= slot.max_shows():
            continue
        assignment = copy.deepcopy(initial_assignment)
        assignment.add(day_name=slot.name(), show_name=show.name())
        yield from enumerate_slot_assignments(slots=slots, shows=other_shows, initial_assignment=assignment)


def test_enumerate_day_assignments_1():
    Slot.__abstractmethods__ = frozenset()
    mon = Slot()
    mon.name = MagicMock(return_value='Mon')
    mon.max_shows = MagicMock(return_value=3)
    tue = Slot()
    tue.name = MagicMock(return_value='Tue')
    tue.max_shows = MagicMock(return_value=3)
    slots = [mon, tue]

    Show.__abstractmethods__ = frozenset()
    led = Show()
    led.name = MagicMock(return_value='Led')
    met = Show()
    met.name = MagicMock(return_value='Met')
    gnr = Show()
    gnr.name = MagicMock(return_value='GNR')
    shows = [led, met, gnr]

    result = [x for x in enumerate_slot_assignments(slots, shows)]
    assert len(result) == 8


def test_enumerate_day_assignments_2():
    Slot.__abstractmethods__ = frozenset()
    mon = Slot()
    mon.name = MagicMock(return_value='Mon')
    mon.max_shows = MagicMock(return_value=1)
    wed = Slot()
    wed.name = MagicMock(return_value='Wed')
    wed.max_shows = MagicMock(return_value=1)
    slots = [mon, wed]

    Show.__abstractmethods__ = frozenset()
    led = Show()
    led.name = MagicMock(return_value='Led')
    met = Show()
    met.name = MagicMock(return_value='Met')
    shows = [led, met]
    result = [x for x in enumerate_slot_assignments(slots, shows)]
    assert len(result) == 2
    assert result[0].show_slot('Led') == 'Mon', result
    assert result[0].show_slot('Met') == 'Wed', result
