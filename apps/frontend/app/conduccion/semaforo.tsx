/**
 * Conducción (Módulo C): dashboard del semáforo de riesgo.
 *
 * Muestra el valor almacenado en la base (ASR-003), nunca un cálculo local. El
 * coordinador puede fijar VERDE manualmente (BR-008) o restaurar el automático.
 */
import {useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {Pressable, Text, View} from "react-native";
import {
    Boton, PortalConduccion, Tarjeta, useUsuarioConduccion,
} from "../../src/components/conduccion/PortalConduccion";
import {SemaforoBadge} from "../../src/components/conduccion/Semaforo";
import {
    ApiError, SemaforoFila, fijarSemaforo, semaforoActivos,
} from "../../src/lib/api";

type Filtro = "TODOS" | "ROJO" | "AMARILLO" | "VERDE";

export default function SemáforoConduccionScreen() {
    const router = useRouter();
    const usuario = useUsuarioConduccion();
    const esCoordinador = usuario?.rol === "COORDINADOR";
    const [filas, setFilas] = useState<SemaforoFila[] | null>(null);
    const [filtro, setFiltro] = useState<Filtro>("TODOS");
    const [error, setError] = useState<string | null>(null);
    const [aviso, setAviso] = useState<string | null>(null);
    const [procesando, setProcesando] = useState<string | null>(null);

    async function cargar() {
        try {
            const respuesta = await semaforoActivos();
            setFilas(respuesta.legajos);
        } catch (e) {
            setError((e as ApiError).message);
        }
    }

    useEffect(() => {
        if (usuario) cargar();
    }, [usuario]);

    async function cambiarVerde(fila: SemaforoFila) {
        setProcesando(fila.legajo_id);
        setError(null);
        setAviso(null);
        try {
            const actualizada = await fijarSemaforo(fila.legajo_id, !fila.semaforo_manual);
            setAviso(actualizada.semaforo_manual
                ? `VERDE fijado manualmente para ${fila.numero_legajo}. El recálculo no lo va a pisar.`
                : `Cálculo automático restaurado para ${fila.numero_legajo}.`);
            await cargar();
        } catch (e) {
            setError((e as ApiError).message);
        } finally {
            setProcesando(null);
        }
    }

    const visibles = (filas ?? []).filter((f) => filtro === "TODOS" || f.semaforo === filtro);
    const conteo: Record<string, number> = {
        ROJO: (filas ?? []).filter((f) => f.semaforo === "ROJO").length,
        AMARILLO: (filas ?? []).filter((f) => f.semaforo === "AMARILLO").length,
        VERDE: (filas ?? []).filter((f) => f.semaforo === "VERDE").length,
    };

    return (
        <PortalConduccion usuario={usuario} titulo="Semáforo de riesgo académico">
            {error ? <Text style={{color: "#b91c1c", fontSize: 13}}>{error}</Text> : null}
            {aviso ? <Text style={{color: "#065f46", fontSize: 13}}>{aviso}</Text> : null}

            <View style={{flexDirection: "row", gap: 12, flexWrap: "wrap"}}>
                {(["ROJO", "AMARILLO", "VERDE"] as const).map((color) => (
                    <Tarjeta key={color} estilo={{minWidth: 140, flex: 1}}>
                        <Text style={{fontSize: 11, color: "#6b7280", textTransform: "uppercase"}}>{color}</Text>
                        <Text style={{fontSize: 26, fontWeight: "700", color: "#111", marginTop: 4}}>
                            {conteo[color]}
                        </Text>
                    </Tarjeta>
                ))}
            </View>

            <View style={{flexDirection: "row", gap: 8, flexWrap: "wrap"}}>
                {(["TODOS", "ROJO", "AMARILLO", "VERDE"] as Filtro[]).map((opcion) => (
                    <Pressable
                        key={opcion}
                        onPress={() => setFiltro(opcion)}
                        style={{
                            borderWidth: 1, borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6,
                            borderColor: filtro === opcion ? "#0d2035" : "#d1d5db",
                            backgroundColor: filtro === opcion ? "#0d2035" : "#ffffff",
                        }}
                    >
                        <Text style={{
                            fontSize: 12, fontWeight: filtro === opcion ? "600" : "400",
                            color: filtro === opcion ? "#ffffff" : "#374151",
                        }}>
                            {opcion === "TODOS" ? `Todos (${filas?.length ?? 0})` : opcion}
                        </Text>
                    </Pressable>
                ))}
            </View>

            {filas === null ? <Text style={{color: "#6b7280", fontSize: 13}}>Cargando semáforo…</Text> : null}
            {filas?.length === 0 ? (
                <Tarjeta><Text style={{fontSize: 13, color: "#6b7280"}}>No hay legajos activos.</Text></Tarjeta>
            ) : null}

            {visibles.map((fila) => (
                <Tarjeta key={fila.legajo_id}>
                    <View style={{flexDirection: "row", alignItems: "flex-start", gap: 12, flexWrap: "wrap"}}>
                        <View style={{flex: 1, minWidth: 200}}>
                            <Pressable onPress={() => router.push(`/conduccion/legajo/${fila.legajo_id}` as never)}>
                                <Text style={{fontSize: 15, fontWeight: "600", color: "#0d2035"}}>
                                    {fila.numero_legajo} · {fila.apellido}, {fila.nombre}
                                </Text>
                            </Pressable>
                            <Text style={{fontSize: 12, color: "#6b7280", marginTop: 4}}>
                                {fila.carrera} · {fila.seminarios_aprobados}/{fila.seminarios_obligatorios_total} obligatorios
                                {fila.seminarios_adeudados > 0 ? ` · ${fila.seminarios_adeudados} adeudados` : ""}
                                {fila.tiene_tfi_registrado ? " · TFI registrado" : " · sin TFI"}
                                {fila.dias_en_riesgo > 0 ? ` · ${fila.dias_en_riesgo} días en este color` : ""}
                            </Text>
                        </View>
                        <SemaforoBadge color={fila.semaforo}/>
                        {esCoordinador ? (
                            <Boton
                                texto={procesando === fila.legajo_id
                                    ? "…"
                                    : fila.semaforo_manual ? "Restaurar cálculo" : "Fijar VERDE"}
                                tipo="secundario"
                                deshabilitado={procesando === fila.legajo_id}
                                alPresionar={() => cambiarVerde(fila)}
                            />
                        ) : null}
                    </View>
                    {fila.semaforo_manual ? (
                        <Text style={{fontSize: 11, color: "#92400e", marginTop: 6}}>
                            VERDE asignado manualmente: el recálculo diario no lo modifica.
                        </Text>
                    ) : null}
                </Tarjeta>
            ))}
        </PortalConduccion>
    );
}
