# Guía rápida del Core — cómo levantarlo y mostrarlo

> Documento **temporal** del Grupo 6 para la etapa de entregas (noviembre 2026).
> Resume qué está hecho en la rama `feature/backend-core`, cómo levantar backend y frontend en la misma máquina sin conflictos y cómo hacer la demo.
> Cuando la rama se fusione y la documentación oficial (README, ARQUITECTURA) esté al día, este archivo se puede borrar.

---

## 1. Qué funciona hoy

El **Core** (inscripción + legajo + workflow) funciona de punta a punta, por pantalla:

| Actor | Qué puede hacer | Dónde |
|---|---|---|
| **Aspirante** (sin cuenta) | Inscribirse en 4 pasos, guardar y seguir después, enviar la inscripción, ver el estado y corregir si le observan algo | `/wizard/inicio` y `/tramite/<token>` |
| **Coordinación** | Abrir y cerrar la inscripción de la cohorte, ver la bandeja de inscriptos (resumen, filtros, búsqueda), revisar, observar, aprobar, rechazar y matricular | `/conduccion` |
| **Dirección de Posgrado** | Lo mismo que la coordinación, pero en **solo lectura** | `/conduccion` |

Reglas de negocio que ya controla el backend:
- **BR-001**: máximo 2 carreras por persona en la misma cohorte.
- **BR-005**: la reserva de vacante vence a los 30 días de aprobada (`POST /legajos/vencer-reservas`).
- **BR-009**: solo la coordinación abre o cierra la cohorte.
- **Workflow**: solo se permiten las transiciones válidas (`BORRADOR → PENDIENTE → EN_REVISION → COMPLETADO → ACTIVO`, más `OBSERVADO`, `RECHAZADO` y `VENCIDO`). Una acción que no corresponde responde **409**.
- Al aprobar se asigna el **número de legajo definitivo** (`27-0001`, `27-0002`, …); antes tiene uno provisorio (`P-XXXXXXXX`).

**Todavía no está hecho:** subida de PDFs (los botones del paso 4 no hacen nada), envío de emails (por ahora es simulado), tests con pytest y CI de Python. Las pantallas de **docente** y **alumno** son las que ya existían y tienen errores propios: no forman parte de la demo.

### Historial de la rama `feature/backend-core`

| # | Commit | Qué agregó |
|---|---|---|
| 1 | `fix(backend)` | Imports rotos, `requirements.txt`, `.gitignore` |
| 2 | `fix(inscripcion)` | Una sola `Base` de SQLAlchemy, sesión con commit/rollback, repositorio corregido |
| 3 | `build(docker)` | Dockerfile del backend, compose con Postgres 16, backend y MailHog |
| 4 | `feat(config)` | Configuración por variables de entorno (`.env`), CORS acotado |
| 5 | `feat(db)` | Alembic: las migraciones corren solas al levantar Docker |
| 6 | `feat(auth)` | Login real (bcrypt + JWT), roles, usuarios de prueba |
| 7 | `feat(oferta)` | Carreras y cohortes, abrir y cerrar la inscripción |
| 8 | `feat(inscripcion)` | Inscripción por pasos con link de seguimiento (token) |
| 9 | `feat(legajos)` | Bandeja de la coordinación y workflow del legajo |
| 10 | `feat(frontend)` | Wizard, trámite y login conectados a la API |
| 11 | `feat(frontend)` | Campos obligatorios y validación por paso |
| 12 | `feat(frontend)` | Portal de conducción |
| 13 | `feat(seed)` | Script que carga datos de demo |

### Cómo está organizado el backend

Clean Architecture: cada módulo de `apps/backend/src/` tiene 4 capas.

```text
src/<modulo>/
├── domain/          ← entidades y reglas de negocio (Python puro, sin FastAPI ni SQLAlchemy)
├── application/     ← casos de uso (aprobar_legajo, iniciar_inscripcion, …)
├── infrastructure/  ← SQLAlchemy: modelos ORM y repositorios de Postgres
└── presentation/    ← routers de FastAPI y schemas de Pydantic
```

| Módulo | Contenido |
|---|---|
| `autenticacion` | Usuarios, login, `/auth/me` |
| `oferta_academica` | Carreras y cohortes |
| `inscripcion` | Inscripción pública por pasos, legajos y workflow |
| `shared` | Configuración, conexión a la base, JWT y `require_role(...)` |

---

## 2. Qué hay que tener instalado

- **Git**
- **Docker Desktop** (abierto y en "Engine running" antes de empezar)
- **Node.js 20 o superior** (probado con Node 22) — solo para el frontend

No hace falta instalar Python ni Postgres: el backend y la base corren dentro de Docker.

---

## 3. Primera vez (unos 10 minutos)

Todos los comandos son de **PowerShell** y se corren desde la **raíz del repo**, salvo que se indique otra cosa.

