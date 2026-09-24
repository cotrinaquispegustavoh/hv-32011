from django import forms
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm

from apps.users.infrastructure.models import User


INPUT_CLASS = (
    "w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm font-medium "
    "focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
)


class PasswordRecoveryRequestForm(forms.Form):
    dni = forms.RegexField(
        label="DNI o código de usuario",
        regex=r"^\d{8}$",
        max_length=8,
        error_messages={"invalid": "Ingresa un DNI de ocho dígitos."},
        widget=forms.TextInput(attrs={
            "autocomplete": "username",
            "inputmode": "numeric",
            "maxlength": "8",
            "class": INPUT_CLASS,
            "placeholder": "Ej. 45678912",
        }),
    )
    email = forms.EmailField(
        label="Correo registrado",
        widget=forms.EmailInput(attrs={
            "autocomplete": "email",
            "class": INPUT_CLASS,
            "placeholder": "nombre@correo.com",
        }),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class PasswordRecoverySetForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "new_password1": "Nueva contraseña",
            "new_password2": "Confirmar nueva contraseña",
        }
        for name, field in self.fields.items():
            field.label = labels[name]
            field.widget.attrs.update({
                "class": INPUT_CLASS,
                "autocomplete": "new-password",
            })


class AdministrativePasswordResetForm(forms.Form):
    dni = forms.RegexField(
        label="DNI o código de usuario",
        regex=r"^\d{8}$",
        max_length=8,
        error_messages={"invalid": "Ingresa un DNI de ocho dígitos."},
        widget=forms.TextInput(attrs={
            "autocomplete": "off",
            "inputmode": "numeric",
            "maxlength": "8",
            "class": INPUT_CLASS,
            "placeholder": "DNI del docente, personal o apoderado",
        }),
    )


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombres", max_length=150)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    email = forms.EmailField(label="Correo electrónico", required=False)
    birth_date = forms.DateField(
        label="Fecha de nacimiento",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    phone = forms.RegexField(
        label="Teléfono",
        regex=r"^[0-9+()\-\s]{6,20}$",
        required=False,
        error_messages={"invalid": "Ingresa un teléfono válido de entre 6 y 20 caracteres."},
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "birth_date", "phone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS

    def clean_first_name(self):
        value = self.cleaned_data["first_name"].strip()
        if not value:
            raise forms.ValidationError("Los nombres son obligatorios.")
        return value

    def clean_last_name(self):
        value = self.cleaned_data["last_name"].strip()
        if not value:
            raise forms.ValidationError("Los apellidos son obligatorios.")
        return value


class AccountPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            'old_password': 'Contraseña actual',
            'new_password1': 'Nueva contraseña',
            'new_password2': 'Confirmar nueva contraseña',
        }
        autocomplete = {
            'old_password': 'current-password',
            'new_password1': 'new-password',
            'new_password2': 'new-password',
        }
        for name, field in self.fields.items():
            field.label = labels[name]
            field.widget.attrs.update({
                'class': INPUT_CLASS,
                'autocomplete': autocomplete[name],
            })
