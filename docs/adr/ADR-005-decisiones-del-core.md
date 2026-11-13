# ADR-005: Decisiones de implementación del Core

## Contexto y Problema

Durante la implementación del Core (rama `feature/backend-core`, noviembre de 2026) aparecieron decisiones que la
documentación (SRS, PRD, ARQUITECTURA y ADR-001 a ADR-004) no definía, o que convenía resolver de otra forma por
simplicidad. Este ADR las registra con su motivo, para que el equipo y la cátedra puedan revisarlas.

## Decisión

### 1. El aspirante no tiene usuario: entra con un link personal

- Al empezar la inscripción se genera un token aleatorio (`secrets.token_urlsafe(32)`). El aspirante lo recibe en
  pantalla y por email como link `/tramite/<token>`.
- En la base se guarda **solo el hash SHA-256** del token, igual que con las contraseñas.
- **Motivo:** el aspirante se inscribe una vez; pedirle crear una cuenta es una barrera. El PRD deja el login fuera
  del alcance del wizard.

### 2. Número de legajo `AA-CCC-NNN`

- SRS: "AÑO-COHORTE-SECUENCIAL, ej.: 26-001-045 → año 2026, cohorte 1, estudiante 45".
- El SRS no define el número de cohorte. Se interpreta como **el orden de la cohorte dentro de su año** (por fecha
  de creación), así no hace falta una columna nueva.
- El número se asigna **al aprobar**, no al inscribirse, para que la numeración no tenga huecos. Antes se usa uno
  provisorio (`P-` + 8 caracteres del UUID).

### 3. Validación de PDFs por firma del archivo

- Se acepta un archivo si empieza con `%PDF-` y pesa hasta 5 MB. No se usa la extensión ni el `Content-Type` del
  navegador.
- **Diferencia con ARQUITECTURA §9.2:** allí se sugiere `python-magic`, que necesita la librería del sistema
  `libmagic` (complicada de instalar en Windows). Para un solo formato, la firma alcanza.
- Archivos en disco (volumen de Docker `postgrado-storage`) con nombre UUID; checksum verificado en cada descarga.

### 4. Emails: MailHog en desarrollo, SMTP configurable

- `EMAIL_MODO=smtp` manda a MailHog (no sale nada a internet); `EMAIL_MODO=simulado` solo escribe en el log.
- Los emails se arman en los casos de uso a través del contrato `Notificador` (dominio) y se envían en una tarea en
  segundo plano **después** del commit. Un error de envío nunca rompe la operación.

### 5. Commit de la transacción antes de responder

- `get_db` se usa con `Depends(get_db, scope="function")` (FastAPI ≥ 0.121). Con el scope por defecto, FastAPI
  respondía antes de hacer el commit, y el cliente podía leer datos que todavía no estaban guardados.

### 6. Tarea diaria sin librería externa

- El vencimiento de reservas (BR-005, ARQUITECTURA §12) corre en un bucle de `asyncio` que arranca con la app
  (`lifespan`): al iniciar y todos los días a las 3:00.
- **Diferencia con ARQUITECTURA §12:** se sugería APScheduler. Para una única tarea diaria, el bucle evita una
  dependencia. Si se suman tareas (por ejemplo, las del Módulo B), conviene pasar a APScheduler.

### 7. Frontend en Docker como sitio estático

- La imagen compila la app con `expo export --platform web` y la sirve con nginx (SPA: toda ruta devuelve
  `index.html`).
- **Motivo:** `expo start` dentro de Docker es lento y no detecta cambios de archivos en Windows y macOS. Para
  programar, se usa `npx expo start --web` fuera de Docker.

### 8. Tests de integración contra una base real

- **Diferencia con ADR-003:** en lugar de probar los casos de uso con repositorios mock, se prueba la API completa
  contra una base `postgrado_test` que se crea y migra desde cero en cada corrida.
- **Motivo:** con poco tiempo, cada test cubre router + caso de uso + repositorio + SQL real, y además verifica las
  migraciones. El dominio sigue teniendo tests unitarios puros, como pide ADR-003.

## Consecuencias

### Consecuencias Positivas

- El sistema completo se levanta con `docker compose up -d --build` en cualquier sistema operativo.
- Las reglas del SRS que antes faltaban (formato del legajo, motivación mínima, documentos, emails, vencimiento
  automático, exportación) quedan implementadas y con tests.
- Cobertura del 93 % y CI con E2E: un cambio que rompa el flujo principal se detecta en el Pull Request.

### Consecuencias Negativas

- El link del aspirante es la única forma de entrar a su trámite: si pierde el email, necesita ayuda de la Secretaría
  (no hay "recuperar link").
- El número de cohorte depende del orden de creación: si se borra una cohorte de un año, los números de las
  siguientes cambian para los legajos que se aprueben después.
- Los tests de integración necesitan Postgres (en Docker o en el CI); solo los unitarios corren sin nada.