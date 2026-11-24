/**
 * Portal CPR (Módulo C, BR-004): busca legajos para registrar o editar su TFI/Tesis.
 * Usa un endpoint propio con datos mínimos; el CPR no accede a la bandeja completa.
 */
import {useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {Pressable, Text, TextInput, View} from "react-native";
import {
    InsigniaEstado, Tarjeta,
} from "../../src/components/conduccion/PortalConduccion";
import {PortalCpr, useUsuarioCpr} from "../../src/components/cpr/PortalCpr";
import {ApiError, LegajoTesisItem, legajosParaTesis} from "../../src/lib/api";
import {ESTADOS} from "../../src/lib/formulario";

export default function GestionTesisScreen() {
    const router = useRouter();
    const usuario = useUsuarioCpr();
    const [buscar, setBuscar] = useState("");
    const [legajos, setLegajos] = useState<LegajoTesisItem[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!usuario) return;
        const espera = setTimeout(() => {
            legajosParaTesis(buscar.trim())
                .then(setLegajos)
                .catch((e: ApiError) => setError(e.message));
        }, 300);
        return () => clearTimeout(espera);
    }, [usuario, buscar]);

    return (
        <PortalCpr usuario={usuario} titulo="Gestión de Tesis y Trabajos Finales">
            <Text style={{fontSize: 13, color: "#4b5563"}}>
                Buscá por apellido, nombre, documento o número de legajo. Solo el CPR puede cargar
                o modificar estos datos (BR-004).
            </Text>
            <TextInput
                value={buscar}
                onChangeText={setBuscar}
                placeholder="Ej.: Fernández, 35222111…"
                style={{
                    borderWidth: 1, borderColor: "#d1d5db", borderRadius: 6, backgroundColor: "#ffffff",
                    paddingHorizontal: 12, paddingVertical: 10, fontSize: 14,
                }}
            />
            {error ? <Text style={{color: "#b91c1c", fontSize: 13}}>{error}</Text> : null}
            {legajos === null ? <Text style={{color: "#6b7280", fontSize: 13}}>Buscando…</Text> : null}
            {legajos?.length === 0 ? (
                <Tarjeta><Text style={{fontSize: 13, color: "#6b7280"}}>No se encontraron legajos.</Text></Tarjeta>
            ) : null}

            {legajos?.map((legajo) => {
                const estado = ESTADOS[legajo.estado] ?? {texto: legajo.estado, color: "#374151", fondo: "#f3f4f6"};
                return (
                    <Tarjeta key={legajo.legajo_id}>
                        <View style={{flexDirection: "row", alignItems: "flex-start", gap: 12, flexWrap: "wrap"}}>
                            <View style={{flex: 1, minWidth: 220}}>
                                <Text style={{fontSize: 15, fontWeight: "600", color: "#111"}}>
                                    {legajo.apellido}, {legajo.nombre}
                                </Text>
                                <Text style={{fontSize: 12, color: "#6b7280", marginTop: 4}}>
                                    {legajo.numero_legajo} · {legajo.carrera}
                                </Text>
                                <View style={{marginTop: 8}}>
                                    <InsigniaEstado texto={estado.texto} color={estado.color} fondo={estado.fondo}/>
                                </View>
                            </View>
                            <Pressable
                                onPress={() => router.push(`/cpr/trabajo-final/${legajo.legajo_id}` as never)}
                                style={{
                                    backgroundColor: "#0d2035", borderRadius: 6, paddingHorizontal: 16,
                                    paddingVertical: 10,
                                }}
                            >
                                <Text style={{color: "#ffffff", fontSize: 13, fontWeight: "600"}}>
                                    {legajo.tiene_trabajo_final ? "Editar TFI ›" : "Registrar TFI ›"}
                                </Text>
                            </Pressable>
                        </View>
                    </Tarjeta>
                );
            })}
        </PortalCpr>
    );
}
