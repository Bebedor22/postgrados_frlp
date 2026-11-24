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
    carrera_id?: string;
    tiene_beca?: boolean;
    estado?: string;
    buscar?: string;
    pagina?: number;
    por_pagina?: number;
}

function aQuery(filtros: Record<string, string | number | boolean | undefined>): string {
    const partes = Object.entries(filtros)
        .filter(([, v]) => v !== undefined && v !== "")
        .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`);
    return partes.length ? `?${partes.join("&")}` : "";
}

export const listarLegajos = (filtros: FiltrosLegajos) =>
    pedir<{total: number; pagina: number; por_pagina: number; legajos: LegajoFila[]}>(
        `/legajos/${aQuery({...filtros})}`, {}, true,
    );

/** Descarga en Excel los legajos que cumplen los filtros (sin paginar, máximo 500). */
export async function exportarLegajos(filtros: FiltrosLegajos): Promise<Blob> {
    const {pagina: _p, por_pagina: _pp, ...sinPaginar} = filtros;
    let respuesta: Response;
    try {
        respuesta = await fetch(`${API_URL}/legajos/exportar${aQuery({...sinPaginar})}`, {
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

export type AccionLegajo = "revisar" | "observar" | "aprobar" | "rechazar" | "matricular" | "baja" | "graduar";

/** Cambia el estado de un legajo. "observar" pide comentario; "rechazar" y "baja" piden motivo. */
export function accionLegajo(id: string, accion: AccionLegajo, texto?: string) {
    const cuerpo =
        accion === "observar" ? {comentario: texto}
            : accion === "rechazar" || accion === "baja" ? {motivo: texto}
                : undefined;
    return pedir<{legajo_id: string; numero_legajo: string; estado: string}>(
        `/legajos/${id}/${accion}`,
        {method: "POST", body: cuerpo ? JSON.stringify(cuerpo) : undefined},
        true,
    );
}

// ── Módulo B: seminarios, cursada y notas finales ───────────────────────────

export interface Seminario {
    id: string;
    carrera_id: string;
    nombre: string;
    codigo: string;
    horas_catedra: number;
    es_obligatorio: boolean;
    docente_email: string | null;
    fecha_limite_actas: string | null;
    actualizado_en: string | null;
}

export interface EstudianteSeminario {
    legajo_id: string;
    numero_legajo: string;
    apellido: string;
    nombre: string;
    email: string;
    nota_final: number | null;
    estado: "CURSANDO" | "APROBADO" | "DESAPROBADO";
}

export interface ProgresoSeminarios {
    obligatorios_total: number;
    aprobados: number;
    adeudados: number;
}

export interface NotaFinal {
    legajo_id: string;
    nota: number;
}

export interface FiltrosSeminarios {
    carrera_id?: string;
    solo_obligatorios?: boolean;
    docente_email?: string;
}

/** Un DOCENTE siempre recibe solo sus seminarios, aunque pida otro `docente_email`. */
export const listarSeminarios = (filtros: FiltrosSeminarios = {}) =>
    pedir<Seminario[]>(`/seminarios/${aQuery({...filtros})}`, {}, true);

export interface SeminarioCrear {
    carrera_id: string;
    nombre: string;
    codigo: string;
    horas_catedra: number;
    es_obligatorio?: boolean;
    docente_email?: string | null;
    fecha_limite_actas?: string | null;
}

export const crearSeminario = (datos: SeminarioCrear) =>
    pedir<Seminario>("/seminarios/", {method: "POST", body: JSON.stringify(datos)}, true);

export const obtenerSeminario = (id: string) => pedir<Seminario>(`/seminarios/${id}`, {}, true);

export const listarInscriptosSeminario = (id: string) =>
    pedir<EstudianteSeminario[]>(`/seminarios/${id}/estudiantes`, {}, true);

export const inscribirEnSeminario = (id: string, legajoId: string) =>
    pedir<{id: string; legajo_id: string; seminario_id: string; nota_final: number | null; estado: string}>(
        `/seminarios/${id}/estudiantes`, {method: "POST", body: JSON.stringify({legajo_id: legajoId})}, true,
    );

/** Nota >= 4 aprueba el seminario (BR-003). Si alguna falla, no se guarda ninguna. */
export const registrarNotasSeminario = (id: string, notas: NotaFinal[]) =>
    pedir<{id: string; legajo_id: string; nota_final: number | null; estado: string}[]>(
        `/seminarios/${id}/notas`, {method: "PATCH", body: JSON.stringify({notas})}, true,
    );

export const progresoSeminarios = (legajoId: string) =>
    pedir<ProgresoSeminarios>(`/seminarios/progreso?legajo_id=${encodeURIComponent(legajoId)}`, {}, true);

// ── Mi avance (aspirante, con el token del trámite) ──────────────────────────

export interface CursadaAlumno {
    seminario_id: string;
    codigo: string;
    nombre: string;
    horas_catedra: number;
    es_obligatorio: boolean;
    estado: EstudianteSeminario["estado"];
    nota_final: number | null;
}

export interface AvanceAlumno {
    legajo_id: string;
    numero_legajo: string;
    estado: string;
    progreso: ProgresoSeminarios;
    seminarios: CursadaAlumno[];
    semaforo: "VERDE" | "AMARILLO" | "ROJO";
    trabajo_final: {
        tipo: string;
        titulo: string;
        director_nombre: string;
        fecha_aprobacion_cpr: string | null;
    } | null;
}

/** Endpoint público: el token del link es la credencial, no hace falta sesión. */
export const avanceAlumno = (token: string) =>
    pedir<AvanceAlumno>(`/inscripciones/${encodeURIComponent(token)}/avance`);

// ── Módulo C: seguimiento de graduación ─────────────────────────────────────

export interface SemaforoFila {
    legajo_id: string;
    numero_legajo: string;
    apellido: string;
    nombre: string;
    carrera: string;
    tipo_carrera: string;
    fecha_inscripcion: string | null;
    semaforo: "VERDE" | "AMARILLO" | "ROJO";
    semaforo_manual: boolean;
    semaforo_desde: string | null;
    dias_en_riesgo: number;
    seminarios_obligatorios_total: number;
    seminarios_aprobados: number;
    seminarios_adeudados: number;
    tiene_tfi_registrado: boolean;
    tiene_fecha_cpr: boolean;
}

export interface EnRiesgoResponse {
    total: number;
    legajos: SemaforoFila[];
}

export interface TrabajoFinal {
    id: string;
    legajo_id: string;
    tipo: "TFI" | "TESIS";
    titulo: string;
    director_nombre: string;
    director_email: string;
    codirector_nombre: string | null;
    fecha_aprobacion_cpr: string | null;
    numero_resolucion: string | null;
    created_at: string | null;
    updated_at: string | null;
}

export interface TrabajoFinalDatos {
    tipo: "TFI" | "TESIS";
    titulo: string;
    director_nombre: string;
    director_email: string;
    codirector_nombre?: string | null;
    fecha_aprobacion_cpr?: string | null;
    numero_resolucion?: string | null;
    limpiar_fecha_cpr?: boolean;
}

export interface LegajoTesisItem {
    legajo_id: string;
    numero_legajo: string;
    apellido: string;
    nombre: string;
    carrera: string;
    estado: string;
    tiene_trabajo_final: boolean;
}

/** Color almacenado de todos los activos (ASR-003: el front nunca calcula el color). */
export const semaforoActivos = () => pedir<EnRiesgoResponse>("/graduacion/semaforo", {}, true);
export const legajosEnRiesgo = () => pedir<EnRiesgoResponse>("/graduacion/en-riesgo", {}, true);
export const semaforoDeLegajo = (legajoId: string) =>
    pedir<SemaforoFila>(`/legajos/${legajoId}/semaforo`, {}, true);

/** BR-008: `manual: true` fija VERDE; `false` restaura el cálculo automático. */
export const fijarSemaforo = (legajoId: string, manual: boolean) =>
    pedir<SemaforoFila>(
        `/legajos/${legajoId}/semaforo/verde`,
        {method: "PATCH", body: JSON.stringify({manual})},
        true,
    );

export const obtenerTrabajoFinal = (legajoId: string) =>
    pedir<TrabajoFinal>(`/legajos/${legajoId}/trabajo-final`, {}, true);

export const registrarTrabajoFinal = (legajoId: string, datos: TrabajoFinalDatos) =>
    pedir<TrabajoFinal>(
        `/legajos/${legajoId}/trabajo-final`, {method: "POST", body: JSON.stringify(datos)}, true,
    );

export const editarTrabajoFinal = (trabajoId: string, datos: TrabajoFinalDatos) =>
    pedir<TrabajoFinal>(
        `/trabajos-finales/${trabajoId}`, {method: "PATCH", body: JSON.stringify(datos)}, true,
    );

/** Búsqueda reducida para el CPR (BR-004), sin acceso a la bandeja completa. */
export const legajosParaTesis = (buscar: string = "") =>
    pedir<LegajoTesisItem[]>(`/tesis/legajos?buscar=${encodeURIComponent(buscar)}`, {}, true);

/** US-C-003: Excel con los legajos en ROJO, ordenados por criticidad. */
export async function exportarEnRiesgo(): Promise<Blob> {
    let respuesta: Response;
    try {
        respuesta = await fetch(`${API_URL}/graduacion/en-riesgo/exportar`, {
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

// ── Módulo D: analytics ──────────────────────────────────────────────────────

export type TipoCarreraFiltro = Carrera["tipo"];

export interface MetricasCohorte {
    cohorte_id: string;
    cohorte_nombre: string;
    cohorte_anio: number;
    inscriptos: number;
    activos: number;
    graduados: number;
    bajas: number;
    en_riesgo: number;
    retencion_pct: number;
    desgranamiento_pct: number;
    tiempo_promedio_graduacion_dias: number | null;
}

export interface Dashboard {
    total_inscriptos: number;
    activos: number;
    graduados: number;
    bajas: number;
    en_riesgo: number;
    retencion_pct: number;
    desgranamiento_pct: number;
    tiempo_promedio_graduacion_dias: number | null;
    por_estado: Record<string, number>;
    por_tipo_carrera: Record<string, number>;
    cohortes: MetricasCohorte[];
}

/** RF-REP-001: métricas globales y por cohorte; `tipo` filtra por tipo de carrera. */
export const obtenerDashboard = (tipo?: TipoCarreraFiltro) =>
    pedir<Dashboard>(`/analytics/dashboard${aQuery({tipo_carrera: tipo})}`, {}, true);

/** RF-REP-002: descarga el dashboard en Excel (con los mismos filtros que la pantalla). */
export async function exportarDashboard(tipo?: TipoCarreraFiltro): Promise<Blob> {
    let respuesta: Response;
    try {
        respuesta = await fetch(`${API_URL}/analytics/exportar${aQuery({tipo_carrera: tipo})}`, {
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
