from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from .models import Profile

import re
from PIL import Image

Usuario = get_user_model()

# ===========================
#  Utilidades de validación
# ===========================

HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{6})$")

def normalize_phone(value: str) -> str:
    """Permite +, espacios y guiones pero valida que existan 8-15 dígitos."""
    if not value:
        return value
    digits = re.sub(r"\D", "", value)  # solo dígitos
    if not (8 <= len(digits) <= 15):
        raise ValidationError("El teléfono debe tener entre 8 y 15 dígitos.")
    # Devuelve en formato limpio (solo dígitos) para guardar homogéneo
    return digits

def clean_hex_color(value: str) -> str:
    if not value:
        return value
    if not HEX_COLOR_RE.match(value):
        raise ValidationError("Usa un color hexadecimal válido (ej: #E2261C).")
    return value.upper()

def rut_clean(rut: str) -> str:
    """Limpia puntos/guiones y retorna en formato XX...X-DV (sin puntos, con guion)."""
    if not rut:
        return rut
    s = rut.replace(".", "").replace(" ", "").upper()
    if "-" in s:
        cuerpo, dv = s.split("-", 1)
    else:
        cuerpo, dv = s[:-1], s[-1]
    return f"{cuerpo}-{dv}"

def rut_is_valid(rut: str) -> bool:
    """Valida dígito verificador chileno (módulo 11)."""
    if not rut:
        return True
    s = rut.replace(".", "").replace(" ", "").upper()
    if "-" in s:
        num, dv = s.split("-", 1)
    else:
        num, dv = s[:-1], s[-1]
    if not num.isdigit():
        return False
    suma = 0
    factor = 2
    for d in reversed(num):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = suma % 11
    dig = 11 - resto
    if dig == 11:
        ver = "0"
    elif dig == 10:
        ver = "K"
    else:
        ver = str(dig)
    return ver == dv.upper()

def validate_image_file(img_field, max_mb=2, max_w=1024, max_h=1024):
    """Valida peso y dimensiones de una imagen (ImageField)."""
    if not img_field:
        return
    f = img_field
    # Tamaño
    size_mb = getattr(f, "size", 0) / (1024 * 1024)
    if size_mb > max_mb:
        raise ValidationError(f"La imagen supera {max_mb} MB.")
    # Dimensiones
    try:
        f.seek(0)
        with Image.open(f) as im:
            w, h = im.size
        if w > max_w or h > max_h:
            raise ValidationError(
                f"La imagen es muy grande ({w}×{h}). Máximo permitido: {max_w}×{max_h}px."
            )
    finally:
        try:
            f.seek(0)
        except Exception:
            pass


# ===========================
#    Widget de Avatar
# ===========================
class AvatarWidget(forms.ClearableFileInput):
    """
    Muestra:
    - Si hay foto: [Eliminar foto] + [Cambiar foto]
    - Si no hay foto: [Subir foto]
    Requiere templates/widgets/avatar_buttons.html
    """
    template_name = "usuarios/widgets/avatar_buttons.html"


# ===========================
#    Formularios existentes
# ===========================
class FormularioLogin(AuthenticationForm):
    username = forms.CharField(
        label="Correo o RUT",
        widget=forms.TextInput(attrs={
            "autofocus": True,
            "placeholder": "tucorreo@dominio.cl o 12345678-9"
        })
    )
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)




User = get_user_model()

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@dominio.cl"})
    )

class PasswordResetVerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    code = forms.CharField(
        label="Código de verificación",
        max_length=6,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "inputmode": "numeric",
            "autocomplete": "one-time-code",
            "placeholder": "6 dígitos"
        })
    )

class PasswordResetSetForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    code = forms.CharField(widget=forms.HiddenInput())
    password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "••••••••"})
    )
    password2 = forms.CharField(
        label="Repite la contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "••••••••"})
    )

    def clean(self):
        data = super().clean()
        if data.get("password1") != data.get("password2"):
            raise forms.ValidationError("Las contraseñas no coinciden.")
        if data.get("password1") and len(data["password1"]) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return data


