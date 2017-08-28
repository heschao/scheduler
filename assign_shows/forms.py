from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired

class ShowForm(FlaskForm):
    name = StringField('name',validators=[DataRequired()])
    min_students = StringField('min_students',validators=[DataRequired()])
    max_students = StringField('max_students',validators=[DataRequired()])
    save_show = SubmitField(label='save')
    delete_show = SubmitField(label='delete')


class PreferenceForm(FlaskForm):
    preference=StringField('preference')
    show_name=HiddenField('show_name')


class StudentForm(FlaskForm):
    name=StringField('name',validators=[DataRequired()])
    preferences=FieldList(FormField(PreferenceForm))
    save_student=SubmitField(label='save')
    delete_student=SubmitField(label='delete')

class AssignmentForm(FlaskForm):
    run = SubmitField(label='run')

class StartOverForm(FlaskForm):
    start_over = SubmitField(label='start over')
    seed = SubmitField(label='seed')
    run = SubmitField(label='run')

