from typing import Dict

from flask import render_template, request, redirect, flash
from sqlalchemy.exc import OperationalError

from sorsched import app, db
from sorsched.canned_inputs import seed
from sorsched.forms import ShowForm, AssignmentForm, OverviewForm, InstrumentMinMaxForm, \
    StudentForm, InstrumentIndicatorForm, SlotAvailabilityForm, ShowPreferenceForm
from sorsched.input_config import ConfigImp
from sorsched.models import Show, Slot, Student, ShowPreference, Instrument, ShowInstrument, SlotAvailable, \
    StudentInstrument, StudentShowAssignment, ShowSlotAssignment
from sorsched.nav import NAV_ITEMS
from sorsched.solver2 import solve


def start_over():
    """
    Wipe out database of everything
    :return:
    """
    db.drop_all()
    db.create_all()


@app.route('/', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
def index():
    form = OverviewForm()
    if form.validate_on_submit():
        if form.start_over.data:
            start_over()
        elif form.seed.data:
            seed(session=db.session)
            db.session.commit()
        elif form.run.data:
            run_optimization(session=db.session)
            db.session.commit()
            return redirect('/assignments')

    create_tables_if_not_exist()

    shows = list(db.session.query(Show).all())
    slots = list(db.session.query(Slot).all())
    students = list(db.session.query(Student).all())
    preferences = get_preferred_shows()
    assigned_students = dict([(show.name, len(show.student_assignments))for show in shows])
    return render_template(
        'index.html', shows=shows, slots=slots, students=students, preferences=preferences,
        assigned_students=assigned_students, navitems=NAV_ITEMS, active_navitem="home", form=form)


def create_tables_if_not_exist():
    try:
        db.session.query(Show).first()
    except OperationalError:
        start_over()


def get_preferred_shows():
    preferences = {}
    for x in db.session.query(ShowPreference).all():
        if x.student_name not in preferences:
            preferences[x.student_name] = x
        if preferences[x.student_name].preference < x.preference:
            preferences[x.student_name] = x
    return preferences


@app.route('/edit_show', methods=['GET', 'POST'])
def edit_show():
    form = ShowForm()
    if form.validate_on_submit():
        edit_show_from_form(form)
        return redirect('/')
    name = request.args.get('name')
    fill_show_form(form=form, show_name=name)
    return render_template('edit_show.html', form=form, navitems=NAV_ITEMS, active_navitem="shows")


def fill_show_form(form, show_name):
    show = db.session.query(Show).filter(Show.name == show_name).first()
    assert show, 'show {} does not exist'.format(show_name)
    form.name.data = show.name
    form.min_students.data = show.min_students
    form.max_students.data = show.max_students
    for instrument, min_max in db.session.query(Instrument, ShowInstrument).outerjoin(ShowInstrument).filter(
                    ShowInstrument.show_name == show.name).all():
        iform = InstrumentMinMaxForm()
        iform.instrument_name = instrument.name
        if min_max:
            iform.min_instruments = min_max.min_instruments
            iform.max_instruments = min_max.max_instruments
        form.instrument_min_max.append_entry(iform)


def edit_show_from_form(form):
    show = db.session.query(Show).filter(Show.name == form.name.data).first()
    if form.delete_show.data:
        delete_show(show_name=show.name,session=db.session)
    else:
        show.min_students = int(form.min_students.data)
        show.max_students = int(form.max_students.data)
        for iform in form.instrument_min_max.entries:
            show_instrument = db.session.query(ShowInstrument).filter(ShowInstrument.show_name == show.name).filter(
                ShowInstrument.instrument_name == iform.data['instrument_name']
            ).first()
            show_instrument.min_instruments = int(iform.data['min_instruments'])
            show_instrument.max_instruments = int(iform.data['max_instruments'])
    db.session.commit()


def delete_show(show_name,session):
    session.query(ShowPreference).filter(ShowPreference.show_name==show_name).delete()
    session.query(StudentShowAssignment).filter(ShowPreference.show_name==show_name).delete()
    session.query(Show).filter(Show.name==show_name).delete()


@app.route('/add_show', methods=['GET', 'POST'])
def add_show():
    form = ShowForm()
    if form.validate_on_submit():
        show_name = form.name.data
        show = Show(
            name=show_name,
            min_students=int(form.min_students.data),
            max_students=int(form.max_students.data)
        )
        db.session.add(show)
        for iform in form.instrument_min_max.entries:
            show_instrument = ShowInstrument(
                show_name=show.name,
                instrument_name=iform.data['instrument_name'],
                min_instruments=int(iform.data['min_instruments']),
                max_instruments=int(iform.data['max_instruments'])
            )
            db.session.add(show_instrument)

        for student in db.session.query(Student).all():
            db.session.add(ShowPreference(student_name=student.name,show_name=show_name,preference=0.0))

        db.session.commit()
        return redirect('/')
    build_show_form(form)
    return render_template('edit_show.html', form=form, navitems=NAV_ITEMS, active_navitem="shows")


def update_student(session, form: StudentForm):
    """
    Edit the student from the content of the form
    :param session:
    :param form:
    :return:
    """
    # Student
    student_name = form.name.data
    student = session.query(Student).filter(Student.name == student_name).first()
    assert student is not None, 'Student {} not found'.format(student_name)

    # Instruments
    session.query(StudentInstrument).filter(StudentInstrument.student_name == student_name).delete()
    for f in form.instruments.entries:
        student_plays = f.data['student_plays']
        if not student_plays:
            continue
        instrument_name = f.data['instrument_name']
        session.add(StudentInstrument(student_name=student_name, instrument_name=instrument_name))

    # Slots
    session.query(SlotAvailable).filter(SlotAvailable.student_name == student_name).delete()
    for f in form.slot_availabilities.entries:
        student_is_available = f.data['student_is_available']
        if not student_is_available:
            continue
        slot_name = f.data['slot_name']
        session.add(SlotAvailable(student_name=student_name, slot_name=slot_name))

    # Shows
    session.query(ShowPreference).filter(ShowPreference.student_name == student_name).delete()
    for f in form.show_preferences.entries:
        show_name = f.data['show_name']
        preference = float(f.data['preference'])
        session.add(ShowPreference(student_name=student_name, show_name=show_name, preference=preference))


def get_student_instruments(session, student_name) -> Dict[str, bool]:
    """
    Get the list of instruments a student plays, but also list the ones she doesn't play
    :param session:
    :param student_name:
    :return:
    """
    stmt = session.query(StudentInstrument).filter(StudentInstrument.student_name == student_name).subquery()
    query = session.query(Instrument.name.label('instrument_name'), stmt.c.student_name).outerjoin(stmt,
                                                                                                   stmt.c.instrument_name == Instrument.name)
    return dict([(x.instrument_name, x.student_name is not None) for x in query.all()])


def get_student_slot_availabilities(session, student_name) -> Dict[str, bool]:
    """
    Get the list of slots, and for each one whether the student is available
    :param session:
    :param student_name:
    :return:
    """
    stmt = session.query(SlotAvailable).filter(SlotAvailable.student_name == student_name).subquery()
    query = session.query(Slot.name.label('slot_name'), stmt.c.student_name).outerjoin(stmt,
                                                                                       stmt.c.slot_name == Slot.name)
    return dict([(x.slot_name, x.student_name is not None) for x in query.all()])


def get_student_show_preferences(session, student_name) -> Dict[str, float]:
    """
    Get the show preferences for the student. Put zero if not found
    :param session:
    :param student_name:
    :return:
    """
    stmt = session.query(ShowPreference).filter(ShowPreference.student_name == student_name).subquery()
    query = session.query(Show.name.label('show_name'), stmt.c.preference).outerjoin(stmt,
                                                                                     stmt.c.show_name == Show.name)
    return dict([(x.show_name, x.preference if x.preference is not None else 0.0) for x in query.all()])


def fill_student_form(form: StudentForm, session):
    """
    Fill the form according to what's in the database
    :param session:
    :param form:
    :return:
    """
    student_name = form.name.data
    instruments = get_student_instruments(session=session, student_name=student_name)
    for instrument_name, student_plays in instruments.items():
        f = InstrumentIndicatorForm()
        f.instrument_name = instrument_name
        f.student_plays = student_plays
        form.instruments.append_entry(f)

    slot_availabilities = get_student_slot_availabilities(session=session, student_name=student_name)
    for slot_name, student_is_available in slot_availabilities.items():
        f = SlotAvailabilityForm()
        f.slot_name = slot_name
        f.student_is_available = student_is_available
        form.slot_availabilities.append_entry(f)

    show_preferences = get_student_show_preferences(session=session, student_name=student_name)
    for show_name, preference in show_preferences.items():
        f = ShowPreferenceForm()
        f.show_name = show_name
        f.preference = preference
        form.show_preferences.append_entry(f)


def delete_student(student_name, session):
    session.query(SlotAvailable).filter(SlotAvailable.student_name==student_name).delete()
    session.query(StudentInstrument).filter(StudentInstrument.student_name==student_name).delete()
    session.query(ShowPreference).filter(ShowPreference.student_name==student_name).delete()
    session.query(Student).filter(Student.name == student_name).delete()



@app.route('/edit_student', methods=['POST', 'GET'])
def edit_student():
    form = StudentForm()
    if form.validate_on_submit():
        if form.delete_student.data:
            delete_student(student_name=form.name.data, session=db.session)
        else:
            update_student(session=db.session, form=form)
        db.session.commit()
        return redirect('/')
    else:
        # noinspection PyTypeChecker
        flash_errors(form)

    form.name.data = request.args.get('name')
    fill_student_form(form=form, session=db.session)
    return render_template('edit_student.html', form=form, navitems=NAV_ITEMS, active_navitem="students")


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error

            ))


