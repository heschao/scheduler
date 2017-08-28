from flask import render_template, request, redirect, flash
from sqlalchemy.exc import OperationalError

from assign_shows import app, db
from assign_shows.forms import ShowForm, StudentForm, PreferenceForm, AssignmentForm, OverviewForm
from assign_shows.input_config import Config
from assign_shows.models import Show, Slot, Student, ShowPreference
from assign_shows.nav import NAV_ITEMS
from assign_shows.solver import solve_fixed_days, get_fixed_day_configs, Solution


def start_over():
    """
    Wipe out database of everything
    :return:
    """
    db.drop_all()
    db.create_all()

@app.route('/',methods=['POST','GET'])
@app.route('/index',methods=['POST','GET'])
def index():
    form = OverviewForm()
    if form.validate_on_submit():
        if form.start_over.data:
            start_over()
        elif form.seed.data:
            seed()
        elif form.run.data:
            run_optimization()
            return redirect('/assignments')

    create_tables_if_not_exist()

    shows = list(db.session.query(Show).all())
    slots = list(db.session.query(Slot).all())
    students = list(db.session.query(Student).all())
    preferences = get_preferred_shows()
    assigned_students = get_assigned_students(shows, students)
    return render_template(
        'index.html', shows=shows, slots=slots, students=students, preferences=preferences,
        assigned_students=assigned_students,navitems=NAV_ITEMS, active_navitem="home",form=form)


def create_tables_if_not_exist():
    try:
        db.session.query(Show).first()
    except OperationalError:
        start_over()


def get_assigned_students(shows, students):
    assigned_students = dict([(x.name, 0) for x in shows])
    for student in students:
        if student.show_name is not None:
            assigned_students[student.show_name] += 1
    return assigned_students


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


def edit_show_from_form(form):
    show = db.session.query(Show).filter(Show.name == form.name.data).first()
    if form.delete_show.data:
        db.session.delete(show)
    else:
        show.min_students = int(form.min_students.data)
        show.max_students = int(form.max_students.data)
    db.session.commit()


@app.route('/add_show', methods=['GET', 'POST'])
def add_show():
    form = ShowForm()
    if form.validate_on_submit():
        show = Show(
            name=form.name.data,
            min_students=int(form.min_students.data),
            max_students=int(form.max_students.data)
        )
        db.session.add(show)
        db.session.commit()
        return redirect('/')
    return render_template('edit_show.html', form=form, navitems=NAV_ITEMS, active_navitem="shows")


@app.route('/edit_student', methods=['POST', 'GET'])
def edit_student():
    form = StudentForm()
    if form.validate_on_submit():
        edit_student_from_form(form)
        return redirect('/')
    else:
        # noinspection PyTypeChecker
        flash_errors(form)

    name = request.args.get('name')
    fill_student_form(form=form, student_name=name)
    return render_template('edit_student.html', form=form, navitems=NAV_ITEMS, active_navitem="students")


def fill_student_form(form, student_name):
    student = db.session.query(Student).filter(Student.name == student_name).first()
    form.name.data = student.name
    for p in student.show_preferences:
        pform = PreferenceForm()
        pform.show_name = p.show_name
        pform.preference = p.preference
        form.preferences.append_entry(pform)


def edit_student_from_form(form):
    name = form.name.data
    if form.delete_student.data:
        student = db.session.query(Student).filter(Student.name == name).first()
        db.session.delete(student)
    else:
        for p in form.preferences.entries:
            show_preference = db.session.query(ShowPreference).filter(
                (ShowPreference.student_name == name) & (ShowPreference.show_name == p.data['show_name'])
            ).first()
            show_preference.preference = float(p.data['preference'])
    db.session.commit()


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error

            ))


@app.route('/add_student', methods=['POST', 'GET'])
def add_student():
    form = StudentForm()
    if form.validate_on_submit():
        if form.save_student.data:
            add_student_from_form(form)
            return redirect('/')
    else:
        # noinspection PyTypeChecker
        flash_errors(form)

    build_student_form(form)
    return render_template('edit_student.html', form=form, navitems=NAV_ITEMS, active_navitem="students")


def build_student_form(form):
    for show in db.session.query(Show).all():
        pform = PreferenceForm()
        pform.show_name = show.name
        pform.preference = 0
        form.preferences.append_entry(pform)


def add_student_from_form(form):
    student_name = form.name.data
    student = Student(name=student_name)
    db.session.add(student)
    for p in form.preferences.entries:
        show_name = p.data['show_name']
        preference = float(p.data['preference'])
        show_preference = ShowPreference(student_name=student_name, show_name=show_name, preference=preference)
        db.session.add(show_preference)
    db.session.commit()


class Assignment(object):
    """
    Data object to pass to template
    """

    def __init__(self, student_name, show_name, slot_name):
        self.student_name = student_name
        self.show_name = show_name
        self.slot_name = slot_name


def run_optimization():
    """
    Solve for optimal assignments!
    :return:
    """
    # flash("here is where we solve for optimal solution, but now it's unimplemented")
    conf = Config.load_from_db()
    solutions = solve_fixed_days(fixed_day_confs=get_fixed_day_configs(conf))
    optimal_solution = next(solutions) # type: Solution

    # save show-slot assignments
    for show_name,slot_name in optimal_solution.show_slots().items():
        show = db.session.query(Show).filter(Show.name==show_name).first()
        show.slot_name=slot_name

    # save student-show assignments
    for student_name,show_name in optimal_solution.assignments():
        student=db.session.query(Student).filter(Student.name==student_name).first()
        student.show_name=show_name

    db.session.commit()

@app.route('/assignments', methods=['POST', 'GET'])
def assignments():
    form = AssignmentForm()
    if form.validate_on_submit():
        run_optimization()

    asses = []
    for student, show in db.session.query(Student, Show).outerjoin(Show).all():
        if show:
            show_name = show.name
            slot_name = show.slot_name
        else:
            show_name = "unassigned"
            slot_name = "unassigned"

        asses.append(Assignment(student_name=student.name, show_name=show_name, slot_name=slot_name))
    return render_template('assignments.html', assignments=asses, form=form, navitems=NAV_ITEMS,
                           active_navitem="assignments")


def seed():
    start_over()
    db.session.add(Show(name='Led Zeppelin', min_students=1, max_students=2))
    db.session.add(Show(name='Metallica', min_students=1, max_students=2))
    db.session.add(Slot(name='Wed', max_shows=1))
    db.session.add(Slot(name='Sat-1', max_shows=1))
    db.session.add(Slot(name='Sat-2', max_shows=1))
    db.session.add(Student(name='Ramona'))
    db.session.add(Student(name='Jennifer'))
    db.session.add(Student(name='Chao'))
    db.session.add(ShowPreference(student_name='Ramona', show_name='Led Zeppelin', preference=1))
    db.session.add(ShowPreference(student_name='Ramona', show_name='Metallica', preference=3))
    db.session.add(ShowPreference(student_name='Jennifer', show_name='Led Zeppelin', preference=4))
    db.session.add(ShowPreference(student_name='Jennifer', show_name='Metallica', preference=0))
    db.session.add(ShowPreference(student_name='Chao', show_name='Led Zeppelin', preference=2))
    db.session.add(ShowPreference(student_name='Chao', show_name='Metallica', preference=2))
    db.session.commit()