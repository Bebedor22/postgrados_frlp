/**
 * Portal CPR (Módulo C, RF-GRAD-001): alta y edición de TFI/Tesis.
 * Al guardar con fecha de aprobación CPR y sin seminarios adeudados, el backend
 * gradúa el legajo automáticamente.
 */
import {useLocalSearchParams, useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {Pressable, Text, TextInput, View} from "react-native";
import {Boton, Tarjeta} from "../../../src/components/conduccion/PortalConduccion";
import {PortalCpr, useUsuarioCpr} from "../../../src/components/cpr/PortalCpr";
import {
    ApiError, TrabajoFinal, TrabajoFinalDatos, editarTrabajoFinal,
    obtenerTrabajoFinal, registrarTrabajoFinal,
} from "../../../src/lib/api";

type Formulario = {
    tipo: "TFI" | "TESIS";
    titulo: string;
    director_nombre: string;
    director_email: string;
    codirector_nombre: string;
    fecha_aprobacion_cpr: string;
    numero_resolucion: string;
};

const VACIO: Formulario = {
    tipo: "TFI", titulo: "", director_nombre: "", director_email: "",
    codirector_nombre: "", fecha_aprobacion_cpr: "", numero_resolucion: "",
};

export default function TrabajoFinalCprScreen() {
    const router = useRouter();
    const usuario = useUsuarioCpr();
    const {legajoId} = useLocalSearchParams<{legajoId: string}>();
    const [actual, setActual] = useState<TrabajoFinal | null>(null);
    const [formulario, setFormulario] = useState<Formulario>(VACIO);
    const [limpiarFecha, setLimpiarFecha] = useState(false);
    const [cargando, setCargando] = useState(true);
    const [guardando, setGuardando] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [aviso, setAviso] = useState<string | null>(null);

    useEffect(() => {
        if (!usuario || !legajoId) return;
        obtenerTrabajoFinal(legajoId)
            .then((trabajo) => {
                setActual(trabajo);
                setFormulario({
                    tipo: trabajo.tipo,
                    titulo: trabajo.titulo,
                    director_nombre: trabajo.director_nombre,
                    director_email: trabajo.director_email,
                    codirector_nombre: trabajo.codirector_nombre ?? "",
                    fecha_aprobacion_cpr: trabajo.fecha_aprobacion_cpr ?? "",
                    numero_resolucion: trabajo.numero_resolucion ?? "",
                });
            })
            .catch((e: ApiError) => {
                if (e.status !== 404) setError(e.message);
            })
            .finally(() => setCargando(false));
    }, [usuario, legajoId]);

    function cambiar(campo: keyof Formulario, valor: string) {
        setFormulario((anterior) => ({...anterior, [campo]: valor}));
    }

    async function guardar() {
        setError(null);
        setAviso(null);
        if (formulario.titulo.trim().length < 3 || !formulario.director_nombre.trim()
            || !formulario.director_email.includes("@")) {
            setError("Completá el título (mínimo 3 caracteres), el director y su email.");
            return;
        }
        const datos: TrabajoFinalDatos = {
            tipo: formulario.tipo,
            titulo: formulario.titulo.trim(),
            director_nombre: formulario.director_nombre.trim(),
            director_email: formulario.director_email.trim(),
            codirector_nombre: formulario.codirector_nombre.trim() || null,
            fecha_aprobacion_cpr: formulario.fecha_aprobacion_cpr || null,
            numero_resolucion: formulario.numero_resolucion.trim() || null,
            limpiar_fecha_cpr: limpiarFecha,
        };
        setGuardando(true);
        try {
            if (actual) await editarTrabajoFinal(actual.id, datos);
            else await registrarTrabajoFinal(legajoId, datos);
            setAviso(actual
                ? "Trabajo final actualizado. Si cumple las condiciones, el backend recalculó la graduación."
                : "Trabajo final registrado. Si tiene fecha CPR y no se adeudan seminarios, el legajo se graduó automáticamente.");
        } catch (e) {
            setError((e as ApiError).message);
        } finally {
            setGuardando(false);
        }
    }

    return (
        <PortalCpr
            usuario={usuario}
            titulo={actual ? "Editar TFI/Tesis" : "Registrar TFI/Tesis"}
            accion={
                <Pressable onPress={() => router.push("/cpr")}>
                    <Text style={{color: "#ffffff", fontSize: 13}}>‹ Volver</Text>
                </Pressable>
            }
        >
            {error ? <Text style={{color: "#b91c1c", fontSize: 13}}>{error}</Text> : null}
            {aviso ? <Text style={{color: "#065f46", fontSize: 13}}>{aviso}</Text> : null}
            {cargando ? <Text style={{color: "#6b7280", fontSize: 13}}>Cargando…</Text> : null}

            {!cargando ? (
                <Tarjeta titulo="Datos del trabajo final (RF-GRAD-001)">
                    <Text style={etiqueta}>Tipo</Text>
                    <View style={{flexDirection: "row", gap: 8, marginBottom: 12}}>
                        {(["TFI", "TESIS"] as const).map((tipo) => (
                            <Pressable
                                key={tipo}
                                onPress={() => cambiar("tipo", tipo)}
                                style={{
                                    borderWidth: 1, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 7,
                                    borderColor: formulario.tipo === tipo ? "#0d2035" : "#d1d5db",
                                    backgroundColor: formulario.tipo === tipo ? "#0d2035" : "#ffffff",
                                }}
                            >
                                <Text style={{
                                    color: formulario.tipo === tipo ? "#ffffff" : "#374151",
                                    fontSize: 13, fontWeight: "600",
                                }}>
                                    {tipo}
                                </Text>
                            </Pressable>
                        ))}
                    </View>

                    <Text style={etiqueta}>Título</Text>
                    <TextInput value={formulario.titulo} onChangeText={(v) => cambiar("titulo", v)} style={campo}/>
                    <Text style={etiqueta}>Director/a</Text>
                    <TextInput value={formulario.director_nombre} onChangeText={(v) => cambiar("director_nombre", v)} style={campo}/>
                    <Text style={etiqueta}>Email del director/a</Text>
                    <TextInput
                        value={formulario.director_email} onChangeText={(v) => cambiar("director_email", v)}
                        autoCapitalize="none" inputMode="email" style={campo}
                    />
                    <Text style={etiqueta}>Codirector/a (opcional)</Text>
                    <TextInput value={formulario.codirector_nombre} onChangeText={(v) => cambiar("codirector_nombre", v)} style={campo}/>
                    <Text style={etiqueta}>Fecha de aprobación CPR (AAAA-MM-DD)</Text>
                    <TextInput
                        value={formulario.fecha_aprobacion_cpr}
                        onChangeText={(v) => { cambiar("fecha_aprobacion_cpr", v); setLimpiarFecha(false); }}
                        placeholder="2026-11-20"
                        style={campo}
                    />
                    {actual?.fecha_aprobacion_cpr ? (
                        <Pressable onPress={() => setLimpiarFecha(!limpiarFecha)} style={{flexDirection: "row", gap: 8, marginBottom: 12}}>
                            <Text style={{fontSize: 16}}>{limpiarFecha ? "☑" : "☐"}</Text>
                            <Text style={{fontSize: 13, color: "#374151"}}>Quitar la fecha de aprobación CPR</Text>
                        </Pressable>
                    ) : null}
                    <Text style={etiqueta}>Número de resolución</Text>
                    <TextInput value={formulario.numero_resolucion} onChangeText={(v) => cambiar("numero_resolucion", v)} style={campo}/>

                    <Boton texto={guardando ? "Guardando…" : "Guardar trabajo final"}
                           alPresionar={guardar} deshabilitado={guardando}/>
                </Tarjeta>
            ) : null}
        </PortalCpr>
    );
}

const etiqueta = {fontSize: 12, color: "#6b7280", marginBottom: 4};
const campo = {
    borderWidth: 1, borderColor: "#d1d5db", borderRadius: 6, backgroundColor: "#ffffff",
    paddingHorizontal: 12, paddingVertical: 9, fontSize: 14, marginBottom: 12, color: "#111",
};
