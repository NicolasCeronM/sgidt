from random import randint, choice
from decimal import Decimal
from calendar import monthrange
from datetime import datetime, timedelta
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware, now
from django.core.files.base import ContentFile
from django.db import transaction

from apps.empresas.models import Empresa
from apps.documentos.models import Documento

def mid_of_month_aware(year: int, month: int):
    day = min(15, monthrange(year, month)[1])
    return make_aware(datetime(year, month, day, 12, 0, 0))

def rnd_rut():
    base = randint(76000000, 96999999)
    return f"{base}-K"

def compute_amounts(tipo: str):
    bruto = Decimal(randint(80_000, 2_000_000))
    if "exenta" in (tipo or ""):
        exento = bruto
        return (Decimal("0"), exento, Decimal("0"), exento)
    else:
        neto = (bruto / Decimal("1.19")).quantize(Decimal("1"))
        iva = (neto * Decimal("0.19")).quantize(Decimal("1"))
        total = neto + iva
        return (neto, Decimal("0"), iva, total)

class Command(BaseCommand):
    help = "Crea documentos de prueba para el dashboard."

    def add_arguments(self, parser):
        parser.add_argument("--months", type=int, default=6, help="Meses hacia atrás (incluye actual).")
        parser.add_argument("--rows", type=int, default=30, help="Cantidad total de documentos.")
        parser.add_argument("--reset", action="store_true", help="Borra documentos de la empresa antes de sembrar.")
        parser.add_argument("--if-empty", action="store_true", help="Sembrar solo si no hay documentos.")

    def handle(self, *args, **opts):
        months = opts["months"]
        rows = opts["rows"]
        reset = opts["reset"]
        if_empty = opts["if_empty"]

        empresa = Empresa.objects.first()
        if not empresa:
            self.stdout.write(self.style.ERROR("No hay Empresa. Crea una en /admin y reintenta."))
            return

        if if_empty and Documento.objects.filter(empresa=empresa).exists():
            self.stdout.write(self.style.WARNING("Ya hay documentos. No se siembra (--if-empty)."))
            return

        if reset:
            Documento.objects.filter(empresa=empresa).delete()

        TIPOS = ["factura_afecta", "factura_exenta", "boleta_afecta", "boleta_exenta", "nota_credito"]
        ESTADOS = ["pendiente", "procesando", "procesado", "error"]

        per_month = max(1, rows // months)
        AHORA = now()

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Sembrando ~{per_month*months} documentos para {empresa}"
        ))

        with transaction.atomic():
            folio_seq = 10000
            for back in range(months - 1, -1, -1):
                year = AHORA.year
                month = AHORA.month - back
                while month <= 0:
                    month += 12
                    year -= 1

                fecha_emision = mid_of_month_aware(year, month)
                creado_en_deseado = fecha_emision + timedelta(days=2)

                for _ in range(per_month):
                    folio_seq += 1
                    tipo = choice(TIPOS)
                    estado = choice(ESTADOS)
                    rut = rnd_rut()
                    razon = choice([
                        "COMERCIAL ACME SPA", "JIRAFA DIGITAL SPA", "IMPORTADORA GHI",
                        "DISTRIBUIDORA DEF", "SERVICIOS XYZ LTDA.",
                    ])

                    monto_neto, monto_exento, iva, total = compute_amounts(tipo)

                    doc = Documento.objects.create(
                        empresa=empresa,
                        subido_por=None,
                        nombre_archivo_original=f"F-{folio_seq}.txt",
                        estado=estado,
                        tipo_documento=tipo,
                        folio=str(folio_seq),
                        fecha_emision=fecha_emision.date(),
                        rut_proveedor=rut,
                        razon_social_proveedor=razon,
                        monto_neto=monto_neto,
                        monto_exento=monto_exento,
                        iva=iva,
                        total=total,
                        iva_tasa=Decimal("19.00"),
                        ocr_fuente="seed",
                        ocr_lang="spa",
                        ocr_engine="seed",
                    )

                    unique_bytes = f"Seed SGIDT\nFOLIO={folio_seq}\nUUID={uuid4()}\n".encode("utf-8")
                    doc.archivo.save(f"F-{folio_seq}.txt", ContentFile(unique_bytes), save=True)
                    Documento.objects.filter(pk=doc.pk).update(creado_en=creado_en_deseado)

        self.stdout.write(self.style.SUCCESS("Seed completo."))

'''
PARA EJECUTAR ESTAS PRUEBAS COMPIA ESTE COMANDO EN LA CONSOLA:

docker compose exec -T web python manage.py seed_docs --months 6 --rows 30 --reset

'''