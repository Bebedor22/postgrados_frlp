"""Casos de uso del catálogo de carreras (gestionado por la Dirección y la conducción)."""
import uuid

from src.oferta_academica.domain.entities import Carrera
from src.oferta_academica.domain.repo import CarreraRepository


class CarreraYaExiste(Exception):
    pass


async def crear_carrera(nombre: str, tipo: str, duracion_anios: int, repo: CarreraRepository) -> Carrera:
    carrera = Carrera(id=str(uuid.uuid4()), nombre=nombre, tipo=tipo, duracion_anios=duracion_anios)
    if await repo.obtener_por_nombre(carrera.nombre) is not None:
        raise CarreraYaExiste(carrera.nombre)
    return await repo.guardar(carrera)


async def listar_carreras(repo: CarreraRepository, solo_activas: bool = True) -> list[Carrera]:
    return await repo.listar(solo_activas=solo_activas)