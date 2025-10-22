# apps/documentos/services/upload_service.py
from django.db import transaction, IntegrityError
from apps.empresas.models import Empresa, EmpresaUsuario
from ..models import Documento
from ..tasks.extract import extract_document

def _empresa_del_usuario(user):
    # usa empresa_activa en sesión si la manejas, si no, 1ra empresa del usuario
    eu = EmpresaUsuario.objects.filter(usuario=user).select_related("empresa").first()
    return eu.empresa if eu else None

def create_documents_from_files(user, FILES):
    empresa = _empresa_del_usuario(user)
    if not empresa:
        return {"created": 0, "skipped": 0, "errors": ["Debes crear primero una empresa o no tienes permisos en ninguna."]}

    files = FILES.getlist("files[]") or FILES.getlist("files")
    if not files:
        return {"created": 0, "skipped": 0, "errors": ["No se recibieron archivos"]}

    created, skipped, errors = 0, 0, []
    for f in files:
        try:
            with transaction.atomic():
                doc = Documento(
                    empresa=empresa,
                    subido_por=user,
                    archivo=f,
                    estado="pendiente",
                )
                doc.save()
                extract_document.delay(doc.id)  # Celery asíncrono
                created += 1
        except IntegrityError:
            skipped += 1
        except Exception as e:
            errors.append(f"{getattr(f,'name','archivo')}: {e}")

    return {"created": created, "skipped": skipped, "errors": errors}
