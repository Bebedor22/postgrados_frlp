/**
 * Flujo principal del Core, de punta a punta y por pantalla (como en la demo):
 *
 *   coordinación entra → aspirante se inscribe con sus PDFs → coordinación observa →
 *   aspirante corrige y reenvía → coordinación aprueba y matricula → el aspirante
 *   es estudiante activo → Dirección solo mira → con la inscripción cerrada no se
 *   puede inscribir nadie (BR-009).
 *
 * Usa dos navegadores separados (dos "contextos"): uno para la coordinación y otro
 * para el aspirante, igual que la ventana normal y la de incógnito de la demo.
 */
import {expect, test, type Browser, type Page} from "@playwright/test";

const API = process.env.E2E_API_URL ?? "http://localhost:8000/api/v1";
const DNI = String(30_000_000 + Math.floor(Math.random() * 9_000_000)); // Uno nuevo en cada corrida
const OBSERVACION = "Revisá el año de graduación: el título dice 2018.";
const PDF = Buffer.from(
    "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n" +
    "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n",
);

/** Expo Router deja montadas las pantallas anteriores (ocultas): se busca solo entre lo visible. */
const texto = (pagina: Page, t: string | RegExp) =>
    pagina.getByText(t, {exact: typeof t === "string"}).filter({visible: true}).first();
const campo = (pagina: Page, placeholder: string | RegExp) =>
    pagina.getByPlaceholder(placeholder, {exact: typeof placeholder === "string"}).filter({visible: true}).first();

async function login(navegador: Browser, email: string, contrasena: string): Promise<Page> {
    const pagina = await (await navegador.newContext()).newPage();
    await pagina.goto("/login");
    await campo(pagina, "usuario@facultad.edu.ar").fill(email);
    await campo(pagina, "••••••••").fill(contrasena);
    await texto(pagina, "Ingresar").click();
    await expect(pagina).toHaveURL(/\/conduccion/);
    return pagina;
}

