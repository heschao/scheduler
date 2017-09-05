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


class Show(db.Model):
    __tablename__ = 'show'
    name = db.Column(db.String(80), primary_key=True)
    min_students = db.Column(db.Integer)
    max_students = db.Column(db.Integer)
    slot_name = db.Column(db.String(80), db.ForeignKey("slot.name"), nullable=True)
    instrument_min_max = db.relation('ShowInstrument')

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
    instrument = db.Column(db.String(80),primary_key=True)
    min_instrument = db.Column(db.Integer,nullable=False)
    max_instrument = db.Column(db.Integer,nullable=False)

    def __repr__(self):
        return "<ShowInstrument: {show_name}, {instrument}: min_instrument-max_instrument>".format(
            show_name=self.show_name,instrument=self.instrument,
            min_instrument=self.min_instrument,
            max_instrument=self.max_instrument,
        )

    def __init__(self,show_name,instrument,min_instrument,max_instrument):
        self.show_name=show_name
        self.instrument=instrument
        self.min_instrument=min_instrument
        self.max_instrument=max_instrument



class Student(db.Model):
    name = db.Column(db.String(80), primary_key=True)
    show_name = db.Column(db.String(80), db.ForeignKey("show.name"), nullable=True)
    show_preferences = db.relationship('ShowPreference', cascade="delete")
    instruments = db.relationship('StudentInstrument')
    available_slots = db.relationship('SlotAvailable')

    def __repr__(self):
        return '<Student({name}; {preferences})>'.format(name=self.name, preferences=self.show_preferences)

    def __init__(self, name):
        self.name = name


class Instrument(db.Model):
    name = db.Column(db.String(80), primary_key=True)


class SlotAvailable(db.Model):
    student_name = db.Column(db.String(80), db.ForeignKey("student.name"), primary_key=True)
    slot_name = db.Column(db.String(80), db.ForeignKey("slot.name", primary_key=True))


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



class ShowSlotAssignment(db.Model):
    show_name=db.Column(db.String(80),db.ForeignKey("show.name"), primary_key=True)
    slot_name=db.Column(db.String(80),db.ForeignKey("slot.name"), nullable=False)

class StudentShowAssignment(db.Model):
    student_name=db.Column(db.String(80),db.ForeignKey("student.name"), primary_key=True)
    show_name=db.Column(db.String(80),db.ForeignKey("show.name"), nullable=False)
