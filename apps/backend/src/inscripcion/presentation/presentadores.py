"""Convierte resultados de los casos de uso en respuestas de la API.

Lo comparten el router del aspirante y el del coordinador, así el formulario,
el progreso y el historial se muestran igual en los dos.
"""
from dataclasses import asdict

from src.inscripcion.presentation.schemas_inscripcion import (
    CambioDeEstadoResponse,
    ProgresoResponse,
    TramiteResponse,
)


def tramite_a_respuesta(legajo, formulario, historial) -> TramiteResponse:
    return TramiteResponse(
        legajo_id=legajo.id,
        numero_legajo=legajo.numero_legajo,
        estado=legajo.estado.value,
        puede_editar=legajo.puede_editar_formulario(),
        cohorte_id=legajo.cohorte_id,
        carrera_id=legajo.carrera_id,
        datos=asdict(formulario),
        progreso=ProgresoResponse(
            porcentaje=formulario.porcentaje_completo(),
            completo=formulario.esta_completo(),
            faltantes_por_paso=formulario.faltantes_por_paso(),
        ),
        historial=[CambioDeEstadoResponse(**asdict(c)) for c in historial],
    )