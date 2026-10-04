"""
Máquina de estados de la factura electrónica (fe_facturas.estado).

Fuente única de verdad para las transiciones permitidas y prohibidas. Tanto la
capa de almacenamiento (stores) como la API deben validar contra este módulo,
de modo que reglas como "una VALIDADA no puede volver a BORRADOR" se apliquen
en un solo lugar.

Flujo principal solicitado:

    BORRADOR ──enviar──▶ PENDIENTE ──┬──▶ VALIDADA   (terminal)
                                      ├──▶ RECHAZADA  (terminal)
                                      ├──▶ ENVIADA    (set asíncrono de habilitación)
                                      └──▶ ERROR      (falló el transporte, reintentable)

Estados terminales (sin transiciones de salida):
    VALIDADA  — aceptada por la DIAN; inmutable.
    RECHAZADA — rechazada por la DIAN; queda RECHAZADA de forma permanente.
                La "corrección" NO reabre esta factura: se genera una factura
                NUEVA (nuevo BORRADOR, nuevo consecutivo al enviarse) que
                referencia a la original vía fe_facturas.factura_origen_id.

Notas:
- ENVIADA cubre el caso de habilitación (SendTestSetAsync), donde el veredicto
  llega de forma asíncrona; por eso ENVIADA aún puede pasar a VALIDADA/RECHAZADA.
- ERROR y OFFLINE son transitorios y reintentables (vuelven a PENDIENTE).
"""

from __future__ import annotations

from typing import Dict, FrozenSet

# --- Estados canónicos ----------------------------------------------------
BORRADOR = "BORRADOR"
PENDIENTE = "PENDIENTE"
ENVIADA = "ENVIADA"
VALIDADA = "VALIDADA"
RECHAZADA = "RECHAZADA"
ERROR = "ERROR"
OFFLINE = "OFFLINE"

ESTADOS_VALIDOS: FrozenSet[str] = frozenset(
    {BORRADOR, PENDIENTE, ENVIADA, VALIDADA, RECHAZADA, ERROR, OFFLINE}
)

# Estados terminales: no admiten ninguna transición de salida.
ESTADOS_TERMINALES: FrozenSet[str] = frozenset({VALIDADA, RECHAZADA})

# --- Tabla de transiciones permitidas -------------------------------------
# clave: estado actual → conjunto de estados destino permitidos.
TRANSICIONES_PERMITIDAS: Dict[str, FrozenSet[str]] = {
    BORRADOR:  frozenset({BORRADOR, PENDIENTE, OFFLINE}),
    PENDIENTE: frozenset({VALIDADA, RECHAZADA, ENVIADA, ERROR}),
    ENVIADA:   frozenset({VALIDADA, RECHAZADA, ERROR}),
    ERROR:     frozenset({PENDIENTE, OFFLINE}),
    OFFLINE:   frozenset({PENDIENTE, ERROR}),
    VALIDADA:  frozenset(),   # terminal
    RECHAZADA: frozenset(),   # terminal
}


class TransicionInvalidaError(ValueError):
    """Se intentó una transición de estado no permitida por la máquina."""

    def __init__(self, actual: str, nuevo: str) -> None:
        self.actual = actual
        self.nuevo = nuevo
        permitidas = ", ".join(sorted(TRANSICIONES_PERMITIDAS.get(actual, frozenset()))) or "(ninguna; estado terminal)"
        super().__init__(
            f"Transición de estado no permitida: {actual} → {nuevo}. "
            f"Desde {actual} solo se permite: {permitidas}."
        )


def es_terminal(estado: str) -> bool:
    """True si el estado no admite transiciones de salida (VALIDADA/RECHAZADA)."""
    return estado in ESTADOS_TERMINALES


def puede_transicionar(actual: str, nuevo: str) -> bool:
    """Indica si la transición actual → nuevo está permitida."""
    return nuevo in TRANSICIONES_PERMITIDAS.get(actual, frozenset())


def validar_transicion(actual: str, nuevo: str) -> None:
    """
    Valida una transición. Lanza ``TransicionInvalidaError`` si está prohibida.

    Idempotencia: re-asignar el mismo estado se permite solo en BORRADOR
    (re-guardar un borrador). En cualquier otro estado, repetir el estado se
    trata como transición inválida para evitar reescrituras silenciosas de
    facturas ya transmitidas/terminales.
    """
    if nuevo not in ESTADOS_VALIDOS:
        raise ValueError(f"Estado destino desconocido: {nuevo!r}.")
    if actual not in ESTADOS_VALIDOS:
        raise ValueError(f"Estado actual desconocido: {actual!r}.")
    if not puede_transicionar(actual, nuevo):
        raise TransicionInvalidaError(actual, nuevo)
