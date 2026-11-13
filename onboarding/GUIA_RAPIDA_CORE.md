# Guía rápida del Core — cómo levantarlo, probarlo y mostrarlo

> Documento del Grupo 6 para la entrega final del Core (noviembre de 2026).
> Resume qué se hizo en la rama `feature/backend-core`, cómo levantar todo con un solo comando, cómo correr los tests y cómo hacer la demo.

---

## 1. Qué funciona

El **Core completo** (PRD §5.1, SRS RF-CORE-001 a 004) funciona de punta a punta:

| Actor | Qué puede hacer | Dónde |
|---|---|---|
| **Aspirante** (sin cuenta) | Inscribirse en 4 pasos, guardar y seguir después, subir sus PDFs, enviar, ver el estado, corregir si le observan algo. Recibe emails en cada paso | `/wizard/inicio` y `/tramite/<token>` |
| **Coordinación** | Abrir y cerrar la inscripción, ver la bandeja con filtros (estado, carrera, beca) y búsqueda, exportar a Excel, ver los PDFs, revisar, observar, aprobar, rechazar, matricular y dar de baja | `/conduccion` |
| **Dirección de Posgrado** | Lo mismo que la coordinación, pero **solo lectura** (también puede exportar) | `/conduccion` |
| **Docente** | Portal del Módulo B con datos de ejemplo (no es parte del Core) | `/docente/misCursos` |

### Requisitos del SRS / PRD cubiertos

| Requisito | Cómo |
|---|---|
| RF-CORE-001 Registro del aspirante | Wizard de 4 pasos con validaciones (DNI de 7 u 8 dígitos, email, motivación ≥ 50 caracteres, obligatorios con asterisco) |
| RF-CORE-002 Gestión documental | PDF de hasta 5 MB, validado por contenido; nombre UUID y checksum SHA-256; documentos obligatorios según el SRS; descarga solo por endpoint con permisos; verificación de integridad |
| RF-CORE-003 Workflow | Borrador → Pendiente → En revisión → Completado → Activo, más Observado, Rechazado, Vencido y Baja. N° de legajo `AA-CCC-NNN` al aprobar. Email con el texto de la observación |
| RF-CORE-004 Búsqueda | Por DNI, apellido, email o N° de legajo; filtros combinados por estado, cohorte, carrera y beca; exportación a Excel con las columnas del SRS |
| BR-001 | Máximo 2 carreras por persona y cohorte |
| BR-005 | Tarea diaria (3:00 y al arrancar) que vence las reservas de más de 30 días y avisa a la coordinación |
| BR-009 | Solo la coordinación abre o cierra la inscripción |

### Calidad

- **115 tests** del backend (76 unitarios + 39 de integración) con **93 % de cobertura**.
- **Prueba E2E** con Playwright que hace la demo completa en un navegador.
- **CI en GitHub Actions**: tests y cobertura, chequeo y build del frontend, y E2E sobre el sistema levantado con Docker.

### Cómo está organizado el backend

Clean Architecture: cada módulo de `apps/backend/src/` tiene 4 capas.

```text
src/<modulo>/
├── domain/          ← entidades y reglas de negocio (Python puro, sin FastAPI ni SQLAlchemy)
├── application/     ← casos de uso (aprobar_legajo, subir_documento, …)
├── infrastructure/  ← SQLAlchemy, archivos, emails, tareas programadas
└── presentation/    ← routers de FastAPI y schemas de Pydantic
```

| Módulo | Contenido |
|---|---|
| `autenticacion` | Usuarios, login, `/auth/me` |
| `oferta_academica` | Carreras y cohortes |
| `inscripcion` | Inscripción por pasos, legajos, workflow, emails, vencimientos, Excel |
| `gestion_documental` | PDFs del legajo |
| `shared` | Configuración, base de datos, JWT, `require_role(...)`, envío de emails |

---

## 2. Qué hay que tener instalado

- **Git**
- **Docker Desktop** (abierto y en "Engine running")

Nada más: Postgres, el backend y el frontend corren dentro de Docker. Node.js solo hace falta para programar el frontend con recarga automática o para correr el E2E desde tu PC.

