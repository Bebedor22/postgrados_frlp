/**
 * Ayudas para los documentos PDF del legajo (RF-CORE-002).
 *
 * - Antes de subir se controla el archivo en el navegador, con los mismos
 *   mensajes que pide el SRS ("rechaza ANTES de transferir"). El backend vuelve
 *   a validar siempre: esto es solo para avisar rápido.
 * - Elegir archivos y abrir PDFs usa APIs del navegador: el wizard es web.
 */
import {Platform} from "react-native";

export const TAMANIO_MAXIMO_MB = 5;
const TAMANIO_MAXIMO_BYTES = TAMANIO_MAXIMO_MB * 1024 * 1024;

export const esWeb = Platform.OS === "web" && typeof document !== "undefined";

/** Devuelve el mensaje de error, o null si el archivo se puede subir. */
export function validarArchivoPdf(archivo: {name: string; type: string; size: number}): string | null {
    const esPdf = archivo.type === "application/pdf" || archivo.name.toLowerCase().endsWith(".pdf");
    if (!esPdf) return "Solo se aceptan archivos en formato PDF";
    if (archivo.size > TAMANIO_MAXIMO_BYTES) {
        return `El archivo es demasiado grande. Máximo permitido: ${TAMANIO_MAXIMO_MB}MB`;
    }
    if (archivo.size === 0) return "El archivo está vacío";
    return null;
}

/** Abre el selector de archivos del sistema y devuelve el PDF elegido (o null si cancela). */
export function elegirArchivoPdf(): Promise<File | null> {
    return new Promise((resolver) => {
        if (!esWeb) {
            resolver(null);
            return;
        }
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "application/pdf,.pdf";
        input.onchange = () => resolver(input.files?.[0] ?? null);
        input.click();
    });
}

/** 1536 → "1,5 KB" */
export function formatearTamanio(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toLocaleString("es-AR", {maximumFractionDigits: 1})} KB`;
    return `${(bytes / 1024 / 1024).toLocaleString("es-AR", {maximumFractionDigits: 1})} MB`;
}

/** Abre una URL (o un PDF ya descargado) en otra pestaña. */
export function abrirEnPestania(url: string): void {
    if (esWeb) window.open(url, "_blank", "noopener");
}

/**
 * Para PDFs que se descargan con el token de sesión: la pestaña se abre en el
 * mismo clic (si se abre después de esperar al servidor, el navegador la bloquea)
 * y se carga cuando llega el archivo.
 */
export async function abrirPdfDescargado(descargar: () => Promise<Blob>): Promise<void> {
    if (!esWeb) return;
    const pestania = window.open("", "_blank");
    try {
        const pdf = await descargar();
        const url = URL.createObjectURL(pdf);
        if (pestania) pestania.location.href = url;
        else window.open(url, "_blank");
    } catch (e) {
        pestania?.close();
        throw e;
    }
}