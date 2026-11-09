/**
 * Cliente de la API del backend (FastAPI).
 *
 * La URL base sale de EXPO_PUBLIC_API_URL (ver .env.example de la raíz) y por
 * defecto apunta al backend de Docker en localhost:8000.
 */
import {obtenerTokenSesion} from "./sesion";

export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
    }
}

/** Convierte el "detail" de FastAPI (texto o lista de errores de validación) en un mensaje legible. */
function mensajeDeError(detail: unknown, status: number): string {
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
        return detail
            .map((e: { loc?: (string | number)[]; msg?: string }) => {
                const campo = e.loc?.[e.loc.length - 1];
                return campo ? `${campo}: ${e.msg}` : e.msg;
            })
            .join(" · ");
    }
    return `Error ${status}`;
}

async function pedir<T>(ruta: string, opciones: RequestInit = {}, conSesion = false): Promise<T> {
    const headers: Record<string, string> = {"Content-Type": "application/json"};
    if (conSesion) {
        const token = obtenerTokenSesion();
        if (token) headers.Authorization = `Bearer ${token}`;
    }
    let respuesta: Response;
    try {
        respuesta = await fetch(`${API_URL}${ruta}`, {...opciones, headers: {...headers, ...opciones.headers}});
    } catch {
        throw new ApiError(0, "No se pudo conectar con el servidor. ¿Está levantado el backend (docker compose up)?");
    }
    const cuerpo = respuesta.status === 204 ? null : await respuesta.json().catch(() => null);
    if (!respuesta.ok) {
        throw new ApiError(respuesta.status, mensajeDeError(cuerpo?.detail, respuesta.status));
    }
    return cuerpo as T;
}

// ── Tipos ────────────────────────────────────────────────────────────────────

export type Rol = "ASPIRANTE" | "DOCENTE" | "COORDINADOR" | "CPR" | "DIRECCION" | "ADMIN";

export interface Usuario {
    id: string;
    email: string;
    nombre: string;
    rol: Rol;
}

export interface Carrera {
    id: string;
    nombre: string;
    tipo: "Especializacion" | "Maestria" | "Doctorado";
    duracion_anios: number;
    activa: boolean;
}

export interface Cohorte {
    id: string;
    anio: number;
    nombre: string;
    inscripcion_abierta: boolean;
    fecha_inicio: string | null;
}

export interface CambioDeEstado {
    estado_anterior: string | null;
    estado_nuevo: string;
    comentario: string | null;
    fecha: string;
}

export interface Tramite {
    legajo_id: string;
    numero_legajo: string;
    estado: string;
    puede_editar: boolean;
    cohorte_id: string;
    carrera_id: string | null;
    datos: Record<string, string | number | boolean | null>;
    progreso: {porcentaje: number; completo: boolean; faltantes_por_paso: Record<string, string[]>};
    historial: CambioDeEstado[];
}

export interface InicioInscripcion {
    cohorte_id: string;
    carrera_id: string;
    tipo_documento: "DNI" | "PASAPORTE";
    numero_documento: string;
    nombre: string;
    apellido: string;
    email: string;
}

// ── Autenticación ────────────────────────────────────────────────────────────

export const login = (email: string, password: string) =>
    pedir<{access_token: string; expires_in: number; usuario: Usuario}>("/auth/login", {
        method: "POST",
        body: JSON.stringify({email, password}),
    });

// ── Oferta académica (pública) ───────────────────────────────────────────────

export const listarCarreras = () => pedir<Carrera[]>("/carreras/");
export const listarCohortesAbiertas = () => pedir<Cohorte[]>("/cohortes/?solo_abiertas=true");

// ── Inscripción del aspirante (pública, con el token del trámite) ────────────

export const iniciarInscripcion = (datos: InicioInscripcion) =>
    pedir<{legajo_id: string; estado: string; token: string; link_seguimiento: string}>("/inscripciones/", {
        method: "POST",
        body: JSON.stringify(datos),
    });

export const consultarTramite = (token: string) => pedir<Tramite>(`/inscripciones/${token}`);

export const guardarProgreso = (token: string, cambios: Record<string, unknown>) =>
    pedir<Tramite>(`/inscripciones/${token}`, {method: "PATCH", body: JSON.stringify(cambios)});

export const confirmarInscripcion = (token: string) =>
    pedir<Tramite>(`/inscripciones/${token}/confirmar`, {method: "POST"});