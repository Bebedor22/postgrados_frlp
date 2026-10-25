# ADR-003: Estrategia de Testing

## Contexto y Problema

El principio "Testable por diseño" de la arquitectura (ARQUITECTURA.md:1.3) establece que la lógica de negocio debe
poder probarse sin base de datos, sin servidor, sin Docker. La pipeline de CI debe correr tests automáticamente en cada
PR. Esto requiere definir qué se testea, cómo y con qué cobertura.

## Decisión

### Testing en Python (Stack Principal)

- **Tests unitarios:** En la capa `domain/` (entidades, value_objects, servicios puros). No tienen imports de
  SQLAlchemy, FastAPI ni HTTP. Ejecutarse en milisegundos sin Docker.
- **Tests de casos de uso:** En `application/`, con repositorios mock. Isolation de la capa de infraestructura.
- **Tests de integración de API:** Con `httpx` (síncrono o asíncrono) sin levantar servidor real. Validar respuestas,
  headers, status codes.
- **Cobertura mínima:** ≥70% en lógica de negocio (reglas de semáforo, cálculos de asistencia, validación de
  transiciones de estado).
- **Tests E2E:** Flujo principal completo (inscripción → aprobación → semáforo) en ambiente de staging.

### Testing en TypeScript/NestJS (Stack Alternativo)

- **Tests unitarios:** En `domain/` (entidades, servicios puros). Sin decoradores NestJS, sin inyección de dependencias.
  Importables en cualquier contexto.
- **Tests e2e:** Supertest contra la aplicación NestJS levantada. Contratos definidos por los DTOs y OpenAPI.
- **Cobertura mínima:** ≥70% en lógica de negocio análoga a la Python.
- **Tests de contratación:** Verificar que los endpoints implementados coinciden exactamente con el OpenAPI generado.

### Testing en Ambos Stacks

- **Fixtures compartidas:** `conftest.py` (Python) y `jest.config.ts` / fixtures TypeScript para bases de datos de test.
- **Variables inyectables:** `hoy` en `calcular_semaforo()` y similares para facilitar tests sin dependencia a
  `date.today()`.
- **Tags de test:** `@unit`, `@integration`, `@e2e` para filtrado en la pipeline de CI.
- **Pipeline de CI:** GitHub Actions que ejecuta: `lint` → `unit tests` → `integration tests` → `build`. Un PR no puede
  mergearse si falla alguna etapa.

## Consecuencias

### Consecuencias Positivas

- **Lógica testable por diseño:** Las funciones puras como `calcular_semaforo()` y `calcular_asistencia()` están
  aisladas en `domain/` sin imports de framework. Cualquier persona puede importarlas y testearlas inmediatamente.
- **Cobertura medible:** ≥70% en lógica de negocio es un umbral claro y verificable. Evita el "testing por testing" sin
  valor real.
- **Pipeline CI automatizada:** El bloqueo automático de PRs que fallan los tests asegura calidad continua sin
  revisiones manuales extensas.

### Consecuencias Negativas

- **Costo inicial:** Escribir tests unitarios para toda la lógica de dominio requiere tiempo al principio del proyecto
  (Semanas 1-3).
- **Falsos positivos:** Tests que pasan en aislamiento pero fallan en integración (ej: tests de dominio que asumen datos
  perfectos pero la BD tiene restricciones). Mitigar con tests de integración también.
- **Maintenance overhead:** Fixtures de base de test y mocks deben mantenerse al evolucionar el modelo de datos.

## Alternativas Consideradas y Descartadas

| Opción                                            | Justificación                                                                                                                   |
|---------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| Testing solo en integración (sin tests unitarios) | Viola "Testable por diseño". Los tests unitarios en dominio cuestan poco y dan alta confianza en refactors.                     |
| Cobertura ≥90%                                    | Meta agresiva para un proyecto académico de 32 semanas. ≥70% es el punto dulce entre cobertura y velocidad de entrega.          |
| Testing E2E completo desde el día 1               | Demasiado costo inicial. Los E2E deben surgir después de que los units y integration tests estables estén en lugar (Semana 4+). |

## Estado

| Aspecto                     | Decisión                                                       |
|-----------------------------|----------------------------------------------------------------|
| **Cobertura mínima**        | ≥70% en lógica de negocio (Python y TypeScript)                |
| **Pipeline CI**             | `lint` → `unit tests` → `integration tests` → `build`          |
| **Tests unitarios**         | Capa `domain/` sola, sin DB, sin HTTP                          |
| **Tests de integración**    | API endpoints con repositorios mock o base de test             |
| **Tests E2E**               | Flujo principal en staging, opcional hasta Semana 4            |
| **Fixtures**                | `conftest.py` Python / fixtures TypeScript, versionadas en Git |
| **Variables inyectables**   | `hoy` paramétrico en funciones de semáforo/asistencia          |
| **Fecha de implementación** | Semana 1 (setup), cobertura obligatoria desde Semana 2         |

## Decision Quality

| Criterio                               | Puntuación (1-10) | Comentario                                           |
|----------------------------------------|-------------------|------------------------------------------------------|
| Cumple principio "Testable por diseño" | 9                 | Domain layer testable sin Docker ni servidor         |
| Velocidad de feedback                  | 9                 | Tests unitarios en milisegundos                      |
| Costo vs valor                         | 7                 | Costo inicial alto, pero previene bugs caros después |
| Maintainability a largo plazo          | 8                 | Fixtures versionadas, reglas claras                  |
| Facilita refactoring                   | 9                 | Confidence high para cambios en dominio              |

**Conclusión:** La estrategia de testing definida asegura que la lógica de negocio sea rigurosamente validada sin
dependencias externas, cumpliendo el principio "Testable por diseño". La cobertura mínima del 70% en lógica de negocio
es el equilibrio óptimo entre garantía de calidad y velocidad de entrega para un proyecto académico de 32 semanas. La
pipeline CI automatizada bloquea PRs que no cumplen, haciendo la calidad un proceso continuo y no una revisión final.

---
*This ADR can be updated when the testing strategy evolves. Reference this decision when adding new test suites or
modifying coverage requirements.*