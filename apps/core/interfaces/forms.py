from django import forms
from django.utils import timezone

from apps.core.file_validation import UploadValidationError, validate_image_upload
from apps.core.infrastructure.models import InstitutionalAnnouncement, InstitutionalEvent


INPUT_CLASS = (
    'w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm font-medium '
    'focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500'
)


class InstitutionalEventForm(forms.ModelForm):
    EVENT_KIND_CHOICES = [
        ('HOLIDAY', 'Feriado local o asueto'),
        ('ACTIVITY', 'Actividad institucional'),
    ]
    event_kind = forms.ChoiceField(label='Tipo de fecha', choices=EVENT_KIND_CHOICES)
    event_date = forms.DateField(
        label='Fecha',
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(format='%d/%m/%Y', attrs={
            'placeholder': 'DD/MM/AAAA',
            'inputmode': 'numeric',
            'autocomplete': 'off',
        }),
    )

    class Meta:
        model = InstitutionalEvent
        fields = ['title', 'description', 'event_date']
        labels = {
            'title': 'Título',
            'description': 'Descripción',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASS

    def clean_event_date(self):
        event_date = self.cleaned_data['event_date']
        if event_date < timezone.localdate():
            raise forms.ValidationError('La fecha no puede estar en el pasado.')
        return event_date

    def save(self, commit=True):
        event = super().save(commit=False)
        event.is_holiday = self.cleaned_data['event_kind'] == 'HOLIDAY'
        if commit:
            event.save()
        return event


class InstitutionalAnnouncementForm(forms.ModelForm):
    event_date = forms.DateField(
        label='Fecha del evento',
        required=False,
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(format='%d/%m/%Y', attrs={
            'placeholder': 'DD/MM/AAAA (opcional)',
            'inputmode': 'numeric',
            'autocomplete': 'off',
        }),
        help_text='Úsala si el comunicado anuncia una reunión, feria u otra actividad con fecha.',
    )
    valid_until = forms.DateField(
        label='Visible hasta',
        required=False,
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(format='%d/%m/%Y', attrs={
            'placeholder': 'DD/MM/AAAA (opcional)',
            'inputmode': 'numeric',
            'autocomplete': 'off',
        }),
    )

    class Meta:
        model = InstitutionalAnnouncement
        fields = ['title', 'message', 'image', 'audience', 'event_date', 'valid_until']
        labels = {
            'title': 'Título',
            'message': 'Contenido del comunicado',
            'image': 'Imagen adjunta (opcional)',
            'audience': 'Destinatarios',
        }
        widgets = {
            'message': forms.Textarea(attrs={'rows': 6}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASS

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            try:
                validate_image_upload(image)
            except UploadValidationError as exc:
                raise forms.ValidationError(str(exc)) from exc
        return image

    def clean_valid_until(self):
        valid_until = self.cleaned_data.get('valid_until')
        if valid_until and valid_until < timezone.localdate():
            raise forms.ValidationError('La vigencia no puede terminar en el pasado.')
        return valid_until

    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        if event_date and event_date < timezone.localdate():
            raise forms.ValidationError('La fecha del evento no puede estar en el pasado.')
        return event_date