class AdminProfileForm(forms.ModelForm):
    # Campos del usuario
    first_name = forms.CharField(label="Nombre", max_length=150, required=False)
    last_name = forms.CharField(label="Apellido", max_length=150, required=False)
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = Profile
        fields = [
            "first_name", "last_name", "email",
            "avatar", "telefono", "cargo", "time_zone", "idioma_pref",
            "empresa_logo", "empresa_nombre", "empresa_fantasia", "empresa_rut",
            "empresa_giro", "empresa_telefono", "empresa_email", "empresa_web",
            "empresa_region", "empresa_comuna", "empresa_direccion",
            "color_primario", "color_secundario",
            "notificaciones_email", "notificaciones_whatsapp", "recibe_boletin",
            "sii_regimen", "sii_actividad", "sii_cod_sii",
        ]
        widgets = {
            "avatar": AvatarWidget,  # 👈 widget de botones para el avatar
            "time_zone": forms.TextInput(attrs={"placeholder": "America/Santiago"}),
            "color_primario": forms.TextInput(attrs={"placeholder": "#E2261C"}),
            "color_secundario": forms.TextInput(attrs={"placeholder": "#232323"}),
        }

    # --------------------------
    #  Validaciones por campo
    # --------------------------
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return email
        # Unicidad frente a otros usuarios (excluye al actual)
        qs = Usuario.objects.filter(email__iexact=email)
        instance = getattr(self, "instance", None)
        if instance and getattr(instance, "user_id", None):
            qs = qs.exclude(pk=instance.user_id)
        if qs.exists():
            raise ValidationError("Este email ya está en uso por otro usuario.")
        return email

    def clean_empresa_rut(self):
        rut = self.cleaned_data.get("empresa_rut")
        if not rut:
            return rut
        if not rut_is_valid(rut):
            raise ValidationError("RUT inválido. Revisa el dígito verificador.")
        return rut_clean(rut)

    def clean_telefono(self):
        tel = self.cleaned_data.get("telefono")
        if not tel:
            return tel
        return normalize_phone(tel)

    def clean_empresa_telefono(self):
        tel = self.cleaned_data.get("empresa_telefono")
        if not tel:
            return tel
        return normalize_phone(tel)

    def clean_color_primario(self):
        return clean_hex_color(self.cleaned_data.get("color_primario"))

    def clean_color_secundario(self):
        return clean_hex_color(self.cleaned_data.get("color_secundario"))

    def clean_avatar(self):
        img = self.cleaned_data.get("avatar")
        if img:
            validate_image_file(img, max_mb=2, max_w=1024, max_h=1024)
        return img

    def clean_empresa_logo(self):
        img = self.cleaned_data.get("empresa_logo")
        if img:
            validate_image_file(img, max_mb=2, max_w=1024, max_h=1024)
        return img

    # --------------------------
    #  Guardado: solo lo cambiado
    # --------------------------
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email

def save(self, commit=True):
    """
    Guarda solo lo que cambió y maneja 'eliminar' en avatar/logo.
    """
    profile = super().save(commit=False)
    changed = set(self.changed_data)

    # ---- Actualiza User si corresponde ----
    user = profile.user
    user_fields = {"first_name", "last_name", "email"}
    user_changed = False
    if changed & user_fields:
        if "first_name" in changed:
            user.first_name = self.cleaned_data.get("first_name", user.first_name)
        if "last_name" in changed:
            user.last_name = self.cleaned_data.get("last_name", user.last_name)
        if "email" in changed:
            user.email = self.cleaned_data.get("email", user.email)
        user_changed = True

    # ---- Manejo de 'clear' en archivos (llega como False) ----
    cleared_avatar = (self.cleaned_data.get("avatar") is False)
    if cleared_avatar:
        if getattr(profile, "avatar", None):
            profile.avatar.delete(save=False)  # borra del storage
        profile.avatar = None

    cleared_logo = (self.cleaned_data.get("empresa_logo") is False)
    if cleared_logo:
        if getattr(profile, "empresa_logo", None):
            profile.empresa_logo.delete(save=False)
        profile.empresa_logo = None

    # ¿Hubo cambios en campos del profile o solo 'clear'?
    profile_fields_changed = changed - user_fields
    need_save_profile = bool(profile_fields_changed) or cleared_avatar or cleared_logo

    if commit:
        if user_changed:
            user.save()
        if need_save_profile:
            profile.save()

    return profile