---

## 3. Levantar todo (Windows, macOS o Linux)

Desde la **raíz** del repo:

```powershell
git checkout feature/backend-core
git pull
Copy-Item .env.example .env        # En macOS/Linux:  cp .env.example .env
docker compose up -d --build
```

Abrí `.env` y cambiá `JWT_SECRET` por un texto largo cualquiera (mínimo 32 caracteres).

La primera vez tarda unos minutos: baja las imágenes, instala dependencias y compila el frontend. Cuando termina:

```powershell
docker compose ps
```

Tienen que estar los **4 contenedores**: `postgrado-db`, `postgrado-backend` (los dos *healthy*), `postgrado-frontend` y `postgrado-mailhog`.

**Las migraciones y los datos de demo se cargan solos** la primera vez (con la base vacía): 4 usuarios, 3 carreras, la Cohorte 2026 (cerrada), la Cohorte 2027 (abierta) y 16 aspirantes en todos los estados, con sus PDFs de ejemplo. Los links de trámite de demo aparecen en `docker compose logs backend`.

| Qué | URL |
|---|---|
| **Aplicación** | http://localhost:8081 |
| Swagger (API) | http://localhost:8000/api/docs |
| MailHog (emails) | http://localhost:8025 |

| Rol | Email | Contraseña |
|---|---|---|
| Coordinación | `admin@fenix.test` | `Admin1234!` |
| Dirección | `direccion@fenix.test` | `Direccion1234!` |
| Docente | `docente@fenix.test` | `Docente1234!` |
| CPR | `cpr@fenix.test` | `Cpr1234!` |

---

## 4. El día a día

| Quiero… | Comando |
|---|---|
| Arrancar todo | `docker compose up -d` |
| Actualizar después de un `git pull` | `docker compose up -d --build` |
| Apagar todo (conserva los datos) | `docker compose down` |
| **Empezar con la base vacía** (borra los datos) | `docker compose down -v` y después `docker compose up -d --build` |
| Ver los logs del backend | `docker compose logs -f backend` |
| Cargar los datos de demo a mano | `docker compose exec backend python -m scripts.seed` |

### Programar el frontend con recarga automática

El contenedor sirve la versión **compilada**: no se actualiza sola al cambiar un archivo. Para programar:

```powershell
docker compose stop frontend       # libera el puerto 8081
cd apps\frontend
npm install                         # la primera vez
npx expo start --web
```

Al terminar, `docker compose up -d --build frontend` vuelve a compilar el contenedor con tus cambios. El backend sí se recarga solo: los cambios en `apps/backend` se ven al instante.

---

## 5. Tests

### Backend (pytest)

```powershell
docker compose exec backend pytest --cov
```

Corre los 115 tests contra una base aparte (`postgrado_test`), que se crea y se migra sola: **no toca tus datos**. Tiene que terminar con `115 passed` y la cobertura total (93 %). Con `--cov-report=html` se genera `apps/backend/htmlcov/index.html`, que muestra línea por línea qué está cubierto.

### E2E (Playwright)

Con el sistema levantado, desde `e2e/`:

```powershell
npm install
npx playwright install chromium     # la primera vez
npx playwright test                 # 8 passed
npx playwright test --headed        # lo mismo, pero se ve el navegador
```

### CI

Cada push corre todo esto en GitHub (pestaña **Actions**): tests del backend, chequeo y build del frontend, y el E2E con `docker compose`.

---

## 6. Guion de la demo (unos 10 minutos)

