"""Exportación del dashboard a Excel (RF-REP-002)."""
from io import BytesIO
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from ..domain.metricas import MetricasDashboard

CABECERAS = [
    "Cohorte", "Año", "Inscriptos", "Activos", "Graduados", "Bajas", "En riesgo",
    "Retención %", "Desgranamiento %", "Tiempo promedio graduación (días)",
]
ANCHOS = [28, 8, 12, 10, 11, 9, 11, 12, 16, 30]
COLOR = "1D6B59"


def _estilo_encabezado(hoja, fila=1) -> None:
    for celda in hoja[fila]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor=COLOR)


def exportar_dashboard_a_excel(metricas: MetricasDashboard) -> bytes:
    libro = Workbook()

    resumen = libro.active
    resumen.title = "Resumen"
    resumen.append(["Métrica", "Valor"])
    _estilo_encabezado(resumen)
    for nombre, valor in [
        ("Total inscriptos", metricas.total_inscriptos),
        ("Activos", metricas.activos),
        ("Graduados", metricas.graduados),
        ("Bajas", metricas.bajas),
        ("En riesgo (ROJO)", metricas.en_riesgo),
        ("Retención %", metricas.retencion_pct),
        ("Desgranamiento %", metricas.desgranamiento_pct),
        ("Tiempo promedio graduación (días)", metricas.tiempo_promedio_graduacion_dias),
    ]:
        resumen.append([nombre, valor])
    resumen.column_dimensions["A"].width = 36
    resumen.column_dimensions["B"].width = 18
    resumen.freeze_panes = "A2"

    hoja = libro.create_sheet("Cohortes")
    hoja.append(CABECERAS)
    _estilo_encabezado(hoja)
    for cohorte in metricas.cohortes:
        hoja.append([
            cohorte.cohorte_nombre,
            cohorte.cohorte_anio,
            cohorte.inscriptos,
            cohorte.activos,
            cohorte.graduados,
            cohorte.bajas,
            cohorte.en_riesgo,
            cohorte.retencion_pct,
            cohorte.desgranamiento_pct,
            cohorte.tiempo_promedio_graduacion_dias,
        ])
    for numero, ancho in enumerate(ANCHOS, start=1):
        hoja.column_dimensions[get_column_letter(numero)].width = ancho
    hoja.freeze_panes = "A2"
    hoja.auto_filter.ref = hoja.dimensions

    metadatos = libro.create_sheet("Metadatos")
    metadatos.append(["Campo", "Valor"])
    _estilo_encabezado(metadatos)
    metadatos.append(["Fecha de generación", datetime.now()])
    metadatos.append(["Filtros aplicados", "Sin filtros (todas las cohortes)"])
    metadatos.append(["Origen", "Sistema de Posgrado - Módulo D"])
    metadatos.column_dimensions["A"].width = 26
    metadatos.column_dimensions["B"].width = 50
    for celda in metadatos["B"][2:3]:
        celda.number_format = "DD/MM/YYYY HH:MM"

    archivo = BytesIO()
    libro.save(archivo)
    return archivo.getvalue()
