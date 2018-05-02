from __future__ import unicode_literals
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions
from . import models
import course

class uploadVideoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.layout = Layout(
            Field('name', placeholder='Enter lecture name'),
            Submit('update', 'Update', css_class="btn-success"),
        )

    class Meta:
        model = models.Session
        fields = ['name', 'video']

class courseCreateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.layout = Layout(
            Field('name', placeholder='Enter Course name'),
            Field('exam', placeholder='Enter Exam'),
            Field('cost'),
            Field('duration', placeholder='Enter Course duration in months'),
            Field('published'),
            Submit('update', 'Update', css_class="btn-success"),
        )

    class Meta:
        model = course.models.Course
        fields = ['name', 'exam', 'cost', 'duration', 'published']
