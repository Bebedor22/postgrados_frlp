/**
 * Guarda la sesión del usuario (JWT) y el token del trámite del aspirante.
 *
 * En web usa localStorage, así un recargo de la página no pierde la sesión.
 * Si no está disponible (app nativa o navegador que lo bloquea) queda en memoria.
 */
import type {Usuario} from "./api";

const CLAVE_SESION = "posgrado.sesion";
const CLAVE_TRAMITE = "posgrado.tramite";
const memoria: Record<string, string> = {};

function leer(clave: string): string | null {
    try {
        if (typeof localStorage !== "undefined") return localStorage.getItem(clave);
    } catch {
        // localStorage bloqueado: se usa la memoria
    }
    return memoria[clave] ?? null;
}

function escribir(clave: string, valor: string | null): void {
    try {
        if (typeof localStorage !== "undefined") {
            if (valor === null) localStorage.removeItem(clave);
            else localStorage.setItem(clave, valor);
            return;
        }
    } catch {
        // localStorage bloqueado: se usa la memoria
    }
    if (valor === null) delete memoria[clave];
    else memoria[clave] = valor;
}

// ── Sesión de usuarios con login (coordinador, docente, Dirección, CPR) ─────

export function guardarSesion(token: string, usuario: Usuario): void {
    escribir(CLAVE_SESION, JSON.stringify({token, usuario}));
}

export function obtenerSesion(): {token: string; usuario: Usuario} | null {
    const texto = leer(CLAVE_SESION);
    if (!texto) return null;
    try {
        return JSON.parse(texto);
    } catch {
        return null;
    }
}

export const obtenerTokenSesion = () => obtenerSesion()?.token ?? null;

export function cerrarSesion(): void {
    escribir(CLAVE_SESION, null);
}

// ── Trámite del aspirante (sin login: lo identifica el token de su link) ────

export const guardarTokenTramite = (token: string) => escribir(CLAVE_TRAMITE, token);
export const obtenerTokenTramite = () => leer(CLAVE_TRAMITE);
export const olvidarTramite = () => escribir(CLAVE_TRAMITE, null);