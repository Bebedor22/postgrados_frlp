/**
 * Conducción (Módulo D): dashboard de estadísticas por cohorte (RF-REP-001, US-D-001) con
 * filtro por tipo de carrera y exportación a Excel (RF-REP-002, US-D-003).
 *
 * Todos los números los calcula el backend; esta pantalla solo los muestra.
 */
import {useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {ActivityIndicator, Pressable, Text, View, useWindowDimensions} from "react-native";
import {Boton, PortalConduccion, Tarjeta, useUsuarioConduccion} from "../../src/components/conduccion/PortalConduccion";
import {BarrasHorizontales, BarrasVerticales} from "../../src/components/conduccion/Graficos";
import {ApiError, Dashboard, TipoCarreraFiltro, exportarDashboard, obtenerDashboard} from "../../src/lib/api";
import {guardarArchivo} from "../../src/lib/documentos";
import {ESTADOS} from "../../src/lib/formulario";

const TIPOS: {texto: string; valor: TipoCarreraFiltro | null}[] = [
    {texto: "Todas", valor: null},
    {texto: "Especialización", valor: "Especializacion"},
    {texto: "Maestría", valor: "Maestria"},
    {texto: "Doctorado", valor: "Doctorado"},
];
const NOMBRE_TIPO: Record<string, string> = {
    Especializacion: "Especialización", Maestria: "Maestría", Doctorado: "Doctorado",
};
const ORDEN_ESTADOS = [
    "BORRADOR", "PENDIENTE", "EN_REVISION", "OBSERVADO", "COMPLETADO", "ACTIVO",
    "GRADUADO", "RECHAZADO", "VENCIDO", "BAJA",
];
const CORTOS: Record<string, string> = {
    BORRADOR: "En carga", PENDIENTE: "Pendientes", EN_REVISION: "En revisión", OBSERVADO: "Observados",
    COMPLETADO: "Aprobados", ACTIVO: "Activos", GRADUADO: "Graduados", RECHAZADO: "Rechazados",
    VENCIDO: "Vencidos", BAJA: "Bajas",
};

const pct = (n: number) => `${n.toLocaleString("es-AR", {maximumFractionDigits: 1})}%`;
const dias = (n: number | null) =>
    n === null ? "—" : `${Math.round(n).toLocaleString("es-AR")} días (~${(n / 365).toLocaleString("es-AR", {maximumFractionDigits: 1})} años)`;

function Chip({texto, activo, alPresionar}: {texto: string; activo: boolean; alPresionar: () => void}) {
    return (
        <Pressable
            onPress={alPresionar}
            style={{
                paddingHorizontal: 12, paddingVertical: 6, borderRadius: 999, borderWidth: 1,
                borderColor: activo ? "#0d2035" : "#d1d5db", backgroundColor: activo ? "#0d2035" : "#ffffff",
            }}
        >
            <Text style={{fontSize: 13, color: activo ? "#ffffff" : "#374151", fontWeight: activo ? "600" : "400"}}>
                {texto}
            </Text>
        </Pressable>
    );
}

function Indicador({titulo, valor, color = "#111827", detalle, alPresionar}: {
    titulo: string; valor: string; color?: string; detalle?: string; alPresionar?: () => void;
}) {
    const contenido = (
        <>
            <Text style={{fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: 0.5}}>{titulo}</Text>
            <Text style={{fontSize: 26, fontWeight: "700", color, marginTop: 4}}>{valor}</Text>
            {detalle ? <Text style={{fontSize: 11, color: "#6b7280", marginTop: 2}}>{detalle}</Text> : null}
        </>
    );
    const estilo = {
        flexGrow: 1, flexBasis: 150, backgroundColor: "#ffffff", borderWidth: 1, borderColor: "#e5e7eb",
        borderRadius: 8, padding: 16,
    };
    return alPresionar
        ? <Pressable onPress={alPresionar} style={estilo}>{contenido}</Pressable>
        : <View style={estilo}>{contenido}</View>;
}

export default function EstadisticasScreen() {
    const router = useRouter();
    const usuario = useUsuarioConduccion();
    const {width} = useWindowDimensions();
    const compacto = width < 860;

    const [tipo, setTipo] = useState<TipoCarreraFiltro | null>(null);
    const [datos, setDatos] = useState<Dashboard | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [exportando, setExportando] = useState(false);

    function manejarError(e: unknown) {
        const err = e as ApiError;
        if (err.status === 401) router.replace("/login");
        else setError(err.message);
    }

    useEffect(() => {
        if (!usuario) return;
        setDatos(null);
        setError(null);
        obtenerDashboard(tipo ?? undefined).then(setDatos).catch(manejarError);
    }, [usuario, tipo]);

    async function exportar() {
        setExportando(true);
        setError(null);
        try {
            const excel = await exportarDashboard(tipo ?? undefined);
            guardarArchivo(excel, `metricas_posgrado${tipo ? `_${tipo.toLowerCase()}` : ""}.xlsx`);
        } catch (e) {
            manejarError(e);
        } finally {
            setExportando(false);
        }
    }

    // El backend devuelve las cohortes de la más nueva a la más vieja: se comparan las últimas 3, en orden cronológico
    const ultimas = datos ? datos.cohortes.slice(0, 3).reverse() : [];
    const estados = datos
        ? ORDEN_ESTADOS.filter((e) => (datos.por_estado[e] ?? 0) > 0).map((e) => ({
            etiqueta: CORTOS[e], valor: datos.por_estado[e], color: ESTADOS[e]?.color,
        }))
        : [];
    const tiposCarrera = datos
        ? Object.entries(datos.por_tipo_carrera).map(([t, valor]) => ({etiqueta: NOMBRE_TIPO[t] ?? t, valor}))
        : [];

    return (
        <PortalConduccion
            usuario={usuario}
            titulo="Estadísticas del posgrado"
            accion={<Boton
                texto={exportando ? "Generando..." : "Exportar Excel"}
                tipo="secundario"
                alPresionar={exportar}
                deshabilitado={exportando || datos === null}
            />}
        >
            {error ? (
                <Tarjeta estilo={{borderColor: "#fca5a5", backgroundColor: "#fef2f2"}}>
                    <Text style={{color: "#b91c1c", fontSize: 13}}>{error}</Text>
                </Tarjeta>
            ) : null}

            <View style={{flexDirection: "row", flexWrap: "wrap", gap: 8, alignItems: "center"}}>
                <Text style={{fontSize: 12, fontWeight: "600", color: "#6b7280"}}>Tipo de carrera</Text>
                {TIPOS.map((t) => (
                    <Chip key={t.texto} texto={t.texto} activo={tipo === t.valor} alPresionar={() => setTipo(t.valor)}/>
                ))}
            </View>

            {datos === null && !error ? (
                <View style={{padding: 32, alignItems: "center"}}><ActivityIndicator color="#0d2035"/></View>
            ) : null}

            {datos ? (
                <>
                    <View style={{flexDirection: "row", flexWrap: "wrap", gap: 10}}>
                        <Indicador titulo="Inscriptos" valor={String(datos.total_inscriptos)}/>
                        <Indicador titulo="Activos" valor={String(datos.activos)} color="#047857"/>
                        <Indicador titulo="Graduados" valor={String(datos.graduados)} color="#047857"/>
                        <Indicador titulo="Bajas" valor={String(datos.bajas)} color="#6b7280"
                                   detalle="Baja, vencido o rechazado"/>
                        <Indicador
                            titulo="En riesgo" valor={String(datos.en_riesgo)} color="#b91c1c"
                            detalle="Ver detalle →"
                            alPresionar={() => router.push("/conduccion/en-riesgo" as never)}
                        />
                    </View>
                    <View style={{flexDirection: "row", flexWrap: "wrap", gap: 10}}>
                        <Indicador titulo="Retención" valor={pct(datos.retencion_pct)}
                                   detalle="(activos + graduados) / matriculados"/>
                        <Indicador titulo="Desgranamiento" valor={pct(datos.desgranamiento_pct)} color="#b45309"
                                   detalle="bajas / matriculados"/>
                        <Indicador titulo="Tiempo promedio de graduación"
                                   valor={datos.tiempo_promedio_graduacion_dias === null ? "—" : `${Math.round(datos.tiempo_promedio_graduacion_dias)} d`}
                                   detalle={datos.tiempo_promedio_graduacion_dias === null ? "Todavía no hay graduados" : dias(datos.tiempo_promedio_graduacion_dias)}/>
                    </View>

                    <Tarjeta titulo="Comparativa de las últimas cohortes">
                        {ultimas.length === 0 ? (
                            <Text style={{fontSize: 13, color: "#6b7280"}}>No hay cohortes cargadas.</Text>
                        ) : (
                            <View style={{flexDirection: compacto ? "column" : "row", gap: 28}}>
                                <View style={{flex: 1}}>
                                    <Text style={subtitulo}>Inscriptos</Text>
                                    <BarrasVerticales datos={ultimas.map((c) => ({
                                        etiqueta: c.cohorte_nombre, valor: c.inscriptos,
                                    }))}/>
                                </View>
                                <View style={{flex: 1}}>
                                    <Text style={subtitulo}>Retención</Text>
                                    <BarrasVerticales maximo={100} color="#2563eb" datos={ultimas.map((c) => ({
                                        etiqueta: c.cohorte_nombre, valor: c.retencion_pct, texto: pct(c.retencion_pct),
                                    }))}/>
                                </View>
                                <View style={{flex: 1}}>
                                    <Text style={subtitulo}>Desgranamiento</Text>
                                    <BarrasVerticales maximo={100} color="#b45309" datos={ultimas.map((c) => ({
                                        etiqueta: c.cohorte_nombre, valor: c.desgranamiento_pct,
                                        texto: pct(c.desgranamiento_pct),
                                    }))}/>
                                </View>
                            </View>
                        )}
                    </Tarjeta>

                    <View style={{flexDirection: compacto ? "column" : "row", gap: 16}}>
                        <Tarjeta titulo="Legajos por estado" estilo={{flex: 1}}>
                            {estados.length === 0
                                ? <Text style={{fontSize: 13, color: "#6b7280"}}>Sin legajos.</Text>
                                : <BarrasHorizontales datos={estados}/>}
                        </Tarjeta>
                        <Tarjeta titulo="Inscriptos por tipo de carrera" estilo={{flex: 1}}>
                            {tiposCarrera.length === 0
                                ? <Text style={{fontSize: 13, color: "#6b7280"}}>Sin legajos.</Text>
                                : <BarrasHorizontales datos={tiposCarrera} color="#2563eb"/>}
                        </Tarjeta>
                    </View>

                    <Tarjeta titulo="Detalle por cohorte">
                        {datos.cohortes.length === 0 ? (
                            <Text style={{fontSize: 13, color: "#6b7280"}}>No hay cohortes cargadas.</Text>
                        ) : compacto ? (
                            datos.cohortes.map((c) => (
                                <View key={c.cohorte_id} style={{paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: "#f3f4f6"}}>
                                    <Text style={{fontSize: 14, fontWeight: "600", color: "#111827"}}>{c.cohorte_nombre}</Text>
                                    <Text style={{fontSize: 12, color: "#6b7280", marginTop: 2}}>
                                        {c.inscriptos} inscriptos · {c.activos} activos · {c.graduados} graduados · {c.bajas} bajas · {c.en_riesgo} en riesgo
                                    </Text>
                                    <Text style={{fontSize: 12, color: "#6b7280"}}>
                                        Retención {pct(c.retencion_pct)} · Desgranamiento {pct(c.desgranamiento_pct)}
                                    </Text>
                                </View>
                            ))
                        ) : (
                            <>
                                <View style={{flexDirection: "row", paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: "#e5e7eb"}}>
                                    {COLUMNAS.map((col) => (
                                        <Text key={col.titulo} style={[celda.encabezado, {flex: col.flex}]}>{col.titulo}</Text>
                                    ))}
                                </View>
                                {datos.cohortes.map((c) => (
                                    <View key={c.cohorte_id} style={{flexDirection: "row", paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: "#f3f4f6"}}>
                                        <Text style={[celda.texto, {flex: COLUMNAS[0].flex, fontWeight: "600"}]}>{c.cohorte_nombre}</Text>
                                        <Text style={[celda.texto, {flex: COLUMNAS[1].flex}]}>{c.inscriptos}</Text>
                                        <Text style={[celda.texto, {flex: COLUMNAS[2].flex}]}>{c.activos}</Text>
                                        <Text style={[celda.texto, {flex: COLUMNAS[3].flex}]}>{c.graduados}</Text>
                                        <Text style={[celda.texto, {flex: COLUMNAS[4].flex}]}>{c.bajas}</Text>
                                        <Text style={[celda.texto, {flex: COLUMNAS[5].flex, color: c.en_riesgo > 0 ? "#b91c1c" : "#374151"}]}>{c.en_riesgo}</Text>
                                        <Text style={[celda.texto, {flex: COLUMNAS[6].flex}]}>{pct(c.retencion_pct)}</Text>
                                        <Text style={[celda.texto, {flex: COLUMNAS[7].flex}]}>{pct(c.desgranamiento_pct)}</Text>
                                    </View>
                                ))}
                            </>
                        )}
                    </Tarjeta>
                </>
            ) : null}
        </PortalConduccion>
    );
}

const COLUMNAS = [
    {titulo: "Cohorte", flex: 1.6}, {titulo: "Inscriptos", flex: 1}, {titulo: "Activos", flex: 1},
    {titulo: "Graduados", flex: 1}, {titulo: "Bajas", flex: 0.8}, {titulo: "En riesgo", flex: 1},
    {titulo: "Retención", flex: 1}, {titulo: "Desgran.", flex: 1},
];
const subtitulo = {fontSize: 12, fontWeight: "600" as const, color: "#6b7280", marginBottom: 8};
const celda = {
    encabezado: {fontSize: 11, fontWeight: "700" as const, color: "#6b7280", textTransform: "uppercase" as const, letterSpacing: 0.5},
    texto: {fontSize: 13, color: "#374151"},
};
