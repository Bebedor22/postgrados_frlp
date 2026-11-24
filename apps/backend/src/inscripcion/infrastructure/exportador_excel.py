"""Exportación de la bandeja de legajos a Excel (RF-CORE-004).

Columnas que pide el SRS: Nº Legajo, Apellido y nombre, DNI, Estado, Carrera y
Fecha de inscripción.
"""
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from src.inscripcion.domain.entities import Legajo

# Las fechas se guardan en UTC (el contenedor corre en UTC); en el Excel van en hora argentina
HORA_ARGENTINA = timezone(timedelta(hours=-3))

COLUMNAS = ["Nº Legajo", "Apellido y nombre", "DNI", "Estado", "Carrera", "Fecha inscripción"]
ANCHOS = [14, 32, 14, 18, 48, 18]

ESTADOS_LEGIBLES = {
    "BORRADOR": "En carga",
    "PENDIENTE": "Pendiente",
    "EN_REVISION": "En revisión",
    "OBSERVADO": "Observado",
    "COMPLETADO": "Aprobado",
    "ACTIVO": "Activo",
    "VENCIDO": "Vencido",
    "RECHAZADO": "Rechazado",
    "BAJA": "Baja",
    "GRADUADO": "Graduado",
}


def _hora_argentina(fecha: Optional[datetime]) -> Optional[datetime]:
    if fecha is None:
        return None
    return fecha.replace(tzinfo=timezone.utc).astimezone(HORA_ARGENTINA).replace(tzinfo=None)


def legajos_a_excel(legajos: list[Legajo], nombres_carreras: dict[Optional[str], str]) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Legajos"
    hoja.append(COLUMNAS)
    for celda in hoja[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor="1D6B59")

    for legajo in legajos:
        hoja.append([
            legajo.numero_legajo,
            f"{legajo.apellido}, {legajo.nombre}",
            str(legajo.dni),
            ESTADOS_LEGIBLES.get(legajo.estado.value, legajo.estado.value),
            nombres_carreras.get(legajo.carrera_id, ""),
            _hora_argentina(legajo.fecha_inscripcion),
        ])
    for numero, ancho in enumerate(ANCHOS, start=1):
        hoja.column_dimensions[get_column_letter(numero)].width = ancho
    for celda in hoja["F"][1:]:
        celda.number_format = "DD/MM/YYYY HH:MM"
    hoja.freeze_panes = "A2"  # La fila de títulos queda fija al bajar

    archivo = BytesIO()
    libro.save(archivo)
    return archivo.getvalue()