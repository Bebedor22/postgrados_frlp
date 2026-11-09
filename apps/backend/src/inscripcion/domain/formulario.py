"""Formulario de inscripción por pasos (dominio puro, sin frameworks).

El aspirante completa el formulario en 4 pasos y puede guardar en cualquier
momento ("cargar y guardar"). Este módulo sabe qué campos pide cada paso, cuáles
son obligatorios y qué porcentaje del formulario está completo: ese porcentaje es
el indicador de "estado de carga del legajo" que pide el enunciado.
"""
from dataclasses import dataclass, fields
from datetime import date
from typing import Optional

COMO_CONOCIO_OPCIONES = ("SITIO_WEB", "OTROS_SITIOS_WEB", "EGRESADOS_UTN", "COLEGAS", "OTROS")
TIPOS_DE_BECA = ("30", "100")
LARGO_MAXIMO_MOTIVACION = 500


class DatosInvalidos(ValueError):
    """Un dato del formulario no respeta las reglas del dominio."""


@dataclass
class FormularioInscripcion:
    # Paso 1 — Datos personales
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    tipo_documento: Optional[str] = None  # DNI | PASAPORTE
    numero_documento: Optional[str] = None
    nacionalidad: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    genero: Optional[str] = None
    # Paso 2 — Contacto y domicilio
    email: Optional[str] = None
    email_alternativo: Optional[str] = None
    telefono_movil: Optional[str] = None
    telefono_fijo: Optional[str] = None
    calle: Optional[str] = None
    numero: Optional[str] = None
    piso_depto: Optional[str] = None
    codigo_postal: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    pais: Optional[str] = None
    # Paso 3 — Formación y motivación
    titulo_grado: Optional[str] = None
    institucion_grado: Optional[str] = None
    anio_graduacion: Optional[int] = None
    titulo_posgrado: Optional[str] = None
    como_conocio: Optional[str] = None
    como_conocio_detalle: Optional[str] = None
    motivacion: Optional[str] = None
    trabaja_en_area: Optional[bool] = None
    # Paso 4 — Beca
    solicita_beca: bool = False
    tipo_beca: Optional[str] = None  # "30" | "100"

    def actualizar(self, cambios: dict, hoy: Optional[date] = None) -> None:
        """Aplica los campos recibidos (guardado parcial) y valida el resultado."""
        nombres_validos = {f.name for f in fields(self)}
        for campo, valor in cambios.items():
            if campo not in nombres_validos:
                raise DatosInvalidos(f"Campo desconocido: {campo}")
            if isinstance(valor, str):
                valor = valor.strip() or None
            setattr(self, campo, valor)
        if not self.solicita_beca:
            self.tipo_beca = None
        self.validar(hoy or date.today())

    def validar(self, hoy: date) -> None:
        """Reglas de formato. No exige completitud: eso lo mide progreso()."""
        if self.fecha_nacimiento and self.fecha_nacimiento >= hoy:
            raise DatosInvalidos("La fecha de nacimiento debe ser anterior a hoy")
        if self.anio_graduacion and not 1950 <= self.anio_graduacion <= hoy.year:
            raise DatosInvalidos(f"El año de graduación debe estar entre 1950 y {hoy.year}")
        if self.como_conocio and self.como_conocio not in COMO_CONOCIO_OPCIONES:
            raise DatosInvalidos(f"'como_conocio' debe ser una de: {', '.join(COMO_CONOCIO_OPCIONES)}")
        if self.tipo_beca and self.tipo_beca not in TIPOS_DE_BECA:
            raise DatosInvalidos("La beca puede ser del 30% o del 100%")
        if self.motivacion and len(self.motivacion) > LARGO_MAXIMO_MOTIVACION:
            raise DatosInvalidos(f"La motivación admite hasta {LARGO_MAXIMO_MOTIVACION} caracteres")

    # ── Indicador de progreso ───────────────────────────────────────────────

    def _obligatorios_por_paso(self) -> dict[int, list[str]]:
        paso_3 = ["titulo_grado", "institucion_grado", "anio_graduacion", "como_conocio", "motivacion"]
        if self.como_conocio == "OTROS":
            paso_3.append("como_conocio_detalle")
        return {
            1: ["nombre", "apellido", "tipo_documento", "numero_documento", "nacionalidad", "fecha_nacimiento"],
            2: ["email", "telefono_movil", "calle", "numero", "codigo_postal", "ciudad", "provincia", "pais"],
            3: paso_3,
            4: ["tipo_beca"] if self.solicita_beca else [],
        }

    def faltantes_por_paso(self) -> dict[int, list[str]]:
        return {
            paso: [campo for campo in campos if getattr(self, campo) in (None, "")]
            for paso, campos in self._obligatorios_por_paso().items()
        }

    def porcentaje_completo(self) -> int:
        obligatorios = sum(len(c) for c in self._obligatorios_por_paso().values())
        faltantes = sum(len(c) for c in self.faltantes_por_paso().values())
        return round(100 * (obligatorios - faltantes) / obligatorios)

    def esta_completo(self) -> bool:
        return not any(self.faltantes_por_paso().values())