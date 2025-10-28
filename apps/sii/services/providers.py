# apps/sii/services/providers.py

import random
import uuid
import time
from typing import TypedDict, NotRequired, Unpack
from dataclasses import dataclass

# --- Data Transfer Objects (DTOs) - Mantenlos como están ---

@dataclass
class Contribuyente:
    rut: str
    razon_social: str
    actividad_principal: str
    estado: str  # ACTIVO, INACTIVO, etc.

class ValidarDTEPayload(TypedDict):
    emisor_rut: str
    receptor_rut: str
    tipo_dte: int
    folio: int
    monto_total: int
    fecha_emision: str
    ted: NotRequired[str]

# --- Interfaz del Provider - Mantenla como está ---

class SIIProvider:
    def consulta_contribuyente(self, rut: str) -> Contribuyente:
        raise NotImplementedError

    def validar_dte(self, **kwargs: Unpack[ValidarDTEPayload]) -> dict:
        raise NotImplementedError

    def estado_dte(self, track_id: str) -> dict:
        raise NotImplementedError
        
    def recibir_dte(self, **kwargs) -> dict:
        raise NotImplementedError

# --- Implementación REAL (no la tocamos) ---
class RealSIIProvider(SIIProvider):
    # ... tu implementación real que se conecta al SII
    pass

# --- MockSIIProvider MEJORADO (reemplaza el tuyo con este) ---

# "Base de datos" en memoria para simular el estado de los DTEs
_MOCK_DB = {
    "dtes": {}, # {track_id: dte_data}
    "contribuyentes": {
        "76.333.222-1": {
            "rut": "76.333.222-1",
            "razon_social": "Comercializadora de Software Ltda.",
            "actividad_principal": "VENTA AL POR MENOR DE OTROS PRODUCTOS EN COMERCIOS ESPECIALIZADOS",
            "estado": "ACTIVO",
        },
        "77.444.555-6": {
            "rut": "77.444.555-6",
            "razon_social": "Importadora Rápida S.A.",
            "actividad_principal": "VENTA DE PARTES, PIEZAS Y ACCESORIOS PARA VEHÍCULOS AUTOMOTORES",
            "estado": "INICIO DE ACTIVIDADES CANCELADO",
        },
    }
}

class MockSIIProvider(SIIProvider):
    """
    Un mock más realista que simula el ciclo de vida de un DTE.
    """
    def consulta_contribuyente(self, rut: str) -> Contribuyente:
        """
        Busca en la base de datos de mocks. Si no encuentra el RUT, lanza una excepción
        simulando un error 404.
        """
        contribuyente_data = _MOCK_DB["contribuyentes"].get(rut)
        if not contribuyente_data:
            # Simula el caso donde el contribuyente no existe.
            # Una implementación real podría lanzar una excepción que se traduce en un 404 en la vista.
            raise Exception(f"Contribuyente con RUT {rut} no encontrado.")
            
        return Contribuyente(**contribuyente_data)

    def validar_dte(self, **kwargs: Unpack[ValidarDTEPayload]) -> dict:
        """
        Aplica reglas de validación básicas y, si son exitosas, registra el DTE
        en estado 'PROCESANDO'.
        """
        # --- Lógica de validación ---
        if not kwargs.get("receptor_rut") or len(kwargs["receptor_rut"]) < 3:
            return {"ok": False, "glosa": "RECHAZADO: El RUT del receptor no es válido."}
        if kwargs.get("monto_total", 0) <= 0:
            return {"ok": False, "glosa": "RECHAZADO: El monto total debe ser mayor a cero."}
        
        # Simular un rechazo aleatorio para probar resiliencia (10% de las veces)
        if random.random() < 0.1:
            return {"ok": False, "glosa": "RECHAZADO: Error interno del SII simulado."}

        # --- Si pasa la validación, se crea el DTE en la "BD" ---
        track_id = str(uuid.uuid4())[:10]
        
        _MOCK_DB["dtes"][track_id] = {
            "payload": kwargs,
            "estado": "PROCESANDO",
            "glosa": "Documento recibido y en proceso de validación.",
            "consultas": 0,  # Contador de cuántas veces se ha consultado el estado
            "timestamp": time.time()
        }
        
        return {
            "ok": True,
            "track_id": track_id,
            "glosa": "Documento recibido por el SII. Consulte el estado con el track_id.",
        }

    def estado_dte(self, track_id: str) -> dict:
        """
        Consulta el estado de un DTE por su track_id.
        Simula el cambio de estado de PROCESANDO a ACEPTADO/RECHAZADO.
        """
        dte = _MOCK_DB["dtes"].get(track_id)
        
        if not dte:
            return {"estado": "NO_ENCONTRADO", "glosa": "Track ID no existe en los registros del SII."}
        
        dte["consultas"] += 1
        
        # Simular que el SII procesa el DTE después de 2 consultas
        if dte["estado"] == "PROCESANDO" and dte["consultas"] > 2:
            # Decidir aleatoriamente si se acepta o rechaza (90% de aceptación)
            if random.random() < 0.9:
                dte["estado"] = "ACEPTADO"
                dte["glosa"] = "DTE Aceptado por el SII."
            else:
                dte["estado"] = "RECHAZADO"
                dte["glosa"] = "DTE Rechazado con Reparos: Monto total no coincide con detalle."

        return {"estado": dte["estado"], "glosa": dte["glosa"]}

    def recibir_dte(self, **kwargs) -> dict:
        """
        Simula la recepción de un DTE enviado por un tercero.
        """
        # Aquí podrías añadir lógica para simular fallos en la recepción
        # por ahora, mantenemos un éxito simple.
        return {
            "ok": True,
            "track_id": str(uuid.uuid4())[:10],
            "detail": "Archivo XML recibido y encolado para procesamiento."
        }


# --- Función de acceso (mantenla como está) ---
def get_provider() -> SIIProvider:
    # Esta lógica te permite cambiar entre el mock y el real fácilmente
    from django.conf import settings
    if getattr(settings, "SII_USE_MOCK", True):
        return MockSIIProvider()
    return RealSIIProvider()