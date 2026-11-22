# ADR-006: Decisiones de implementación de los Módulos B y C

## Contexto y Problema

Durante la implementación del Módulo B (Carga Académica mínima) y del Módulo C (Seguimiento de
Graduación, noviembre de 2026) aparecieron dos tipos de decisiones que la documentación no resolvía:

1. **Alcance y contradicciones entre documentos.** El SRS y `ARQUITECTURA.md` coinciden en las reglas
   del semáforo; el PRD y el BFD tenían redacciones distintas (umbral de seminarios, fórmula de riesgo,
   "VERDE solo manual"). Además, el BFD afirma que el aspirante no ve el semáforo, mientras el portal
   del alumno lo muestra.
2. **Detalles operativos no documentados.** Alcance real del Módulo B, persistencia del Verde manual,
   horario del job de recálculo, rutas de los endpoints, graduación automática vs. manual y el acceso
   del rol CPR.

## Decisión

### 1. Fuente de verdad: SRS + ARQUITECTURA

Ante discrepancias, prevalecen `docs/SRS.md` (requisitos) y `docs/ARQUITECTURA.md` (diseño).
Se corrigieron los documentos divergentes:

| Documento | Antes | Ahora (canónico) |
|---|---|---|
| PRD REQ-GRAD-002 | "adeuda **>1** seminario" | "adeuda **≥1** seminario" (SRS RF-GRAD-002) |
| BFD regla crítica | `aprobados < total * 0.8` | `aprobados < total` (cualquier deuda) |
| PRD criterio 3 | "nunca verde automáticamente" | Verde automático dentro de plazo; manual solo la **sobrescritura** |
| SRS BR-008 | "VERDE solo manual" | Verde normativo automático + override manual del coordinador |
| ASR-003 pseudocódigo | override dentro de la función pura | override en persistencia; la función pura no sabe del flag |

### 2. Módulo B: alcance mínimo

- Se modelan **seminarios + inscripción de legajos + nota final**. La planilla de asistencia completa
  (clases, porcentaje de presencia) queda fuera del alcance aprobado: la pantalla
  `app/docente/planilla.tsx` sigue siendo una maqueta con datos de ejemplo.
- BR-003: con nota ≥ 4 el seminario queda `APROBADO`; con nota < 4, `DESAPROBADO`.
- El progreso de obligatorios (`aprobados / total`, `adeudados`) es la entrada del semáforo (Módulo C).

### 3. El alumno ve **su propio** semáforo, con el valor almacenado

- `GET /api/v1/inscripciones/{token}/avance` expone el semáforo **persistido** (`legajos.semaforo`),
  nunca un cálculo hecho en el frontend ni en el momento de la consulta (ASR-003).
- **Diferencia con BFD §2.8:** allí se dice que los aspirantes no pueden ver el semáforo. Se interpreta
  que la restricción aplica al *dashboard de riesgo de otros estudiantes* (información interna de
  Conducción/CPR), no al propio indicador de avance, que es información del legajo del propio alumno.
  El endpoint solo responde con el token del link y no permite consultar a terceros.

### 4. Verde manual con restauración (BR-008)

- `PATCH /api/v1/legajos/{id}/semaforo/verde` con `{manual: true}` fija Verde y `semaforo_manual=true`.
- `guardar_semaforo()` no sobrescribe un legajo con ese flag (el recálculo diario lo respeta).
- El mismo endpoint con `{manual: false}` **restaura** el cálculo automático: limpia el flag y recalcula.
  Sin esta vuelta atrás, un Verde manual desactivaba el recálculo para siempre, contradiciendo el
  criterio de aceptación del SRS ("el semáforo se actualiza automáticamente").

### 5. Tareas programadas: asyncio, 2:00 y 3:00

- Se mantiene el bucle de `asyncio` del ADR-005 (sin APScheduler, sin dependencia nueva).
- El recálculo de semáforos corre al arrancar y a las **2:00** (ARQUITECTURA §12); el vencimiento de
  reservas (BR-005) a las **3:00**. Antes ambos corrían juntos a las 3:00.

### 6. Rutas canónicas y compatibilidad

- `GET /api/v1/graduacion/en-riesgo`, `GET /api/v1/graduacion/semaforo` y
  `GET /api/v1/graduacion/en-riesgo/exportar` son las rutas canónicas (ARQUITECTURA §11).
- Se conserva `GET /api/v1/en-riesgo` como alias deprecated para no romper integraciones existentes.
- Se agrega `GET /api/v1/tesis/legajos?buscar=` con rol CPR: una búsqueda reducida de legajos para
  poder dar de alta un TFI, sin exponer al CPR la bandeja completa de inscripción.

### 7. Graduación

- Automática (`graduar_si_corresponde`): exige `ACTIVO`, fecha de aprobación CPR, `total > 0` y
  `adeudados == 0`. Se dispara al crear/editar el trabajo final.
- `POST /api/v1/legajos/{id}/graduar` sigue siendo una **sobrescritura explícita de la coordinación**
  (solo valida la transición `ACTIVO → GRADUADO`). Se documenta como tal: no es la regla automática.

### 8. Portal CPR

- `login.tsx` redirige el rol CPR a `/cpr`, con un marco propio que reutiliza `Tarjeta`/`Boton` del
  portal de conducción. El alta/edición de TFI/Tesis usa todos los campos de RF-GRAD-001
  (tipo, título, director + email, codirector, fecha CPR, resolución), aunque el ERD del PRD solo
  listara `director_nombre`.

## Consecuencias

### Positivas
- Un solo algoritmo de semáforo, en dominio puro y testeable sin Docker; todos los consumidores muestran
  el valor persistido.
- El Verde manual tiene ciclo de vida completo y el recálculo automático se recupera.
- El dashboard, la exportación y el alta de tesis tienen rutas y permisos explícitos y documentados.

### Negativas
- Existen dos rutas para el listado en riesgo (una alias deprecated).
- El Módulo B no incluye asistencia: la planilla sigue siendo una maqueta.
- El bucle de asyncio no tiene la precisión de APScheduler, pero evita una dependencia más (ADR-005).