def save_student_form(form: StudentForm, session):
    student_name = form.name.data
    student = Student(name=student_name)

    instruments = []
    for f in form.instruments.entries:
        if f.data['student_plays']:
            instrument_name = f.data['instrument_name']
            instruments.append(StudentInstrument(student_name=student_name, instrument_name=instrument_name))

    show_preferences = []
    for f in form.show_preferences.entries:
        show_name = f.data['show_name']
        preference = float(f.data['preference'])
        show_preferences.append(ShowPreference(show_name=show_name, student_name=student_name, preference=preference))

    slot_availabilities = []
    for f in form.slot_availabilities.entries:
        if f.data['student_is_available']:
            slot_name = f.data['slot_name']
            slot_availabilities.append(SlotAvailable(student_name=student_name, slot_name=slot_name))

    session.add(student)
    session.add_all(instruments)
    session.add_all(show_preferences)
    session.add_all(slot_availabilities)


@app.route('/add_student', methods=['POST', 'GET'])
def add_student():
    form = StudentForm()
    if form.validate_on_submit():
        if form.save_student.data:
            save_student_form(form=form, session=db.session)
            db.session.commit()
            return redirect('/')
    else:
        # noinspection PyTypeChecker
        flash_errors(form)

    fill_student_form(form=form, session=db.session)
    return render_template('edit_student.html', form=form, navitems=NAV_ITEMS, active_navitem="students")


