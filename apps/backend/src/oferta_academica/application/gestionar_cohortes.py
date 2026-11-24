"""Casos de uso de cohortes: alta, listado y apertura/cierre de inscripción (BR-009)."""
import uuid
from datetime import date
from typing import Optional

from src.oferta_academica.domain.entities import Cohorte, ReglaDeNegocioViolada
from src.oferta_academica.domain.repo import CohorteRepository


class CohorteNoEncontrada(Exception):
    pass


class CohorteYaExiste(Exception):
    pass


async def crear_cohorte(
        anio: int,
        nombre: str,
        repo: CohorteRepository,
        fecha_inicio: Optional[date] = None,
) -> Cohorte:
    nombre = nombre.strip()
    if await repo.obtener_por_nombre(nombre) is not None:
        raise CohorteYaExiste(nombre)
    # Una cohorte nueva arranca con la inscripción cerrada: se abre explícitamente
    cohorte = Cohorte(id=str(uuid.uuid4()), anio=anio, nombre=nombre, fecha_inicio=fecha_inicio)
    return await repo.guardar(cohorte)


async def listar_cohortes(repo: CohorteRepository, solo_abiertas: bool = False) -> list[Cohorte]:
    return await repo.listar(solo_abiertas=solo_abiertas)


async def cambiar_estado_inscripcion(cohorte_id: str, abrir: bool, repo: CohorteRepository) -> Cohorte:
    cohorte = await repo.obtener_por_id(cohorte_id)
    if cohorte is None:
        raise CohorteNoEncontrada(cohorte_id)
    if abrir:
        cohorte.abrir_inscripcion()
    else:
        cohorte.cerrar_inscripcion()
    return await repo.actualizar(cohorte)


async def verificar_cohorte_abierta(cohorte_id: str, repo: CohorteRepository) -> Cohorte:
    """Lo usa la inscripción: solo se aceptan aspirantes en cohortes abiertas (BR-009)."""
    cohorte = await repo.obtener_por_id(cohorte_id)
    if cohorte is None:
        raise CohorteNoEncontrada(cohorte_id)
    if not cohorte.acepta_inscripciones():
        raise ReglaDeNegocioViolada(f"La inscripción de {cohorte.nombre} está cerrada")
    return cohorte