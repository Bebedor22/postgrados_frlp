from datetime import date
from src.inscripcion.domain.entities import Aspirante, Legajo, EstadoLegajo, TipoCarrera
from src.inscripcion.domain.value_objects import DNI, Email

def inscribir_aspirante(
        id: str,
        dni: str,
        email: str,
        nombre: str,
        apellido: str,
        tipo_carrera: str,
        carrera_elegida: str,
        motivacion: str,
        solicita_beca: bool,
        cohorte_id: str,
        hoy: date = None,
) -> tuple[Aspirante, Legajo, str | None]:
    """
    Caso de uso: inscribir aspirante (RF-CORE-001).
    
    Flujo:
    1. Validar DNI (formato 7-8 dígitos) y unicidad en cohorte
    2. Crear Aspirante en estado BORRADOR
    3. Crear Legajo en estado BORRADOR con número de legajo provisional
    4. Retornar datos para que el aspirante complete documentación
    
    Returns: (aspirante, legajo, error_message)
    Error message es None si todo ok, o mensaje de error en caso contrario.
    """
    # 1. Validar formato de DNI
    try:
        dni_obj = DNI(dni)
    except ValueError as e:
        return None, None, f"DNI inválido: {e}"

    # 2. Validar formato de email
    try:
        email_obj = Email(email)
    except ValueError as e:
        return None, None, f"Email inválido: {e}"

    # 3. Validar que el aspirante no esté ya inscripto a 2 carreras simultáneas (BR-001)
    # Nota: esta validación completa requiere acceso a la BD, aquí es solo el caso de uso
    # la verificación real se hará en el repositorio

    # 4. Crear Aspirante
    tipo_carrera_obj = TipoCarrera(tipo_carrera)
    aspirante = Aspirante(
        id=id,
        dni=dni_obj,
        email=email_obj,
        nombre=nombre,
        apellido=apellido,
        tipo_carrera=tipo_carrera_obj,
        carrera_elegida=carrera_elegida,
        motivacion=motivacion,
        solicita_beca=solicita_beca,
        estado=EstadoLegajo.BORRADOR,
        fecha_inscripcion=hoy,
    )

    # 5. Crear Legajo en estado BORRADOR
    # El número de legajo se genera al aprobar (BR-005), por ahora usamos provisional
    # formato: AÑO-COHORTE-SECUENCIAL
    anyo = hoy.year if hoy else date.today().year
    numero_legajo_provisional = f"{anyo}-{cohorte_id[:8]}-001"

    legajo = Legajo(
        id=id,
        numero_legajo=numero_legajo_provisional,
        cohorte_id=cohorte_id,
        dni=dni_obj,
        apellido=apellido,
        nombre=nombre,
        email=email_obj,
        tipo_carrera=tipo_carrera_obj,
        solicita_beca=solicita_beca,
        estado=EstadoLegajo.BORRADOR,
        fecha_inscripcion=hoy,
    )

    return aspirante, legajo, None