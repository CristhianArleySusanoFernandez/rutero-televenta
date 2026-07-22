def calcular_stats(clientes: list) -> dict:
    total = len(clientes)
    contesto = sum(1 for c in clientes if c["estado"] == "contesto")
    no_contesto = sum(1 for c in clientes if c["estado"] == "no_contesto")
    # "Novedad" no es un estado — es la presencia de al menos una fila en la
    # tabla novedades para ese cliente ese día (ver get_llamadas_del_dia).
    # Un cliente puede haber contestado y también tener novedad.
    novedad = sum(1 for c in clientes if c.get("ultima_novedad"))
    pendiente = sum(1 for c in clientes if c["estado"] == "pendiente")
    llamados = total - pendiente
    progreso = round((llamados / total * 100) if total else 0)
    return {
        "total": total,
        "contesto": contesto,
        "no_contesto": no_contesto,
        "novedad": novedad,
        "pendiente": pendiente,
        "llamados": llamados,
        "progreso": progreso,
    }


def filtrar_clientes(clientes: list, filtro: str) -> list:
    if filtro == "todos":
        return clientes
    if filtro == "novedad":
        return [c for c in clientes if c.get("ultima_novedad")]
    return [c for c in clientes if c["estado"] == filtro]
