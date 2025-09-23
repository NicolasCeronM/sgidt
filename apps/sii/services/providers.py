# apps/sii/services/providers.py
from dataclasses import dataclass
import hashlib, random, time

@dataclass
class Contribuyente:
    rut: str
    razon_social: str
    actividad_principal: str
    estado: str  # ACTIVO / SUSPENDIDO

class SIIProvider:
    """Interfaz proveedor SII."""
    def consulta_contribuyente(self, rut: str) -> Contribuyente: ...
    def validar_dte(self, **payload) -> dict: ...
    def estado_dte(self, track_id: str) -> dict: ...
    def recibir_dte(self, xml_base64: str, filename: str) -> dict: ...

class MockSIIProvider(SIIProvider):
    """Respuestas determinísticas basadas en hash para que sea estable."""
    def _rng(self, key: str) -> random.Random:
        h = hashlib.sha256(key.encode()).hexdigest()
        seed = int(h[:12], 16)
        return random.Random(seed)

    def consulta_contribuyente(self, rut: str) -> Contribuyente:
        r = self._rng(f"contrib-{rut}")
        estado = "ACTIVO" if r.random() > 0.15 else "SUSPENDIDO"
        giros = ["Venta al por menor", "Servicios TI", "Construcción", "Transporte", "Restaurantes"]
        rs = f"Contribuyente {rut.replace('-','')[-4:]}"
        return Contribuyente(
            rut=rut, razon_social=rs,
            actividad_principal=r.choice(giros),
            estado=estado
        )

    def validar_dte(self, **payload) -> dict:
        key = f"{payload.get('emisor_rut')}|{payload.get('receptor_rut')}|{payload.get('tipo_dte')}|{payload.get('folio')}|{payload.get('monto_total')}|{payload.get('fecha_emision')}"
        r = self._rng(f"validar-{key}")
        ok = r.random() > 0.08  # 92% ok
        track = f"MOCK-{abs(hash(key))%1_000_000:06d}"
        return {
            "ok": ok,
            "track_id": track,
            "glosa": "Aceptado" if ok else "Rechazado por firma/estructura",
            "detalles": {"warning": r.random() > 0.85}
        }

    def estado_dte(self, track_id: str) -> dict:
        r = self._rng(f"estado-{track_id}")
        estados = ["RECIBIDO","EN_PROCESO","ACEPTADO","RECHAZADO"]
        # pseudo progreso por tiempo
        idx = int(time.time()/5) % len(estados)
        return {
            "track_id": track_id,
            "estado": estados[(idx + int(r.random()*4)) % 4],
            "glosa": "Simulación estado DTE (mock)"
        }

    def recibir_dte(self, xml_base64: str, filename: str) -> dict:
        r = self._rng(f"recibir-{filename}-{len(xml_base64)}")
        track = f"MOCK-RX-{r.randint(100000,999999)}"
        return {"ok": True, "track_id": track, "glosa": "DTE recibido (mock)"}

class RealSIIProvider(SIIProvider):
    """Stub: aquí irán las llamadas reales cuando conectemos con SII."""
    def consulta_contribuyente(self, rut: str) -> Contribuyente:
        raise NotImplementedError("Proveedor real pendiente")
    def validar_dte(self, **payload) -> dict:
        raise NotImplementedError("Proveedor real pendiente")
    def estado_dte(self, track_id: str) -> dict:
        raise NotImplementedError("Proveedor real pendiente")
    def recibir_dte(self, xml_base64: str, filename: str) -> dict:
        raise NotImplementedError("Proveedor real pendiente")
