from django import forms
from .models import Documento

class SubirDocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ("archivo",)  # MVP: solo archivo. Luego añadimos captura manual opcional.
        widgets = {
            "archivo": forms.ClearableFileInput(attrs={"accept": ".pdf,.png,.jpg,.jpeg"})
        }
