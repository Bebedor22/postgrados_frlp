/**
 * Cliente de la API del backend (FastAPI).
 *
 * La URL base sale de EXPO_PUBLIC_API_URL (ver .env.example de la raíz) y por
 * defecto apunta al backend de Docker en localhost:8000.
 */
import {cerrarSesion, obtenerTokenSesion} from "./sesion";

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
    // Con FormData (subida de archivos) el navegador arma el Content-Type con su "boundary"
    const headers: Record<string, string> = opciones.body instanceof FormData ? {} : {"Content-Type": "application/json"};
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
        // Token vencido o inválido: se cierra la sesión para que la pantalla mande al login
        if (conSesion && respuesta.status === 401) cerrarSesion();
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

export interface DocumentoSubido {
    id: string;
    tipo: string;
    descripcion: string;
    nombre_original: string;
    tamanio_bytes: number;
    checksum_sha256: string;
    fecha_subida: string | null;
}

/** Un documento que pide el legajo (RF-CORE-002) y, si ya se subió, sus datos. */
export interface RequisitoDocumental {
    tipo: string;
    descripcion: string;
    obligatorio: boolean;
    presentado: boolean;
    documento: DocumentoSubido | null;
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
    documentos: RequisitoDocumental[];
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

// ── Documentos del aspirante (con el token del trámite) ──────────────────────

export function subirDocumento(token: string, tipo: string, archivo: Blob, nombre: string) {
    const formulario = new FormData();
    formulario.append("tipo", tipo);
    formulario.append("archivo", archivo, nombre);
    return pedir<DocumentoSubido>(`/inscripciones/${token}/documentos`, {method: "POST", body: formulario});
}

export const eliminarDocumento = (token: string, documentoId: string) =>
    pedir<null>(`/inscripciones/${token}/documentos/${documentoId}`, {method: "DELETE"});

/** El link del aspirante sirve de permiso: el PDF se puede abrir directo en otra pestaña. */
export const urlDocumentoPropio = (token: string, documentoId: string) =>
    `${API_URL}/inscripciones/${token}/documentos/${documentoId}/descarga`;

// ── Conducción: cohortes y bandeja de legajos (requieren login) ──────────────

export const listarCohortes = () => pedir<Cohorte[]>("/cohortes/");

export const cambiarInscripcionCohorte = (cohorteId: string, abierta: boolean) =>
    pedir<Cohorte>(`/cohortes/${cohorteId}/inscripcion`, {method: "PATCH", body: JSON.stringify({abierta})}, true);

export interface LegajoFila {
    id: string;
    numero_legajo: string;
    apellido: string;
    nombre: string;
    tipo_documento: string;
    documento: string;
    email: string;
    carrera_id: string | null;
    carrera: string | null;
    estado: string;
    solicita_beca: boolean;
    tipo_beca: string | null;
    fecha_inscripcion: string | null;
}

export interface FiltrosLegajos {
    cohorte_id?: string;
    estado?: string;
    buscar?: string;
    pagina?: number;
    por_pagina?: number;
}

function aQuery(filtros: Record<string, string | number | undefined>): string {
    const partes = Object.entries(filtros)
        .filter(([, v]) => v !== undefined && v !== "")
        .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`);
    return partes.length ? `?${partes.join("&")}` : "";
}

export const listarLegajos = (filtros: FiltrosLegajos) =>
    pedir<{total: number; pagina: number; por_pagina: number; legajos: LegajoFila[]}>(
        `/legajos/${aQuery({...filtros})}`, {}, true,
    );

export const resumenLegajos = (cohorteId?: string) =>
    pedir<Record<string, number>>(`/legajos/resumen${aQuery({cohorte_id: cohorteId})}`, {}, true);

export type DetalleLegajo = Tramite & {reserva_vence_el: string | null};

export const detalleLegajo = (id: string) => pedir<DetalleLegajo>(`/legajos/${id}`, {}, true);

/** Trae un PDF con el token de sesión (la conducción no puede abrir el link directo). */
export async function descargarDocumento(documentoId: string): Promise<Blob> {
    let respuesta: Response;
    try {
        respuesta = await fetch(`${API_URL}/documentos/${documentoId}/download`, {
            headers: {Authorization: `Bearer ${obtenerTokenSesion() ?? ""}`},
        });
    } catch {
        throw new ApiError(0, "No se pudo conectar con el servidor.");
    }
    if (!respuesta.ok) {
        if (respuesta.status === 401) cerrarSesion();
        const cuerpo = await respuesta.json().catch(() => null);
        throw new ApiError(respuesta.status, mensajeDeError(cuerpo?.detail, respuesta.status));
    }
    return respuesta.blob();
}

export type AccionLegajo = "revisar" | "observar" | "aprobar" | "rechazar" | "matricular";

/** Cambia el estado de un legajo. "observar" pide comentario y "rechazar" pide motivo. */
export function accionLegajo(id: string, accion: AccionLegajo, texto?: string) {
    const cuerpo =
        accion === "observar" ? {comentario: texto} : accion === "rechazar" ? {motivo: texto} : undefined;
    return pedir<{legajo_id: string; numero_legajo: string; estado: string}>(
        `/legajos/${id}/${accion}`,
        {method: "POST", body: cuerpo ? JSON.stringify(cuerpo) : undefined},
        true,
    );
}