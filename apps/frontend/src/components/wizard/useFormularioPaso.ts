/**
 * Lógica compartida por los 4 pasos del wizard ("cargar y guardar").
 *
 * - Al abrir el paso trae del backend lo que el aspirante ya guardó.
 * - Cada input queda conectado a `valores`.
 * - `guardarYSeguir` manda solo los campos del paso (PATCH) y navega al siguiente.
 */
import {useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {ApiError, Tramite, consultarTramite, guardarProgreso} from "../../lib/api";
import {obtenerTokenTramite} from "../../lib/sesion";

export type Valores = Record<string, string | number | boolean | null>;

export function useFormularioPaso() {
    const router = useRouter();
    const [token] = useState(() => obtenerTokenTramite());
    const [tramite, setTramite] = useState<Tramite | null>(null);
    const [valores, setValores] = useState<Valores>({});
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

    /** Para un TextInput: value + onChangeText. */
    const campo = (nombre: string) => ({
        value: valores[nombre] == null ? "" : String(valores[nombre]),
        onChangeText: (texto: string) => setValores((v) => ({...v, [nombre]: texto})),
    });

    const set = (nombre: string, valor: string | number | boolean | null) =>
        setValores((v) => ({...v, [nombre]: valor}));

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

    return {token, tramite, valores, campo, set, error, setError, guardando, setGuardando, guardarYSeguir};
}