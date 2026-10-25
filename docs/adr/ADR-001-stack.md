# ADR-001: Stack Tecnológico Principal

## Contexto y Problema

El proyecto "Sistema de Posgrado" debe definir su stack tecnológico base antes del cierre del Kickoff (Semana 3). Esta
decisión impacta toda la arquitectura, la curva de aprendizaje del equipo y el soporte disponible de la cátedra.

## Decisión

**Stack Principal:** React 19 + FastAPI (Python 3.12) + PostgreSQL 16 + TypeScript + Vite + TailwindCSS + Pydantic v2 +
SQLAlchemy 2.0 + Alembic

**Stack Alternativo:** React 19 + NestJS (TypeScript) + Prisma + PostgreSQL 16 (requiere ADR-001 aprobado)

## Consecuencias

### Consecuencias Positivas

- **Stack principal:** La documentación de la cátedra, ejemplos de código y soporte están orientados a este stack. React
  es la tecnología más demandada en la región (2026). Vite arranca en <300ms. FastAPI ofrece Swagger automático sin
  configuración. PostgreSQL es la opción más madura para datos relacionales.
- **Stack alternativo:** Un solo lenguaje (TypeScript) en frontend y backend reduce el cambio de contexto. NestJS tiene
  inyección de dependencias nativa similar a Spring. Prisma genera tipos TypeScript desde el schema para máxima
  type-safety. La estructura de módulos de NestS alinea naturalmente con Screaming Architecture.

### Consecuencias Negativas

- **Stack principal:** La curva de aprendizaje implica alternar entre Python (backend) y TypeScript (frontend). La
  documentación está escrita para Python/FastAPI, lo que puede crear fragmentación de conocimiento. Más de un lenguaje
  en el proyecto aumenta la complejidad de onboarding.
- **Stack alternativo:** Mayor boilerplate para operaciones simples. Curva de aprendizaje mayor por decoradores, módulos
  y providers de NestJS. El soporte del docente es funcional pero limitado comparado con el stack principal.

## Alternativas Consideradas y Descartadas

| Opción                               | Justificación                                                                                                |
|--------------------------------------|--------------------------------------------------------------------------------------------------------------|
| Django + React                       | Demasiada "magia" oculta. Violaría el principio de "Explícito sobre implícito" de la arquitectura.           |
| Node.js puro (sin framework backend) | Pérdida de validación tipo-first con Pydantic/Swagger automático. Mayor responsabilidad de seguridad manual. |
| Java/Spring Boot + React             | Curva de aprendizaje muy alta para el cuatrimestre. No es la demanda del mercado local (2026).               |
| Go + React                           | Buen rendimiento, pero ecosistema de testing y documentación menos maduro para el equipo.                    |

## Estado

| Aspecto               | Decisión                                           |
|-----------------------|----------------------------------------------------|
| **Fecha de registro** | Semana 3, antes del kickoff                        |
| **Autor**             | Cátedra Desarrollo de Software                     |
| **Aprobado por**      | Product Owner (Secretaría de Posgrado)             |
| **Referencias**       | SRS-001, PRD-001, ARQUITECTURA.md                  |
| **Relacionado**       | ADR-002-linting, ADR-003-testing, ADR-004-database |

## Decision Quality

| Criterio               | Puntuación (1-10) | Comentario                                     |
|------------------------|-------------------|------------------------------------------------|
| Cumple OKRs            | 9                 | Reduce tiempo de inscripción de 72hs a <15 min |
| Screaming Architecture | 8                 | Las carpetas gritan el dominio del negocio     |
| Testable por diseño    | 9                 | Lógica de dominio sin imports de framework     |
| Seguridad por defecto  | 8                 | JWT opcional solo en formulario público        |
| Mantenibilidad         | 7                 | Dos lenguajes (Py + TS) aumentan complejidad   |
| Simplicidad            | 8                 | Stack oficial, bien documentado en cátedra     |

**Conclusión:** El stack principal (React + FastAPI + PostgreSQL) es la decisión óptima para el MVP del proyecto. El
stack alternativo (NestJS + TypeScript + Prisma) está disponible para equipos que lo justifiquen con un ADR propio y
aprobación del docente antes de la Semana 4.

---
*This ADR can be updated when the stack decision changes. Future ADRs should reference this decision regarding migration
strategies or framework upgrades.*