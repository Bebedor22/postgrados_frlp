"""Exportación del listado de estudiantes en riesgo a Excel (US-C-003)."""
from datetime import datetime
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from ..domain.repo import FilaSeguimiento

CABECERAS = [
    "Legajo", "Apellido", "Nombre", "Carrera", "Tipo de carrera", "Fecha de inscripción",
    "Seminarios obligatorios", "Seminarios aprobados", "Seminarios adeudados",
    "Días en ROJO", "VERDE manual", "Desde",
]
ANCHOS = [16, 18, 18, 32, 16, 18, 22, 20, 20, 13, 14, 20]


def exportar_en_riesgo_a_excel(filas: list[FilaSeguimiento]) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.title = "En riesgo"
    hoja.append(CABECERAS)
    for celda in hoja[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor="1D6B59")

    for fila in filas:
        hoja.append([
            fila.numero_legajo,
            fila.apellido,
            fila.nombre,
            fila.carrera_nombre,
            fila.tipo_carrera,
            fila.fecha_inscripcion,
            fila.seminarios_obligatorios_total,
            fila.seminarios_aprobados,
            fila.seminarios_adeudados,
            fila.dias_en_riesgo(),
            "Sí" if fila.semaforo_manual else "No",
            fila.semaforo_desde,
        ])

    for numero, ancho in enumerate(ANCHOS, start=1):
        hoja.column_dimensions[get_column_letter(numero)].width = ancho
    hoja.freeze_panes = "A2"
    hoja.auto_filter.ref = hoja.dimensions

    metadatos = libro.create_sheet("Metadatos")
    metadatos.append(["Campo", "Valor"])
    for celda in metadatos[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor="1D6B59")
    metadatos.append(["Fecha de generación", datetime.now()])
    metadatos.append(["Legajos en ROJO", len(filas)])
    metadatos.append(["Origen", "Sistema de Posgrado - Módulo C"])
    metadatos.column_dimensions["A"].width = 26
    metadatos.column_dimensions["B"].width = 40

    archivo = BytesIO()
    libro.save(archivo)
    return archivo.getvalue()
