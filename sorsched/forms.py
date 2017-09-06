from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FieldList, FormField, HiddenField, BooleanField
from wtforms.validators import DataRequired


class InstrumentMinMaxForm(FlaskForm):
    """
    Part of the show form -- enter a min and a max for one instrument
    """
    min_instruments = StringField('min')
    max_instruments = StringField('max')
    instrument_name = HiddenField('instrument_name')


class ShowForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    min_students = StringField('min_students', validators=[DataRequired()])
    max_students = StringField('max_students', validators=[DataRequired()])
    instrument_min_max = FieldList(FormField(InstrumentMinMaxForm))
    save_show = SubmitField(label='save')
    delete_show = SubmitField(label='delete')


class InstrumentIndicatorForm(FlaskForm):
    instrument_name = HiddenField('instrument_name')
    student_plays = BooleanField('student_plays')


class ShowPreferenceForm(FlaskForm):
    show_name = HiddenField('show_name')
    preference = StringField('preference', validators=[DataRequired()])


class SlotAvailabilityForm(FlaskForm):
    slot_name = HiddenField('slot_name')
    student_is_available = BooleanField('student_is_available')


class StudentForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    save_student = SubmitField('save')
    delete_student = SubmitField('delete')
    instruments = FieldList(FormField(InstrumentIndicatorForm))
    show_preferences = FieldList(FormField(ShowPreferenceForm))
    slot_availabilities = FieldList(FormField(SlotAvailabilityForm))


class AssignmentForm(FlaskForm):
    run = SubmitField(label='run')


class OverviewForm(FlaskForm):
    start_over = SubmitField(label='start over')
    seed = SubmitField(label='seed')
    run = SubmitField(label='run')
