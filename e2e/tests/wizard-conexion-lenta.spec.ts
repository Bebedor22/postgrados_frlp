/**
 * Con una conexión lenta, los datos guardados del trámite llegan después de que la
 * persona empezó a escribir: lo que escribió no se tiene que borrar.
 */
import {expect, test} from "@playwright/test";

const API = process.env.E2E_API_URL ?? "http://localhost:8000/api/v1";

test("Con la conexión lenta no se pierde lo que se escribe en el paso 3", async ({page}) => {
    // Una inscripción nueva, recién empezada (BORRADOR)
    const cohortes = await (await page.request.get(`${API}/cohortes/`)).json();
    const cohorte = cohortes.find((c: {inscripcion_abierta: boolean}) => c.inscripcion_abierta);
    const carreras = await (await page.request.get(`${API}/carreras/`)).json();
    const r = await page.request.post(`${API}/inscripciones/`, {
        data: {
            cohorte_id: cohorte.id, carrera_id: carreras[0].id, tipo_documento: "DNI",
            numero_documento: String(40_000_000 + Math.floor(Math.random() * 9_000_000)),
            nombre: "Lenta", apellido: "Conexión", email: "lenta@mail.com",
        },
    });
    const {token} = await r.json();
    await page.goto("/wizard/inicio");
    await page.evaluate((t) => localStorage.setItem("posgrado.tramite", t), token);

    // El trámite tarda 2 segundos en llegar
    await page.route(/\/inscripciones\/[^/]+$/, async (ruta) => {
        if (ruta.request().method() === "GET") await new Promise((listo) => setTimeout(listo, 2000));
        await ruta.continue();
    });

    await page.goto("/wizard/step-3");
    const titulo = page.getByPlaceholder("Ej.: Lic. en Sociología").filter({visible: true}).first();
    await titulo.fill("Ingeniería en Sistemas");
    await page.waitForTimeout(3000); // ya llegaron los datos guardados
    await expect(titulo).toHaveValue("Ingeniería en Sistemas");
});