async function abrirLegajo(pagina: Page, busqueda: string) {
    await pagina.goto("/conduccion");
    await campo(pagina, /Buscar por apellido/).fill(busqueda);
    // La búsqueda se aplica al dejar de escribir: se espera a que quede un solo resultado
    await expect(texto(pagina, /^1 legajo · /)).toBeVisible();
    await texto(pagina, "Prueba E2E, Lucía").click();
    await expect(pagina).toHaveURL(/\/conduccion\/legajo\//);
}

test.describe.serial("Flujo principal del Core", () => {
    let coordinacion: Page;
    let aspirante: Page;
    let linkTramite: string;

    test.beforeAll(async ({browser}) => {
        aspirante = await (await browser.newContext()).newPage();
    });

    test.afterAll(async ({playwright}) => {
        // Pase lo que pase, la inscripción de la cohorte queda abierta como la dejó el seed
        const api = await playwright.request.newContext();
        const login = await api.post(`${API}/auth/login`, {data: {email: "admin@fenix.test", password: "Admin1234!"}});
        const headers = {Authorization: `Bearer ${(await login.json()).access_token}`};
        const cohortes = await (await api.get(`${API}/cohortes/`)).json();
        const cohorte = cohortes.find((c: {nombre: string}) => c.nombre === "Cohorte 2027");
        if (cohorte && !cohorte.inscripcion_abierta) {
            await api.patch(`${API}/cohortes/${cohorte.id}/inscripcion`, {data: {abierta: true}, headers});
        }
        await api.dispose();
    });

    test("1. La coordinación entra al portal de conducción", async ({browser}) => {
        coordinacion = await login(browser, "admin@fenix.test", "Admin1234!");
        await expect(texto(coordinacion, /^Inscripción abierta/)).toBeVisible();
    });

    test("2. El aspirante se inscribe en 4 pasos y adjunta sus PDFs", async () => {
        const p = aspirante;
        await p.goto("/wizard/inicio");
        await texto(p, "Maestría en Ingeniería en Sistemas de Información").click();
        await campo(p, "Ej.: 12345678").fill(DNI);
        await campo(p, "Ej.: nombre@email.com").fill("lucia.e2e@mail.com");
        await campo(p, "Ej.: Juan").fill("Lucía");
        await campo(p, "Ej.: Pérez").fill("Prueba E2E");
        await texto(p, "Comenzar ›").click();

        // Paso 1: no deja avanzar sin los obligatorios
        await texto(p, "Siguiente ›").click();
        await expect(texto(p, "Revisá los campos marcados en rojo para poder continuar.")).toBeVisible();
        await campo(p, "Ej.: Argentina").fill("Argentina");
        await campo(p, "DD/MM/AAAA").pressSequentially("15061995");
        await texto(p, "Siguiente ›").click();

        // Paso 2
        await campo(p, "Ej.: +54 9 221 123-4567").fill("221 555-1234");
        await campo(p, "Ej.: Argentina").fill("Argentina");
        await campo(p, "Ej.: Buenos Aires").fill("Buenos Aires");
        await campo(p, "Ej.: La Plata").fill("La Plata");
        await campo(p, "Ej.: Av. 7").fill("Calle 60");
        await campo(p, "Ej.: 1234").fill("1234");
        await campo(p, "Ej.: 1900").fill("1900");
        await texto(p, "Siguiente ›").click();

        // Paso 3: la motivación pide al menos 50 caracteres
        await campo(p, "Ej.: Lic. en Sociología").fill("Ingeniería en Sistemas");
        await campo(p, "Ej.: Universidad Nacional de La Plata").fill("UTN FRLP");
        await campo(p, "Ej.: 2019").fill("2019");
        await texto(p, "Egresados de la UTN FRLP").click();
        const motivacion = campo(p, "Contanos tus motivaciones y qué esperás de la carrera...");
        await motivacion.fill("Me interesa.");
        await texto(p, "Siguiente ›").click();
        await expect(texto(p, "Escribí al menos 50 caracteres")).toBeVisible();
        await motivacion.fill("Quiero especializarme en arquitectura de software y aplicarlo en mi trabajo.");
        await texto(p, "Siguiente ›").click();

        // Paso 4: sin documentos no deja enviar (RF-CORE-002)
        await expect(texto(p, "Documentación y Archivos")).toBeVisible();
        await texto(p, "Enviar Inscripción ✓").click();
        await expect(texto(p, "Falta adjuntar este documento")).toBeVisible();

        // Un archivo que no es PDF se rechaza antes de subirlo
        const elegir = async (archivo: {name: string; mimeType: string; buffer: Buffer}) => {
            const [selector] = await Promise.all([
                p.waitForEvent("filechooser"),
                texto(p, "Seleccionar PDF").click(),
            ]);
            await selector.setFiles(archivo);
        };
        await elegir({name: "foto.jpg", mimeType: "image/jpeg", buffer: Buffer.from("no es un pdf")});
        await expect(texto(p, "Solo se aceptan archivos en formato PDF")).toBeVisible();

        // Los 5 obligatorios: el primer "Seleccionar PDF" es siempre el primero que falta
        for (let i = 0; i < 5; i++) {
            const subidos = await p.getByText(/^✓ /).filter({visible: true}).count();
            await elegir({name: `documento-${i + 1}.pdf`, mimeType: "application/pdf", buffer: PDF});
            await expect(p.getByText(/^✓ /).filter({visible: true})).toHaveCount(subidos + 1);
        }

        await texto(p, "Enviar Inscripción ✓").click();
        await expect(p).toHaveURL(/\/tramite\//);
        await expect(texto(p, "Enviada, pendiente de revisión")).toBeVisible();
        linkTramite = p.url();
    });

    test("3. La coordinación lo toma para revisión y lo observa", async () => {
        const p = coordinacion;
        await abrirLegajo(p, DNI);
        // Los PDFs que subió el aspirante aparecen en la tarjeta Documentación
        await expect(p.getByText(/^✓ documento-1\.pdf/).filter({visible: true})).toBeVisible();
        await texto(p, "Tomar para revisión").click();
        await expect(texto(p, "En revisión")).toBeVisible();
        await texto(p, "Observar").click();
        await campo(p, "Ej.: Falta adjuntar la copia del título de grado").fill(OBSERVACION);
        await texto(p, "Enviar observación").click();
        await expect(texto(p, "Observada: requiere correcciones")).toBeVisible();
    });

    test("4. El aspirante ve la observación, corrige y reenvía", async () => {
        const p = aspirante;
        await p.goto(linkTramite);
        await expect(texto(p, OBSERVACION)).toBeVisible();
        await texto(p, "Corregir y reenviar ›").click();
        await expect(texto(p, "Enviar Inscripción ✓")).toBeVisible();
        await texto(p, "Enviar Inscripción ✓").click();
        await expect(p).toHaveURL(/\/tramite\//);
        await expect(texto(p, "Enviada, pendiente de revisión")).toBeVisible();
    });

    test("5. La coordinación lo aprueba (N° de legajo del SRS) y lo matricula", async () => {
        const p = coordinacion;
        await abrirLegajo(p, DNI);
        await texto(p, "Tomar para revisión").click();
        await texto(p, "Aprobar").click();
        await expect(texto(p, /Número de legajo asignado: \d{2}-\d{3}-\d{3}/)).toBeVisible();
        await texto(p, "Matricular").click();
        await expect(texto(p, "Estudiante activo")).toBeVisible();
    });

    test("6. El aspirante ve que ya es estudiante activo", async () => {
        await aspirante.goto(linkTramite);
        await expect(texto(aspirante, "Estudiante activo")).toBeVisible();
    });

    test("7. La Dirección ve los legajos pero no puede cambiarlos", async ({browser}) => {
        const p = await login(browser, "direccion@fenix.test", "Direccion1234!");
        await expect(texto(p, "Solo la coordinación abre o cierra la inscripción.")).toBeVisible();
        await abrirLegajo(p, DNI);
        await expect(texto(p, "Vista de solo lectura (Dirección de Posgrado).")).toBeVisible();
        await expect(texto(p, "Dar de baja")).toBeHidden();
    });

    test("8. Con la inscripción cerrada no se puede inscribir nadie (BR-009)", async () => {
        await coordinacion.goto("/conduccion");
        await texto(coordinacion, "Cerrar inscripción").click();
        await expect(texto(coordinacion, "Abrir inscripción")).toBeVisible();

        await aspirante.goto("/wizard/inicio");
        await expect(texto(aspirante, "Inscripción no disponible")).toBeVisible();

        await texto(coordinacion, "Abrir inscripción").click();
        await expect(texto(coordinacion, "Cerrar inscripción")).toBeVisible();
    });
});