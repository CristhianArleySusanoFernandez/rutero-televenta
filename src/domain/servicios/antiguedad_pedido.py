from datetime import date

UMBRAL_SEMANAS_ALARMA = 4
# El rutero es semanal (BR-009): una asesora visita/llama a sus clientes
# en un ciclo de ~1 semana. No comprar en un par de semanas es normal
# (pudo no necesitar nada, o coincidir con una semana floja). Pasar de
# un mes (4 semanas, ~4 ciclos de rutero) sin ninguna compra es lo
# suficientemente distinto del patrón esperado como para destacarlo.


def semanas_desde_ultimo_pedido(fecha_ultimo_pedido: date, hoy: date) -> int:
    """
    Semanas completas transcurridas desde `fecha_ultimo_pedido` hasta
    `hoy`. Pura: no consulta nada, no sabe si el cliente tiene o no
    pedidos — esa decisión (mostrar o no la señal) es de quien la llama.
    """
    dias = (hoy - fecha_ultimo_pedido).days
    return max(0, dias // 7)


def es_inactividad_alarmante(semanas: int) -> bool:
    return semanas >= UMBRAL_SEMANAS_ALARMA