Tené abiertas: una ventana **normal** (coordinación), una **de incógnito** (aspirante) y una pestaña con **MailHog** (http://localhost:8025).

| # | Dónde | Qué hacer | Qué se ve |
|---|---|---|---|
| 1 | Normal | Login con `admin@fenix.test` | Bandeja de la Cohorte 2027 con 16 legajos y el resumen por estado |
| 2 | Normal | Filtrar por **Con beca** y una carrera; **Exportar Excel** | La lista se filtra; se descarga el `.xlsx` con las columnas del SRS |
| 3 | Incógnito | `/wizard/inicio` → elegir carrera, DNI nuevo, completar los pasos 1 a 3 | Obligatorios con asterisco; no deja avanzar sin completarlos; motivación de 50 caracteres o más |
| 4 | MailHog | — | Llegó **"link de seguimiento"** con el link personal |
| 5 | Incógnito | Paso 4: **Enviar** sin documentos → después subir los 5 PDF (cualquier PDF sirve) → **Enviar** | Faltantes en rojo; un archivo que no es PDF se rechaza; al enviar → trámite **Pendiente** |
| 6 | Normal | Buscar el DNI → abrir → **Ver** un PDF → **Tomar para revisión** → **Observar** | El PDF se abre en otra pestaña; el legajo queda **Observado** |
| 7 | MailHog / Incógnito | Ver el email con la observación → recargar el trámite → **Corregir y reenviar** → **Enviar** | El texto de la observación llega por email y se ve en naranja en el trámite |
| 8 | Normal | **Tomar para revisión** → **Aprobar** → **Matricular** | N° de legajo **27-001-005**; queda **Estudiante activo**; llegan los emails |
| 9 | Normal | **Cerrar inscripción** → en incógnito, `/wizard/inicio` | "Inscripción no disponible" (BR-009). Volver a **Abrir inscripción** |
| 10 | Normal | Cerrar sesión → login con `direccion@fenix.test` | Ve todo, sin botones de acción ("Vista de solo lectura") |

**Si preguntan por la calidad:** mostrar `npx playwright test --headed` (la demo se hace sola) y `docker compose exec backend pytest --cov` (115 tests, 93 %).

**Si preguntan por BR-005:** en el portal, Benítez y Fernández están **Aprobados** con la reserva de 30 días corriendo. El vencimiento corre solo todos los días a las 3:00, y también se puede forzar con `POST /legajos/vencer-reservas` desde Swagger.

> Para la próxima demo, empezá de cero con `docker compose down -v` y `docker compose up -d --build`.

---

## 7. Si algo falla

| Síntoma | Causa probable | Solución |
|---|---|---|
| `port is already allocated` en **5432** | Hay un Postgres instalado en la PC | En el `.env`, poné `PUERTO_DB=5433` y `docker compose up -d` |
| `port is already allocated` en **8081** | Está corriendo `npx expo start` | Cortalo (`Ctrl + C`) o usá `docker compose stop frontend` para programar con Expo |
| `port is already allocated` en **8000** | Quedó un `uvicorn` corriendo fuera de Docker | Cerrá esa terminal |
| `postgrado-db` se reinicia una y otra vez; el log dice que la base fue creada con la versión 15 | Volumen de la versión vieja del compose | `docker compose down -v` y `docker compose up -d --build` |
| Un cambio en el frontend no se ve | El contenedor sirve la versión compilada | `docker compose up -d --build frontend` y `Ctrl + F5` en el navegador |
| MailHog no recibe nada | `EMAIL_MODO=simulado` en tu `.env` | Cambialo a `EMAIL_MODO=smtp` y `docker compose up -d` |
| "No se pudo conectar con el servidor" | El backend no está arriba | `docker compose ps` y `docker compose logs backend` |
| "Inscripción no disponible" sin haberla cerrado | La cohorte quedó cerrada | Abrila desde `/conduccion` |
| El login pide contraseña de nuevo | El token venció (8 h) o se cambió `JWT_SECRET` | Volver a loguearse |
| `pytest` no conecta a la base | Se corrió fuera de Docker | Usá `docker compose exec backend pytest` |
| `docker` no se reconoce como comando | Docker Desktop cerrado | Abrilo y esperá "Engine running" |

---

## 8. Mapa de la API (`/api/v1`)

| Método y ruta | Quién | Para qué |
|---|---|---|
| `POST /auth/login` · `GET /auth/me` | Todos | Login y usuario actual |
| `GET /carreras` · `POST /carreras` | Público · Coordinación y Dirección | Listar o crear carreras |
| `GET /cohortes` · `POST /cohortes` | Público · Coordinación | Listar o crear cohortes |
| `PATCH /cohortes/{id}/inscripcion` | Coordinación | Abrir o cerrar la inscripción (BR-009) |
| `POST /inscripciones` | Público | Empezar la inscripción (devuelve el token y manda el link por email) |
| `GET` / `PATCH /inscripciones/{token}` | Aspirante | Ver o guardar el avance (incluye los documentos) |
| `POST /inscripciones/{token}/confirmar` | Aspirante | Enviar (exige formulario completo y PDFs obligatorios) |
| `POST /inscripciones/{token}/documentos` | Aspirante | Subir un PDF |
| `DELETE /inscripciones/{token}/documentos/{id}` | Aspirante | Quitar un PDF |
| `GET /inscripciones/{token}/documentos/{id}/descarga` | Aspirante | Ver un PDF propio |
| `GET /documentos/{id}/download` | Coordinación y Dirección | Ver cualquier PDF |
| `GET /legajos` · `/legajos/resumen` · `/legajos/{id}` | Coordinación y Dirección | Bandeja (filtros: `estado`, `cohorte_id`, `carrera_id`, `tiene_beca`, `buscar`), resumen y detalle |
| `GET /legajos/exportar` | Coordinación y Dirección | Excel de la búsqueda (máximo 500) |
| `POST /legajos/{id}/revisar\|observar\|aprobar\|rechazar\|matricular\|baja` | Coordinación | Workflow |
| `POST /legajos/vencer-reservas` | Coordinación | Forzar BR-005 |

Para probar los endpoints protegidos en Swagger: `POST /auth/login`, copiar el `access_token` y pegarlo en **Authorize**.

---

## 9. Historial de la rama `feature/backend-core`

| # | Commit | Qué agregó |
|---|---|---|
| 1 | `fix(backend)` | Imports rotos, `requirements.txt`, `.gitignore` |
| 2 | `fix(inscripcion)` | Una sola `Base` de SQLAlchemy, sesión con commit/rollback, repositorio corregido |
| 3 | `build(docker)` | Dockerfile del backend, compose con Postgres 16 y MailHog |
| 4 | `feat(config)` | Configuración por variables de entorno, CORS acotado |
| 5 | `feat(db)` | Alembic: migraciones automáticas |
| 6 | `feat(auth)` | Login real (bcrypt + JWT), roles, usuarios de prueba |
| 7 | `feat(oferta)` | Carreras y cohortes, abrir y cerrar la inscripción |
| 8 | `feat(inscripcion)` | Inscripción por pasos con link de seguimiento |
| 9 | `feat(legajos)` | Bandeja y workflow del legajo |
| 10 | `feat(frontend)` | Wizard, trámite y login conectados a la API |
| 11 | `feat(frontend)` | Campos obligatorios y validación por paso |
| 12 | `feat(frontend)` | Portal de conducción |
| 13 | `feat(seed)` | Datos de demo |
| 14 | `docs` | Primera versión de esta guía |
| 15 | `fix(db)` | Commit antes de responder (`scope="function"`) |
| 16 | `feat(documentos)` | PDFs en el backend (RF-CORE-002) |
| 17 | `feat(frontend)` | PDFs en el wizard, el trámite y la conducción |
| 18 | `feat(notificaciones)` | Emails y vencimiento automático (BR-005) |
| 19 | `feat(legajos)` | N° de legajo del SRS, motivación mínima, baja |
| 20 | `feat(bandeja)` | Filtros por carrera y beca, exportación a Excel |
| 21 | `fix(frontend)` | Portales docente y alumno sin errores de TypeScript |
| 22 | `build(docker)` | Frontend en Docker, todo con un solo comando |
| 23 | `test(backend)` | 115 tests, 93 % de cobertura |
| 24 | `test(e2e)` | E2E con Playwright y CI en GitHub Actions |
| 25 | `docs` | Esta guía, README, CHANGELOG y ADR-005 |

Las decisiones de diseño de esta etapa (y por qué) están en [`docs/adr/ADR-005-decisiones-del-core.md`](../docs/adr/ADR-005-decisiones-del-core.md).