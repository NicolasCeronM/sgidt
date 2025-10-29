# apps/documentos/services/upload_service.py
from django.db import transaction, IntegrityError
from django.core.files.base import File
from apps.empresas.models import Empresa, EmpresaUsuario
from ..models import Documento
from ..tasks.extract import extract_document

# -------------------- NUEVA FUNCIÓN REUTILIZABLE --------------------
def handle_uploaded_file(uploaded_file: File, empresa: Empresa, subido_por=None, origen: str = "web"):
    """
    Crea un objeto Documento a partir de un archivo subido.
    Esta función es genérica y puede ser usada por cualquier servicio.

    :param uploaded_file: El objeto de archivo (de un request, de un adjunto de correo, etc.).
    :param empresa: La empresa a la que pertenece el documento.
    :param subido_por: (Opcional) El usuario que subió el archivo.
    :param origen: (Opcional) De dónde vino el archivo ('web', 'email', 'api').
    :return: El objeto Documento creado.
    """
    try:
        with transaction.atomic():
            doc = Documento(
                empresa=empresa,
                subido_por=subido_por,
                archivo=uploaded_file,
                estado="pendiente",
                origen=origen # Añadimos el origen para trazabilidad
            )
            doc.save()
            extract_document.delay(doc.id)  # Lanza la tarea de OCR
            return doc
    except IntegrityError:
        # Podrías querer loggear esto. Significa que un archivo con el mismo nombre ya existe.
        return None
    except Exception as e:
        # Es buena idea loggear el error real
        print(f"Error al crear documento desde archivo {getattr(uploaded_file, 'name', 'N/A')}: {e}")
        raise # Vuelve a lanzar la excepción para que el llamador sepa que algo falló

# -------------------- FUNCIÓN ORIGINAL MODIFICADA --------------------
def _empresa_del_usuario(user):
    # usa empresa_activa en sesión si la manejas, si no, 1ra empresa del usuario
    eu = EmpresaUsuario.objects.filter(usuario=user).select_related("empresa").first()
    return eu.empresa if eu else None

def create_documents_from_files(user, FILES):
    """
    Función original, ahora utiliza nuestro nuevo handler reutilizable.
    Procesa archivos subidos desde una vista web por un usuario.
    """
    empresa = _empresa_del_usuario(user)
    if not empresa:
        return {"created": 0, "skipped": 0, "errors": ["Debes crear primero una empresa o no tienes permisos en ninguna."]}

    files = FILES.getlist("files[]") or FILES.getlist("files")
    if not files:
        return {"created": 0, "skipped": 0, "errors": ["No se recibieron archivos"]}

    created, skipped, errors = 0, 0, []
    for f in files:
        try:
            # Ahora llamamos a la nueva función centralizada
            doc = handle_uploaded_file(f, empresa, subido_por=user, origen="web")
            if doc:
                created += 1
            else:
                skipped += 1
        except Exception as e:
            errors.append(f"{getattr(f,'name','archivo')}: {e}")

    return {"created": created, "skipped": skipped, "errors": errors}