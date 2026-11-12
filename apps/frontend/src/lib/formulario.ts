/** Datos del formulario de inscripción que comparten el wizard y la pantalla de trámite. */

/** Nombre legible de cada campo (para los mensajes de "faltan completar"). */
export const ETIQUETAS: Record<string, string> = {
    nombre: "Nombre",
    apellido: "Apellido",
    tipo_documento: "Tipo de documento",
    numero_documento: "Documento",
    nacionalidad: "Nacionalidad",
    fecha_nacimiento: "Fecha de nacimiento",
    email: "Correo electrónico",
    telefono_movil: "Teléfono celular",
    calle: "Calle",
    numero: "Número",
    codigo_postal: "Código postal",
    ciudad: "Localidad",
    provincia: "Provincia",
    pais: "País",
    titulo_grado: "Título de grado",
    institucion_grado: "Institución",
    anio_graduacion: "Año de graduación",
    como_conocio: "Cómo conoció la oferta",
    como_conocio_detalle: "Detalle de cómo conoció la oferta",
    motivacion: "Motivación (mínimo 50 caracteres)",
    tipo_beca: "Tipo de beca",
};

export const NOMBRES_DE_PASO: Record<string, string> = {
    "1": "Datos personales",
    "2": "Contacto y residencia",
    "3": "Antecedentes y motivaciones",
    "4": "Documentación y beca",
};

export const OPCIONES_COMO_CONOCIO = [
    {valor: "SITIO_WEB", texto: "Sitio web de la facultad"},
    {valor: "OTROS_SITIOS_WEB", texto: "Otros sitios web"},
    {valor: "EGRESADOS_UTN", texto: "Egresados de la UTN FRLP"},
    {valor: "COLEGAS", texto: "Comentarios de colegas"},
    {valor: "OTROS", texto: "Otros"},
];

export const ESTADOS: Record<string, {texto: string; color: string; fondo: string}> = {
    BORRADOR: {texto: "Borrador", color: "#374151", fondo: "#f3f4f6"},
    PENDIENTE: {texto: "Enviada, pendiente de revisión", color: "#1d4ed8", fondo: "#eff6ff"},
    EN_REVISION: {texto: "En revisión", color: "#7c3aed", fondo: "#f5f3ff"},
    OBSERVADO: {texto: "Observada: requiere correcciones", color: "#b45309", fondo: "#fffbeb"},
    COMPLETADO: {texto: "Aprobada", color: "#047857", fondo: "#ecfdf5"},
    ACTIVO: {texto: "Estudiante activo", color: "#047857", fondo: "#ecfdf5"},
    RECHAZADO: {texto: "Rechazada", color: "#b91c1c", fondo: "#fef2f2"},
    VENCIDO: {texto: "Reserva de vacante vencida", color: "#b91c1c", fondo: "#fef2f2"},
    BAJA: {texto: "Baja", color: "#6b7280", fondo: "#f3f4f6"},
    GRADUADO: {texto: "Graduado", color: "#047857", fondo: "#ecfdf5"},
};

/** "15/06/1995" → "1995-06-15" (null si está vacía, undefined si es inválida). */
export function fechaAIso(texto: string): string | null | undefined {
    const limpio = texto.trim();
    if (!limpio) return null;
    const partes = limpio.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (!partes) return undefined;
    const [, d, m, a] = partes;
    return `${a}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
}

/** "1995-06-15" → "15/06/1995" */
export function isoAFecha(iso: unknown): string {
    if (typeof iso !== "string" || !iso) return "";
    const [a, m, d] = iso.split("-");
    return `${d}/${m}/${a}`;
}

/** Lista "Paso X: campo, campo" con lo que falta completar. */
export function describirFaltantes(faltantes: Record<string, string[]>): string[] {
    return Object.entries(faltantes)
        .filter(([, campos]) => campos.length > 0)
        .map(([paso, campos]) => `${NOMBRES_DE_PASO[paso]}: ${campos.map((c) => ETIQUETAS[c] ?? c).join(", ")}`);
}