### 3.1 Bajar la rama

```powershell
git clone https://github.com/Bebedor22/postgrados_frlp.git
cd postgrados_frlp
git checkout feature/backend-core
```

Si ya tenías el repo clonado:

```powershell
git fetch origin
git checkout feature/backend-core
git pull
```

> ⚠️ El trabajo del Core **todavía no está en `main` ni en `backend`**. Si estás en otra rama, vas a ver el proyecto viejo.

### 3.2 Crear el `.env`

```powershell
Copy-Item .env.example .env
```

Abrí `.env` y cambiá `JWT_SECRET` por un texto largo cualquiera (mínimo 32 caracteres). Para generarlo:

```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
```

> El `.env` **nunca se sube a Git** (ya está en el `.gitignore`).

### 3.3 Levantar backend, base y MailHog

```powershell
docker compose up -d --build
docker compose ps
```

Tienen que aparecer 3 contenedores en estado `running`: `postgrado-db`, `postgrado-backend` y `postgrado-mailhog`.
Las **migraciones corren solas** al arrancar el backend (`alembic upgrade head`).

Para comprobar: abrí http://localhost:8000/api/docs. Tiene que cargar el Swagger.

### 3.4 Cargar los datos de demo

```powershell
docker compose exec backend python -m scripts.seed
```

Crea los usuarios de prueba, 3 carreras, la Cohorte 2026 (cerrada), la Cohorte 2027 (abierta) y **16 aspirantes** repartidos en todos los estados. Al final imprime dos links de trámite para usar en la demo: **anotalos**.
Se puede correr más de una vez: lo que ya existe no se duplica.

### 3.5 Levantar el frontend

En **otra** terminal:

```powershell
cd apps\frontend
npm install
npx expo start --web --clear
```

Se abre http://localhost:8081. `npm install` solo hace falta la primera vez y cuando cambia el `package.json`.

> El frontend **no** corre en Docker (está comentado en el compose): corre con Node en tu máquina y le habla al backend de Docker por `http://localhost:8000/api/v1`.

---

## 4. El día a día

| Quiero… | Comando |
|---|---|
| Arrancar todo | `docker compose up -d` + (en `apps\frontend`) `npx expo start --web` |
| Después de un `git pull` | `docker compose up -d --build` (aplica migraciones nuevas) + `npx expo start --web --clear` |
| Ver los logs del backend | `docker compose logs -f backend` |
| Apagar todo | `Ctrl + C` en la terminal de Expo + `docker compose down` |
| **Empezar con la base vacía** | `docker compose down -v` → `docker compose up -d --build` → `docker compose exec backend python -m scripts.seed` |

`docker compose down` **conserva** los datos. `docker compose down -v` **los borra** (útil antes de una demo para empezar de cero).

---

## 5. Direcciones y usuarios

| Qué | URL |
|---|---|
| Frontend | http://localhost:8081 |
| Login | http://localhost:8081/login |
| Wizard de inscripción | http://localhost:8081/wizard/inicio |
| Portal de conducción | http://localhost:8081/conduccion |
| Swagger (API) | http://localhost:8000/api/docs |
| MailHog (emails de prueba) | http://localhost:8025 |

| Rol | Email | Contraseña | Entra a |
|---|---|---|---|
| Coordinación | `admin@fenix.test` | `Admin1234!` | `/conduccion` (puede todo) |
| Dirección | `direccion@fenix.test` | `Direccion1234!` | `/conduccion` (solo lectura) |
| Docente | `docente@fenix.test` | `Docente1234!` | pantallas viejas, fuera de la demo |
| CPR | `cpr@fenix.test` | `Cpr1234!` | sin pantallas todavía |

Los aspirantes **no tienen usuario**: entran con el link de seguimiento que reciben al empezar la inscripción.

---

## 6. Guion de la demo (unos 10 minutos)

Usá **dos ventanas**: una normal para la coordinación y una **de incógnito** para el aspirante. Así cada uno tiene su propia sesión.

