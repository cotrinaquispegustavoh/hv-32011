from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.file_validation import UploadValidationError, validate_evidence_upload
from apps.academics.infrastructure.models import Student
from apps.discipline.infrastructure.models import Incident
from apps.discipline.student_access import accessible_students


class IncidentReportForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.none())
    additional_students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.none(),
        required=False,
    )
    occurred_at = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local'},
        ),
    )
    location = forms.ChoiceField(choices=Incident.LOCATION_CHOICES)
    other_location = forms.CharField(max_length=120, required=False)
    category = forms.ChoiceField(choices=Incident.CATEGORY_CHOICES)
    subtype = forms.ChoiceField(choices=Incident.SUBTYPE_CHOICES)
    severity = forms.ChoiceField(choices=Incident.SEVERITY_CHOICES)
    description = forms.CharField()
    additional_people = forms.CharField(required=False)
    immediate_action = forms.CharField()
    requires_follow_up = forms.TypedChoiceField(
        choices=(('false', 'No'), ('true', 'Sí')),
        coerce=lambda value: value == 'true',
    )
    referred_to = forms.ChoiceField(
        choices=(('', 'Seleccionar área'), *Incident.REFERRAL_CHOICES),
        required=False,
    )
    additional_observations = forms.CharField(required=False)
    evidence = forms.FileField(required=False)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        students = accessible_students(user)
        self.fields['student'].queryset = students
        self.fields['additional_students'].queryset = students
        self.fields['location'].choices = (('', 'Seleccionar lugar'), *Incident.LOCATION_CHOICES)
        self.fields['category'].choices = (('', 'Seleccionar categoría'), *Incident.CATEGORY_CHOICES)
        self.fields['subtype'].choices = (('', 'Seleccionar subtipo'), *Incident.SUBTYPE_CHOICES)
        self.fields['severity'].choices = (('', 'Seleccionar gravedad'), *Incident.SEVERITY_CHOICES)
        control_class = (
            'block w-full px-4 py-3 bg-slate-50 border border-slate-200 '
            'rounded-xl text-sm font-semibold text-slate-900 focus:outline-none '
            'focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500'
        )
        for name in (
            'occurred_at', 'location', 'other_location', 'category', 'subtype',
            'severity', 'referred_to',
        ):
            self.fields[name].widget.attrs['class'] = control_class
        for name in (
            'description', 'additional_people', 'immediate_action',
            'additional_observations',
        ):
            self.fields[name].widget = forms.Textarea(attrs={
                'class': control_class,
                'rows': 3,
            })
        self.fields['description'].widget.attrs['placeholder'] = (
            'Describa brevemente qué ocurrió, dónde ocurrió y quiénes estuvieron involucrados.'
        )
        self.fields['immediate_action'].widget.attrs['placeholder'] = (
            'Ej.: Se dialogó con el estudiante y se informó al tutor.'
        )
        self.fields['evidence'].widget.attrs.update({
            'class': (
                'block w-full text-sm text-slate-500 file:mr-4 file:py-2.5 '
                'file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold '
                'file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100 border '
                'border-slate-200 rounded-xl bg-slate-50'
            ),
            'accept': '.pdf,.jpg,.jpeg,.png',
        })
        if not self.is_bound:
            self.initial['occurred_at'] = timezone.localtime().replace(
                second=0,
                microsecond=0,
            )
            self.initial['requires_follow_up'] = False

    def clean_occurred_at(self):
        occurred_at = self.cleaned_data['occurred_at']
        if occurred_at > timezone.now() + timedelta(minutes=5):
            raise ValidationError('La fecha de la incidencia no puede estar en el futuro.')
        return occurred_at

    def clean_evidence(self):
        evidence = self.cleaned_data.get('evidence')
        if not evidence:
            return None
        try:
            validate_evidence_upload(evidence)
        except UploadValidationError as exc:
            raise ValidationError(str(exc)) from exc
        return evidence

    def clean(self):
        cleaned = super().clean()
        category = cleaned.get('category')
        subtype = cleaned.get('subtype')
        valid_subtypes = {
            value for value, _label in Incident.CATEGORY_SUBTYPES.get(category, [])
        }
        if subtype and subtype not in valid_subtypes:
            self.add_error('subtype', 'El subtipo no corresponde a la categoría seleccionada.')

        location = cleaned.get('location')
        other_location = (cleaned.get('other_location') or '').strip()
        if location == 'OTRO' and not other_location:
            self.add_error('other_location', 'Especifica el lugar de la incidencia.')
        elif location != 'OTRO':
            cleaned['other_location'] = ''

        if cleaned.get('requires_follow_up'):
            if not cleaned.get('referred_to'):
                self.add_error('referred_to', 'Selecciona el área a la que se derivará.')
        else:
            cleaned['referred_to'] = ''

        student = cleaned.get('student')
        additional_students = cleaned.get('additional_students')
        if student and additional_students and student in additional_students:
            self.add_error(
                'additional_students',
                'El estudiante principal no debe repetirse como participante adicional.',
            )
        return cleaned
