/**
 * Conducción (Módulo C): listado de estudiantes en ROJO ordenados por criticidad
 * (US-C-003), con exportación a Excel y acción rápida de VERDE manual (BR-008).
 */
import {useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {Pressable, Text, View} from "react-native";
import {
    Boton, PortalConduccion, Tarjeta, useUsuarioConduccion,
} from "../../src/components/conduccion/PortalConduccion";
import {
    ApiError, SemaforoFila, exportarEnRiesgo, fijarSemaforo, legajosEnRiesgo,
} from "../../src/lib/api";
import {guardarArchivo} from "../../src/lib/documentos";
import {isoAFecha} from "../../src/lib/formulario";

export default function EnRiesgoConduccionScreen() {
    const router = useRouter();
    const usuario = useUsuarioConduccion();
    const esCoordinador = usuario?.rol === "COORDINADOR";
    const [filas, setFilas] = useState<SemaforoFila[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [aviso, setAviso] = useState<string | null>(null);
    const [exportando, setExportando] = useState(false);
    const [procesando, setProcesando] = useState<string | null>(null);

    async function cargar() {
        try {
            setFilas((await legajosEnRiesgo()).legajos);
        } catch (e) {
            setError((e as ApiError).message);
        }
    }

    useEffect(() => {
        if (usuario) cargar();
    }, [usuario]);

    async function exportar() {
        setExportando(true);
        setError(null);
        try {
            guardarArchivo(await exportarEnRiesgo(), "estudiantes-en-riesgo.xlsx");
            setAviso("Excel descargado.");
        } catch (e) {
            setError((e as ApiError).message);
        } finally {
            setExportando(false);
        }
    }

    async function marcarVerde(fila: SemaforoFila) {
        setProcesando(fila.legajo_id);
        setError(null);
        setAviso(null);
        try {
            await fijarSemaforo(fila.legajo_id, !fila.semaforo_manual);
            setAviso(fila.semaforo_manual
                ? `Cálculo automático restaurado para ${fila.numero_legajo}.`
                : `VERDE fijado para ${fila.numero_legajo}.`);
            await cargar();
        } catch (e) {
            setError((e as ApiError).message);
        } finally {
            setProcesando(null);
        }
    }

    return (
        <PortalConduccion
            usuario={usuario}
            titulo="Estudiantes en riesgo"
            accion={
                <Boton texto={exportando ? "Generando…" : "⬇ Exportar Excel"}
                       tipo="secundario" deshabilitado={exportando} alPresionar={exportar}/>
            }
        >
            {error ? <Text style={{color: "#b91c1c", fontSize: 13}}>{error}</Text> : null}
            {aviso ? <Text style={{color: "#065f46", fontSize: 13}}>{aviso}</Text> : null}
            <Text style={{fontSize: 13, color: "#374151"}}>
                {filas === null ? "Cargando…" : `${filas.length} legajo(s) en ROJO, ordenados por días en riesgo.`}
            </Text>

            {filas?.length === 0 ? (
                <Tarjeta>
                    <Text style={{fontSize: 14, color: "#374151"}}>
                        No hay estudiantes en ROJO en este momento.
                    </Text>
                </Tarjeta>
            ) : null}

            {filas?.map((fila) => (
                <Tarjeta key={fila.legajo_id}>
                    <View style={{flexDirection: "row", alignItems: "flex-start", gap: 12, flexWrap: "wrap"}}>
                        <View style={{flex: 1, minWidth: 220}}>
                            <Pressable onPress={() => router.push(`/conduccion/legajo/${fila.legajo_id}` as never)}>
                                <Text style={{fontSize: 15, fontWeight: "600", color: "#0d2035"}}>
                                    {fila.apellido}, {fila.nombre} · {fila.numero_legajo}
                                </Text>
                            </Pressable>
                            <Text style={{fontSize: 12, color: "#6b7280", marginTop: 4}}>
                                {fila.carrera} · Inscripción: {isoAFecha(fila.fecha_inscripcion)}
                            </Text>
                            <Text style={{fontSize: 12, color: "#b91c1c", marginTop: 4}}>
                                Adeuda {fila.seminarios_adeudados} de {fila.seminarios_obligatorios_total}{" "}
                                seminarios obligatorios · {fila.dias_en_riesgo} días en ROJO
                                {fila.tiene_fecha_cpr ? " · con fecha CPR" : " · sin fecha CPR"}
                            </Text>
                        </View>
                        {esCoordinador ? (
                            <Boton
                                texto={procesando === fila.legajo_id ? "…" : fila.semaforo_manual ? "Restaurar" : "Fijar VERDE"}
                                tipo="secundario"
                                deshabilitado={procesando === fila.legajo_id}
                                alPresionar={() => marcarVerde(fila)}
                            />
                        ) : null}
                    </View>
                </Tarjeta>
            ))}
        </PortalConduccion>
    );
}