| # | Ventana | Qué hacer | Qué se ve |
|---|---|---|---|
| 1 | Normal | Login con `admin@fenix.test` | Portal de conducción con la Cohorte 2027 abierta y 16 legajos |
| 2 | Normal | Tocar las tarjetas del resumen (Pendientes, Observados…) y buscar "Rodríguez" o un DNI | La lista se filtra |
| 3 | Incógnito | Ir a `/wizard/inicio`, elegir carrera, poner un DNI nuevo y completar los 4 pasos | El avance se guarda en cada paso; los obligatorios tienen asterisco rojo y no se puede avanzar sin completarlos |
| 4 | Incógnito | Enviar la inscripción | Pantalla del trámite con estado **Pendiente** y el link de seguimiento |
| 5 | Normal | Buscar al aspirante nuevo → **Tomar para revisión** → **Observar** con un comentario | El legajo pasa a Observado |
| 6 | Incógnito | Recargar el trámite → **Corregir y reenviar** → enviar de nuevo | Se ve la observación en naranja; al reenviar vuelve a Pendiente |
| 7 | Normal | **Tomar para revisión** → **Aprobar** → **Matricular** | Se asigna el N° definitivo (`27-0005`) y queda **Estudiante activo** |
| 8 | Normal | **Cerrar inscripción** de la cohorte | En la ventana de incógnito, `/wizard/inicio` muestra "Inscripción no disponible" |
| 9 | Normal | Cerrar sesión → login con `direccion@fenix.test` | Ve todo pero sin botones de acción ("Vista de solo lectura") |

**Atajos si falta tiempo:** los links que imprime el seed abren directamente un trámite **observado** (Ríos) y uno **a medio completar** (Torres). En la bandeja ya hay legajos en todos los estados para mostrar.

**Si preguntan por la seguridad:** el token de seguimiento se guarda en la base solo como hash SHA-256; las contraseñas con bcrypt; cada endpoint de conducción exige JWT y rol (`require_role`); quien valida las transiciones es el backend, no el frontend.

> Después de la demo, abrí de nuevo la inscripción (o corré `down -v` + seed) para dejar todo como estaba.

---

## 7. Si algo falla

| Síntoma | Causa probable | Solución |
|---|---|---|
| `port is already allocated` en **5432** | Hay un Postgres instalado en Windows corriendo | Detenelo: `Stop-Service postgresql*` (PowerShell como administrador) o desde "Servicios" |
| `port is already allocated` en **8000** | Quedó un `uvicorn` corriendo fuera de Docker | Cerrá esa terminal. **No** corras el backend local y el de Docker a la vez |
| Expo pregunta si usar otro puerto en vez del **8081** | Hay otro Expo abierto | Respondé **No**, cerrá el otro Expo y volvé a arrancar. En otro puerto el backend rechaza las llamadas (CORS) |
| `postgrado-db` se reinicia una y otra vez; el log dice que la base fue creada con la versión 15 | Quedó el volumen de la versión vieja del compose (Postgres 15) | `docker compose down -v` y `docker compose up -d --build` (borra los datos viejos) |
| El backend arranca pero los cambios del código no se ven | Imagen vieja | `docker compose up -d --build` |
| El frontend muestra una versión vieja de una pantalla | Caché de Metro | Cortar Expo y `npx expo start --web --clear`; en el navegador, `Ctrl + F5` |
| "No se pudo conectar con el servidor" en el frontend | El backend no está arriba | `docker compose ps` y `docker compose logs backend` |
| "Todavía no hay carreras cargadas" o "Inscripción no disponible" sin haberla cerrado | Base vacía o cohorte cerrada | Correr el seed (3.4) o abrir la inscripción desde `/conduccion` |
| El login vuelve a pedir contraseña de golpe | El token venció (8 h) o se cambió el `JWT_SECRET` | Volver a loguearse |
| `docker` no se reconoce como comando | Docker Desktop cerrado | Abrir Docker Desktop y esperar a "Engine running" |
| Avisos en la consola de Expo sobre `docente/` o `alumno/` | Errores que ya tenían esas pantallas | No afectan la demo del Core |

---

## 8. Mapa de la API (`/api/v1`)

| Método y ruta | Quién | Para qué |
|---|---|---|
| `POST /auth/login` · `GET /auth/me` | Todos | Login y usuario actual |
| `GET /carreras` · `POST /carreras` | Público · Coordinación y Dirección | Listar o crear carreras |
| `GET /cohortes` · `POST /cohortes` | Público · Coordinación | Listar o crear cohortes |
| `PATCH /cohortes/{id}/inscripcion` | Coordinación | Abrir o cerrar la inscripción |
| `POST /inscripciones` | Público | Empezar la inscripción (devuelve el token) |
| `GET` / `PATCH /inscripciones/{token}` | Aspirante | Ver o guardar el avance |
| `POST /inscripciones/{token}/confirmar` | Aspirante | Enviar la inscripción |
| `GET /legajos` · `GET /legajos/resumen` · `GET /legajos/{id}` | Coordinación y Dirección | Bandeja, resumen y detalle |
| `POST /legajos/{id}/revisar\|observar\|aprobar\|rechazar\|matricular` | Coordinación | Workflow |
| `POST /legajos/vencer-reservas` | Coordinación | BR-005 |

El detalle de cada endpoint (cuerpos, respuestas, errores) está en el Swagger: http://localhost:8000/api/docs. Para probar los endpoints protegidos ahí: `POST /auth/login`, copiar el `access_token` y pegarlo en el botón **Authorize**.