def build_show_form(form: ShowForm):
    for instrument in db.session.query(Instrument).all():
        iform = InstrumentMinMaxForm()
        iform.instrument_name = instrument.name
        iform.min_instruments = ""
        iform.max_instruments = ""
        form.instrument_min_max.append_entry(iform)


class Assignment(object):
    """
    Data object to pass to template
    """

    def __init__(self, student_name, show_name, slot_name):
        self.student_name = student_name
        self.show_name = show_name
        self.slot_name = slot_name


def run_optimization(session):
    """
    Solve for optimal assignments!
    :return:
    """
    # flash("here is where we solve for optimal solution, but now it's unimplemented")
    conf = ConfigImp.load_from_db(session=session)
    slot_assignment, optimal_solution = solve(conf)

    # save show-slot assignments
    session.query(ShowSlotAssignment).delete()
    for show_name, slot_name in slot_assignment.show_slots().items():
        session.add(ShowSlotAssignment(show_name=show_name,slot_name=slot_name))

    # save student-show assignments
    session.query(StudentShowAssignment).delete()
    for student_name, show_name in optimal_solution.student_show_assignment().items():
        session.add(StudentShowAssignment(student_name=student_name,show_name=show_name))


@app.route('/assignments', methods=['POST', 'GET'])
def assignments():
    form = AssignmentForm()
    if form.validate_on_submit():
        run_optimization(session=db.session)
        db.session.commit()

    asses = []
    slot_ass = dict([(x.show_name,x.slot_name) for x in db.session.query(ShowSlotAssignment).all()])
    for show_ass in db.session.query(StudentShowAssignment).all():
        asses.append(Assignment(student_name=show_ass.student_name, show_name=show_ass.show_name, slot_name=slot_ass[show_ass.show_name]))
    return render_template('assignments.html', assignments=asses, form=form, navitems=NAV_ITEMS,
                           active_navitem="assignments")
