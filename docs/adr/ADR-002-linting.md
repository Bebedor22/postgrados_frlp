# ADR-002: Estrategia de Linting y Formato de Código

## Contexto y Problema

El proyecto tiene múltiples stacks (Python/FastAPI y TypeScript/React/NestJS). Es crucial definir una estrategia de
linting y formato que sea consistente, rápida y exigible en la pipeline de CI. El principio "Explícito sobre implícito"
de la arquitectura exige que la calidad de código sea visible y verificable, no suposiciones.

## Decisión

**Stack Principal (Python/FastAPI):** `ruff` como herramienta única de linting/format (reemplaza flake8 + isort +
black). Pre-commit hook que corre `ruff check` y `ruff format` en cada commit.

**Stack Alternativo (NestJS/TypeScript):** `eslint + prettier` como configuración estándar. Pre-commit hook que corre
`eslint` y `prettier --write`.

**Testing Stack:** Pytest para Python, Vitest para TypeScript/JS.

## Consecuencias

### Consecuencias Positivas

- **ruff en Python:** 100× más rápido que flake8 + isort + black combinados. Una sola herramienta reduce la fricción de
  configuración. Genera reporte JSON para GitHub Actions fácilmente.
- **eslint + prettier en NestJS:** Estándar de la industria para TypeScript. Herramientas maduras con amplia comunidad.
  Configuración compartida posible entre frontend y backend si el equipo elige el stack alternativo.

### Consecuencias Negativas

- **Ruido en migración:** Si el equipo ya tiene configuración de flake8/black/isort existente, la migración a ruff puede
  generar conflictos iniciales en .rufftoml.
- **Configuración dual:** Mantener configuraciones de linting para dos stacks diferentes requiere disciplina. El
  principio "Simplicidad sobre ingeniosidad" sugiere no over-engineer la configuración.

## Alternativas Consideradas y Descartadas

| Opción                             | Justificación                                                                                                                           |
|------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| flake8 + isort + black (separados) | 3 herramientas separadas, más lentas, configuración más compleja. Violaría "Simplicidad sobre ingeniosidad".                            |
| prettier solo (sin linting)        | Formato consistente pero sin chequeo de calidad de código (imports no usados, tipos, etc.). Riesgo de código "formato pero defectuoso". |
| tslint + prettier (Legacy)         | Deprecado. tslint ya no recibe actualizaciones activas en 2026.                                                                         |

## Estado

| Aspecto                     | Decisión                                                                        |
|-----------------------------|---------------------------------------------------------------------------------|
| **Herramienta principal**   | Ruff (Python) / ESLint + Prettier (TypeScript)                                  |
| **Pre-commit**              | Obligatorio en todos los commits                                                |
| **CI Pipeline**             | GitHub Actions ruff check + pytest para Python; eslint + vitest para TypeScript |
| **Formato de reporte**      | JSON para GitHub Actions badge                                                  |
| **Fecha de implementación** | Semana 1, setup inicial                                                         |

## Decision Quality

| Criterio           | Puntuación (1-10) | Comentario                                            |
|--------------------|-------------------|-------------------------------------------------------|
| Velocidad          | 9                 | Ruff 100× más rápido que alternativa separada         |
| Consistencia       | 8                 | Una herramienta = una regla                           |
| Adopción en equipo | 7                 | Requiere habituación si ya había configuración previa |
| Maintainability    | 8                 | Menos configuración = menos deuda técnica             |
| Simplicidad        | 9                 | Una herramienta reemplaza tres                        |

**Conclusión:** Usar `ruff` para Python es la decisión óptima por velocidad y simplicidad. Para el stack alternativo
(NestJS), `eslint + prettier` es el estándar de la industria. La configuración debe ser parte del setup inicial (Semana
1) y exigible en la pipeline de CI desde el primer PR.

---
*This ADR can be updated when linting tools change or when the team adopts a single stack. Reference this decision when
adding new linters or modifying existing configurations.*