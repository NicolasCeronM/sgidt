from django import forms
from django.forms import inlineformset_factory
from .models import Proveedor, ProveedorContacto
from .utils import clean_rut, is_valid_rut

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = (
            'razon_social','rut','giro','email','telefono',
            'direccion','comuna','region','categoria','activo'
        )

    def clean_rut(self):
        val = clean_rut(self.cleaned_data.get('rut', ''))
        if not is_valid_rut(val):
            raise forms.ValidationError("RUT inválido.")
        return val

class ProveedorContactoForm(forms.ModelForm):
    class Meta:
        model = ProveedorContacto
        fields = ('nombre','email','telefono','cargo','nota')

# Inline formset (1 extra, opcional, puedes subir a extra=3 si quieres)
ProveedorContactoFormSet = inlineformset_factory(
    Proveedor,
    ProveedorContacto,
    form=ProveedorContactoForm,
    extra=1,
    can_delete=True
)
