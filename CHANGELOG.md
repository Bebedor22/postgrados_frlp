# Changelog — Sistema de  Posgrado

Todos los cambios notables de este proyecto se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).  
Este proyecto sigue [Versionado Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

> Los cambios que están en `develop` pero no en un release van acá.

### Added
- Estructura inicial del repositorio
- Documentación base: SRS, PRD, BFD, Arquitectura, Cronograma
- Backend FastAPI con Clean Architecture, PostgreSQL 16 en Docker y migraciones con Alembic
- Login con JWT y bcrypt, roles y usuarios de prueba
- Carreras, cohortes y apertura/cierre de la inscripción (BR-009)
- Inscripción por pasos con link de seguimiento y límite de 2 carreras por cohorte (BR-001)
- Bandeja de la coordinación y workflow del legajo, con número de legajo definitivo al aprobar
- Frontend conectado: wizard de inscripción, trámite del aspirante, login y portal de conducción
- Script de datos de demo (`scripts/seed.py`) y guía rápida del Core (`onboarding/GUIA_RAPIDA_CORE.md`)

---

## [v0.1.0-alpha] — Sprint 0 (esperado 15/05/2026)

### Added
- Autenticación JWT básica (login/logout)
- Modelo de base de datos inicial con migraciones
- Docker Compose funcional para ambiente de desarrollo
- Pipeline de CI/CD base en GitHub Actions (lint + test + build)

---

## Historial de versiones planificadas

| Versión | Fecha planificada | Descripción |
|---------|:-----------------:|------------|
| v0.1.0-alpha | 15/05/2026 | Auth + DB + Docker |
| v0.5.0-beta | 31/07/2026 | Core completo |
| v0.8.0-rc | 11/09/2026 | Core + Módulo especializado |
| v1.0.0 | 23/10/2026 | Sistema completo + docs |
