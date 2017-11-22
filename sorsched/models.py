from uuid import uuid4

from sorsched import db


def uuid4str():
    return str(uuid4())


class Slot(db.Model):
    name = db.Column(db.String(80), primary_key=True)
    max_shows = db.Column(db.Integer, default=0)

    def __init__(self, name, max_shows):
        self.name = name
        self.max_shows = max_shows

    def __repr__(self):
        return "<Slot: {} {} concurrent rehearsals>".format(self.name,self.max_shows)


class Show(db.Model):
    __tablename__ = 'show'
    name = db.Column(db.String(80), primary_key=True)
    min_students = db.Column(db.Integer)
    max_students = db.Column(db.Integer)
    instrument_min_max = db.relation('ShowInstrument')
    student_assignments = db.relation('StudentShowAssignment')
    slot_assignments = db.relation('ShowSlotAssignment')

    def __repr__(self):
        return '<Show(name={name}, {min_students}-{max_students} students, slot={slot_name})>'.format(
            name=self.name, min_students=self.min_students, max_students=self.max_students,
            slot_name=self.slot_name if self.slot_name else 'unassigned'
        )

    def __init__(self, name,
                 min_students, max_students,
                 ):
        self.name = name
        self.min_students = min_students
        self.max_students = max_students


class ShowInstrument(db.Model):
    __tablename__ = 'show_instrument'
    show_name = db.Column(db.String(80),db.ForeignKey("show.name"),primary_key=True)
    instrument_name = db.Column(db.String(80), db.ForeignKey("instrument.name"), primary_key=True)
    min_instruments = db.Column(db.Integer, nullable=False)
    max_instruments = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<ShowInstrument: {show_name}, {instrument}: min_instrument-max_instrument>".format(
            show_name=self.show_name,instrument=self.instrument_name,
            min_instrument=self.min_instruments,
            max_instrument=self.max_instruments,
        )

    def __init__(self, show_name, instrument_name, min_instruments, max_instruments):
        self.show_name=show_name
        self.instrument_name=instrument_name
        self.min_instruments=min_instruments
        self.max_instruments=max_instruments



class Student(db.Model):
    name = db.Column(db.String(80), primary_key=True)
    show_preferences = db.relationship('ShowPreference', cascade="delete")
    instruments = db.relationship('StudentInstrument')
    available_slots = db.relationship('SlotAvailable')

    def __repr__(self):
        return '<Student({name}; {preferences})>'.format(name=self.name, preferences=self.show_preferences)

    def __init__(self, name):
        self.name = name


class Instrument(db.Model):
    name = db.Column(db.String(80), primary_key=True)

    def __init__(self, name=None):
        self.name=name

    def __repr__(self):
        return "<Instrument: {}>".format(self.name)


class SlotAvailable(db.Model):
    __tablename__ = "slot_available"
    student_name = db.Column(db.String(80), db.ForeignKey("student.name"), primary_key=True)
    slot_name = db.Column(db.String(80), db.ForeignKey("slot.name"), primary_key=True)

    def __init__(self, student_name, slot_name):
        self.student_name=student_name
        self.slot_name=slot_name

    def __repr__(self):
        return "<SlotAvailable: {} : {}>".format(self.student_name,self.slot_name)



class ShowPreference(db.Model):
    student_name = db.Column(db.String(80), db.ForeignKey("student.name"), primary_key=True)
    show_name = db.Column(db.String(80), db.ForeignKey("show.name"), primary_key=True)
    preference = db.Column(db.Float, default=0)

    def __repr__(self):
        return '<ShowPreference({student_name}-{show_name}:{preference})>'.format(
            student_name=self.student_name,
            show_name=self.show_name,
            preference=self.preference
        )

    def __init__(self, student_name, show_name, preference):
        self.student_name = student_name
        self.show_name = show_name
        self.preference = preference


class StudentInstrument(db.Model):
    student_name = db.Column(db.String(80), db.ForeignKey("student.name"), primary_key=True)
    instrument_name = db.Column(db.String(80), db.ForeignKey("instrument.name"), primary_key=True)

    def __init__(self, student_name=None, instrument_name=None):
        self.student_name = student_name
        self.instrument_name = instrument_name

    def __repr__(self):
        return "<StudentInstrument: {} - {}>".format(self.student_name,self.instrument_name)


class ShowSlotAssignment(db.Model):
    show_name=db.Column(db.String(80),db.ForeignKey("show.name"), primary_key=True)
    slot_name=db.Column(db.String(80),db.ForeignKey("slot.name"), nullable=False)

    def __init__(self,show_name,slot_name):
        self.show_name=show_name
        self.slot_name=slot_name

class StudentShowAssignment(db.Model):
    student_name=db.Column(db.String(80),db.ForeignKey("student.name"), primary_key=True)
    show_name=db.Column(db.String(80),db.ForeignKey("show.name"), nullable=False)

    def __init__(self, student_name, show_name ):
        self.student_name=student_name
        self.show_name=show_name