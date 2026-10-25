# ADR-004: Modelo de Dominio y Entidades

## Contexto y Problema

El principio "Testable por diseño" (ARQUITECTURA.md:1.3) y "Explícito sobre implícito" (ARQUITECTURA.md:1.2) exigen que
las entidades y value objects del dominio sean tipos auto-contenidos, sin imports de frameworks externos (SQLAlchemy,
FastAPI, Prisma). La lógica de negocio —cálculo del semáforo, validación de transiciones de estado, cálculo de
asistencia— debe poder probarse con un test unitario que se ejecute en milisegundos, sin base de datos, sin servidor,
sin Docker.

## Decisión

### Entidades del Dominio (Python — Stack Principal)

Todas las entidades viven en `src/{modulo}/domain/entities.py` y contienen **solo lógica pura**, sin imports de
SQLAlchemy, FastAPI ni nada del framework. Son clases dataclass o clases normales con métodos que operan solo sobre sus
atributos.

**Entidades core:**

- `Aspirante`: datos personales, email, DNI, carrera, motivación, estado legajo, fechas.
- `Legajo`: número de legajo, estado, tipo_carrera, semáforo, relaciones con cohortes y documentos.
- `Seminario`: nombre, código, horas_catedra, es_obligatorio.
- `Documento`: tipo, path_storage, checksum_sha256, fecha_subida, legajo_id FK.
- `Tesis/TFI`: título, tipo, director, codirector, fecha_aprobacion_cpr, numero_resolucion.

**Entidades módulo B (Carga Académica):**

- `Asistencia`: legajo_id, seminario_id, fecha_clase, presente (bool).
- `Calificacion`: legajo_id, seminario_id, valor (1-10, un decimal).

**Entidades módulo C (Graduación):**

- `Semaforo`: tipo_carrera, fecha_inscripcion, seminarios_obligatorios_total, seminarios_aprobados,
  tiene_tfi_registrado, tiene_director_asignado, tiene_fecha_cpr → resultado: VERDE/AMARILLO/ROJO.

### Value Objects (Python — Stack Principal)

Los value objects encapsulan validación y lógica de tipo. **Viven en `src/{modulo}/domain/value_objects.py`** y pueden
ser usadas por múltiples entidades.

- `DNI`: valida formato (7-8 dígitos), mayúscul/minúsculas, unicidad en cohorte.
- `Email`: valida formato RFC, unicidad global.
- `PorcentajeAsistencia`: cálculo (presentes / total × 100), validación rango 0-100.
- `Nota`: valida rango 1-10, máximo 1 decimal.
- `EstadoLegajo`: enum con valores permitidos (
  'BORRADOR','PENDIENTE','EN_REVISION','OBSERVADO','COMPLETADO','ACTIVO','VENCIDO','RECHAZADO','BAJA','GRADUADO').
- `Semaforo`: enum VERDE/AMARILLO/ROJO con reglas de transición.

### Modelos Prisma (Stack Alternativo — TypeScript)

El modelo de datos vive en `prisma/schema.prisma` y genera tipos TypeScript automáticamente. Debe ser **consistente**
con las entidades Python (mismas restricciones, mismos nombres de campo donde sea posible).

```prisma
model Legajo {
  id             String   @id @default(uuid())
  numeroLegajo   String?  @unique @map("numero_legajo")
  cohorteId      String   @map("cohorte_id")
  dni            String
  apellido       String
  nombre         String
  email          String   @unique
  estado         EstadoLegajo @default(BORRADOR)
  tipoCarrera    TipoCarrera? @map("tipo_carrera")
  solicitaBeca   Boolean  @default(false) @map("solicita_beca")
  semaforo       Semaforo @default(VERDE)
  semaforoManual Boolean  @default(false) @map("semaforo_manual")
  createdAt      DateTime @default(now()) @map("created_at")
  updatedAt      DateTime @updatedAt @map("updated_at")
  // Relaciones
  cohorte        Cohorte      @relation(fields: [cohorteId], references: [id])
  documentos     Documento[]
  auditoria      AuditoriaLegajo[]
  tesis          Tesis[]
  @@map("legajos")
}
```

### Restricciones y Validaciones Críticas

| Regla de Negocio (BR)                                    | Implementación                                                                 | Ubicación              |
|----------------------------------------------------------|--------------------------------------------------------------------------------|------------------------|
| BR-001: Máximo 2 carreras simultáneas                    | Validación en aplicación/inscribir_aspirante.py                                | Aplicación Core        |
| BR-002: Asistencia = (presentes / clases dictadas) × 100 | Value object `PorcentajeAsistencia`                                            | Módulo B               |
| BR-003: Aprobado = Asistencia ≥75% AND Nota ≥4           | Validación en `registrar_nota_final.py`                                        | Módulo B               |
| BR-004: Solo CPR puede crear/modificar tesis             | Authorization via `require_role("CPR")`                                        | Módulo C               |
| BR-005: Reserva de vacante vence a 30 días               | Job diario `vencer_reservas`                                                   | Core / Infraestructura |
| BR-006: Documentos conservados 5 años post-graduación    | Políticas de storage, no código                                                | Infraestructura        |
| BR-007: Docente solo ve sus seminarios                   | `require_role("DOCENTE")` + filtrado por cohorte/seminario                     | Módulo B               |
| BR-008: VERDE solo manual por coordinador                | Lógica en `calcular_semaforo()`, resultado VERDE solo por asignación explícita | Módulo C               |

