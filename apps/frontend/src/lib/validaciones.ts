/**
 * Validaciones del formulario del lado del navegador.
 *
 * Sirven para avisar al instante qué falta o qué está mal escrito. El backend
 * vuelve a validar todo: estas reglas son una ayuda para el usuario, no la
 * única barrera.
 */

export type Regla = "requerido" | "email" | "fecha" | "anio" | "telefono" | "dni" | "pasaporte" | "motivacion";

/** REQ-CORE-001: "Motivación (texto libre, mínimo 50 caracteres)". */
export const LARGO_MINIMO_MOTIVACION = 50;
export type Errores = Record<string, string>;

const MENSAJES: Record<Regla, string> = {
    requerido: "Este campo es obligatorio",
    email: "Ingresá un correo válido (ejemplo@email.com)",
    fecha: "Ingresá una fecha válida con el formato DD/MM/AAAA",
    anio: "Ingresá un año de 4 dígitos que no sea futuro",
    telefono: "Ingresá solo números, espacios, guiones o +",
    dni: "El DNI tiene 7 u 8 números, sin puntos",
    pasaporte: "El pasaporte tiene entre 6 y 12 letras o números",
    motivacion: `Escribí al menos ${LARGO_MINIMO_MOTIVACION} caracteres`,
};

function fechaValida(texto: string): boolean {
    const partes = texto.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!partes) return false;
    const [, d, m, a] = partes.map(Number);
    const fecha = new Date(a, m - 1, d);
    const esReal = fecha.getFullYear() === a && fecha.getMonth() === m - 1 && fecha.getDate() === d;
    return esReal && fecha < new Date() && a >= 1900;
}

const CUMPLE: Record<Exclude<Regla, "requerido">, (v: string) => boolean> = {
    email: (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v),
    fecha: fechaValida,
    anio: (v) => /^\d{4}$/.test(v) && Number(v) >= 1950 && Number(v) <= new Date().getFullYear(),
    telefono: (v) => /^[\d\s()+-]{6,}$/.test(v),
    dni: (v) => /^\d{7,8}$/.test(v),
    pasaporte: (v) => /^[A-Za-z0-9]{6,12}$/.test(v),
    motivacion: (v) => v.length >= LARGO_MINIMO_MOTIVACION,
};

/** Devuelve un mensaje por cada campo que no cumple sus reglas (vacío = todo bien). */
export function validar(valores: Record<string, unknown>, reglas: Record<string, Regla[]>): Errores {
    const errores: Errores = {};
    for (const [campo, reglasDelCampo] of Object.entries(reglas)) {
        const valor = valores[campo] == null ? "" : String(valores[campo]).trim();
        if (!valor) {
            if (reglasDelCampo.includes("requerido")) errores[campo] = MENSAJES.requerido;
            continue;
        }
        const falla = reglasDelCampo.find((r) => r !== "requerido" && !CUMPLE[r as Exclude<Regla, "requerido">](valor));
        if (falla) errores[campo] = MENSAJES[falla];
    }
    return errores;
}

export const hayErrores = (errores: Errores) => Object.keys(errores).length > 0;

/** Mientras se escribe: "15061995" → "15/06/1995". */
export function enmascararFecha(texto: string): string {
    const digitos = texto.replace(/\D/g, "").slice(0, 8);
    if (digitos.length <= 2) return digitos;
    if (digitos.length <= 4) return `${digitos.slice(0, 2)}/${digitos.slice(2)}`;
    return `${digitos.slice(0, 2)}/${digitos.slice(2, 4)}/${digitos.slice(4)}`;
}