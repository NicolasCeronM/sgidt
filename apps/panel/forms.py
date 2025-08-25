from django import forms

class HelpContactForm(forms.Form):
    name = forms.CharField(max_length=120, label="Nombre")
    email = forms.EmailField(label="Email")
    message = forms.CharField(widget=forms.Textarea, max_length=4000, label="Mensaje")
    hp = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_hp(self):
        if self.cleaned_data.get("hp"):
            raise forms.ValidationError("Bot detectado.")
        return ""