## Consecuencias

### Consecuencias Positivas

- **Lógica pura en dominio:** Las entidades y value objects no tienen imports de framework. Cualquier persona puede
  importar `calcular_semaforo()` desde cualquier contexto y testearlo sin levantar Docker.
- **Consistencia entre stacks:** Las mismas restricciones de negocio (BR-001 a BR-008) se implementan en Python
  (entidades) y TypeScript (Prisma schema). Si cambian las reglas, se actualizan ambos lados.
- **Testabilidad extrema:** `calcular_semaforo(datos)` es una función pura sin efectos secundarios. Test:
  `assert calcular_semaforo(datos) == EstadoSemaforo.ROJO` funciona en cualquier entorno.
- **Explícito sobre implícito:** Los nombres de entidades y value objects "gritan" el negocio. `PorcentajeAsistencia`
  knowing its own validation, no necesita comentarios. `EstadoLegajo` enum tiene todos los valores permitidos definidos
  en un CHECK constraint en la BD y en el enum Python.

### Consecuencias Negativas

- **Duplicidad de modelos:** Tener entidades Python y schema Prisma requiere sincronización. Un cambio en una requiere
  cambio en la otra. Mitigar con generación de schema a partir de las entidades o viceversa.
- **Curva de aprendizaje:** Los value objects con validación embebida (ej: `DNI`, `Email`) requieren acostumbrarse si el
  equipo viene de validación "suelta" en los controllers.
- **Rigidez inicial:** Definir enum States y validaciones en value objects al inicio del proyecto puede sentirse
  restrictivo si el negocio evoluciona rápido. Pero el principio "Testable por diseño" justifica la inversión inicial.

## Alternativas Consideradas y Descartadas

| Opción                                                  | Justificación                                                                                                                                                                            |
|---------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Entidades con imports de SQLAlchemy en domain/          | Viola "Testable por diseño". Los tests de dominio dejarían de ser unitarios y requerirían Docker/BD. Descartado rotundamente.                                                            |
| Validación solo en capa presentation/REST               | Viola "Seguridad por defecto" (ARQUITECTURA.md:1.4). La validación debe estar lo más cerca posible de los datos, preferiblemente en el dominio.                                          |
| Usar solo Prisma schemas sin entidades Python separadas | Para el stack alternativo (NestJS + Prisma) es viable, pero para el stack principal (FastAPI + SQLAlchemy) las entidades Python son necesarias. Mezclar los two aumentaría la confusión. |

## Estado

| Aspecto                     | Decisión                                                                               |
|-----------------------------|----------------------------------------------------------------------------------------|
| **Ubicación entidades**     | `src/{modulo}/domain/entities.py` (Python), `prisma/schema.prisma` (TypeScript/NestJS) |
| **Ubicación value objects** | `src/{modulo}/domain/value_objects.py` (Python)                                        |
| **Lógica pura**             | Solo en domain/, sin imports de framework                                              |
| **Enums centralizados**     | `EstadoLegajo`, `Semaforo`, `TipoCarrera` definidos en ambos stacks                    |
| **Validación embebida**     | Value objects (DNI, Email, Nota, PorcentajeAsistencia) validan al crear                |
| **Versionado**              | Entidades y schema Prisma versionadas juntas en Git                                    |
| **Fecha de implementación** | Semana 1, definido antes de escribir código de dominio                                 |

## Decision Quality

| Criterio                     | Puntuación (1-10) | Comentario                                                         |
|------------------------------|-------------------|--------------------------------------------------------------------|
| Cumple "Testable por diseño" | 9                 | Domain layer testable sin Docker, sin BD, sin HTTP                 |
| Explícito sobre implícito    | 9                 | Nombres de entidades y value objects son autocontenidos            |
| Consistencia stacks          | 7                 | Mismas reglas en Python y Prisma, requiere sync                    |
| Maintainability              | 8                 | Un cambio en reglas afecta ambos lados, pero es rastreable         |
| Facilita refactoring         | 9                 | Puedo cambiar implementación SQLAlchemy ↔ Prisma sin tocar dominio |

**Conclusión:** El modelo de dominio definido asegura que la lógica de negocio sea rigurosamente validada, testable en
aislamiento y consistente entre los dos stacks tecnológicos posibles. Los value objects con validación embebida (DNI,
Email, Nota, PorcentajeAsistencia) llevan el principio "Explícito sobre implícito" al extremo: el tipo mismo te dice qué
valores son válidos, sin necesidad de leer documentación aparte. Esta inversión inicial en diseño de dominio paga
retorno en menor deuda técnica, mayor testabilidad y refactoring más seguro.

---
*This ADR can be updated when the domain model evolves. Reference this decision when adding new entities, modifying
value objects, or changing business rules (BR-001 a BR-008).*