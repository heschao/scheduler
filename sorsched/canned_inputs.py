from dbtest.testdb import TestDb
from sorsched import db, models
from sorsched.data import Instrument
from sorsched.models import Show, Slot, Student, ShowPreference, ShowInstrument, StudentInstrument, SlotAvailable


def seed(session):
    # instruments
    instruments =[]
    for instrument in Instrument:
        instruments.append(models.Instrument(name=instrument.value))

    # shows
    led = Show(name='Led Zeppelin', min_students=1, max_students=2)
    met = Show(name='Metallica', min_students=1, max_students=2)
    shows = [led, met]

    show_instruments = []
    for show in shows:
        for instrument in Instrument:
            show_instruments.append(ShowInstrument(show_name=show.name,instrument_name=instrument.value,min_instruments=0,max_instruments=100))

    wed = Slot(name='Wed', max_shows=1)
    sat1 = Slot(name='Sat-1', max_shows=1)
    sat2 = Slot(name='Sat-2', max_shows=1)
    slots = [wed,sat1,sat2]

    ramona = Student(name='Ramona')
    jennifer = Student(name='Jennifer')
    chao = Student(name='Chao')
    students = [ramona,jennifer,chao]

    show_preferences = [
        ShowPreference(student_name=ramona.name, show_name=led.name, preference=1),
        ShowPreference(student_name=ramona.name, show_name=met.name, preference=3),
        ShowPreference(student_name=jennifer.name, show_name=led.name, preference=4),
        ShowPreference(student_name=jennifer.name, show_name=met.name, preference=0),
        ShowPreference(student_name=chao.name, show_name=led.name, preference=2),
        ShowPreference(student_name=chao.name, show_name=met.name, preference=2)
    ]

    student_instruments = [
        StudentInstrument(student_name=ramona.name, instrument_name=Instrument.Vocals.value),
        StudentInstrument(student_name=jennifer.name, instrument_name=Instrument.Drums.value),
        StudentInstrument(student_name=chao.name, instrument_name=Instrument.Guitar.value)
    ]

    slot_availabilities = []
    for student in students:
        for slot in slots:
            slot_availabilities.append(SlotAvailable(student_name=student.name, slot_name=slot.name))

    session.add_all(instruments + shows + slots + students + show_instruments + show_preferences + student_instruments+ slot_availabilities)


class TestSeed(TestDb):
    @classmethod
    def base(cls):
        return db.Model

    def test_seed(self):
        seed(self.session)
        ct = self.session.query(ShowPreference).filter(ShowPreference.show_name == 'Metallica').count()
        assert ct == 3, list(self.session.query(ShowPreference).all())

        student_name='Ramona'
        stmt = db.session.query(SlotAvailable).filter(SlotAvailable.student_name == student_name).subquery()
        query = db.session.query(Slot.name,stmt.c.slot_name).outerjoin(stmt, stmt.c.slot_name == Slot.name)
        assert query.count()==3, query.statement
