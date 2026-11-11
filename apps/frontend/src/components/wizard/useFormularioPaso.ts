/**
 * Lógica compartida por los 4 pasos del wizard ("cargar y guardar").
 *
 * - Al abrir el paso trae del backend lo que el aspirante ya guardó.
 * - Cada input queda conectado a `valores` (y a su mensaje de error).
 * - `validarPaso` marca en rojo los obligatorios vacíos o mal escritos.
 * - `guardarYSeguir` manda los campos del paso (PATCH) y navega.
 * - `recargar` vuelve a traer el trámite (por ejemplo, después de subir un PDF).
 */
import {useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {ApiError, Tramite, consultarTramite, guardarProgreso} from "../../lib/api";
import {obtenerTokenTramite} from "../../lib/sesion";
import {Errores, Regla, hayErrores, validar} from "../../lib/validaciones";

export type Valores = Record<string, string | number | boolean | null>;

export function useFormularioPaso() {
    const router = useRouter();
    const [token] = useState(() => obtenerTokenTramite());
    const [tramite, setTramite] = useState<Tramite | null>(null);
    const [valores, setValores] = useState<Valores>({});
    const [errores, setErrores] = useState<Errores>({});
    const [error, setError] = useState<string | null>(null);
    const [guardando, setGuardando] = useState(false);

    useEffect(() => {
        if (!token) {
            router.replace("/wizard/inicio");
            return;
        }
        consultarTramite(token)
            .then((t) => {
                if (!t.puede_editar) {
                    router.replace(`/tramite/${token}`);
                    return;
                }
                setTramite(t);
                setValores(t.datos);
            })
            .catch((e: ApiError) => setError(e.message));
    }, [token]);

    /** Al corregir un campo se borra su error. */
    const set = (nombre: string, valor: string | number | boolean | null) => {
        setValores((v) => ({...v, [nombre]: valor}));
        setErrores(({[nombre]: _, ...resto}) => resto);
    };

    /** Para un CampoTexto: value + onChangeText + error. */
    const campo = (nombre: string, transformar?: (texto: string) => string) => ({
        value: valores[nombre] == null ? "" : String(valores[nombre]),
        onChangeText: (texto: string) => set(nombre, transformar ? transformar(texto) : texto),
        error: errores[nombre],
    });

    /** Valida el paso; si algo falla lo marca y devuelve false. */
    function validarPaso(reglas: Record<string, Regla[]>, extra: Valores = {}): boolean {
        const encontrados = validar({...valores, ...extra}, reglas);
        setErrores(encontrados);
        if (hayErrores(encontrados)) {
            setError("Revisá los campos marcados en rojo para poder continuar.");
            return false;
        }
        setError(null);
        return true;
    }

    /** Guarda los cambios del paso. Si `destino` está, navega después. */
    async function guardarYSeguir(cambios: Valores, destino?: string): Promise<Tramite | null> {
        if (!token) return null;
        setGuardando(true);
        setError(null);
        try {
            // Un texto vacío se guarda como "sin completar"
            const limpios = Object.fromEntries(
                Object.entries(cambios).map(([k, v]) => [k, typeof v === "string" && v.trim() === "" ? null : v]),
            );
            const actualizado = await guardarProgreso(token, limpios);
            setTramite(actualizado);
            if (destino) router.push(destino as never);
            return actualizado;
        } catch (e) {
            setError((e as ApiError).message);
            return null;
        } finally {
            setGuardando(false);
        }
    }

    /** Vuelve a pedir el trámite al backend (sin tocar lo que se está escribiendo). */
    async function recargar(): Promise<Tramite | null> {
        if (!token) return null;
        const actualizado = await consultarTramite(token);
        setTramite(actualizado);
        return actualizado;
    }

    return {
        token, tramite, valores, campo, set, errores, error, setError,
        guardando, setGuardando, validarPaso, guardarYSeguir, recargar,
    };
}