/**
 * Bandeja del equipo de conducción: elegir cohorte, abrir o cerrar la inscripción,
 * ver cuántos legajos hay en cada estado y listar o buscar inscriptos.
 */
import {useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {ActivityIndicator, Pressable, Text, TextInput, View, useWindowDimensions} from "react-native";
import {
    Boton, InsigniaEstado, PortalConduccion, Tarjeta, useUsuarioConduccion,
} from "../../src/components/conduccion/PortalConduccion";
import {
    ApiError, Cohorte, LegajoFila, cambiarInscripcionCohorte, listarCohortes, listarLegajos, resumenLegajos,
} from "../../src/lib/api";
import {ESTADOS} from "../../src/lib/formulario";

const POR_PAGINA = 15;
// Estados que se muestran en el resumen, en el orden del workflow
const ESTADOS_RESUMEN = ["PENDIENTE", "EN_REVISION", "OBSERVADO", "COMPLETADO", "ACTIVO", "BORRADOR", "RECHAZADO", "VENCIDO"];
const NOMBRE_CORTO: Record<string, string> = {
    BORRADOR: "En carga",
    PENDIENTE: "Pendientes",
    EN_REVISION: "En revisión",
    OBSERVADO: "Observados",
    COMPLETADO: "Aprobados",
    ACTIVO: "Activos",
    RECHAZADO: "Rechazados",
    VENCIDO: "Vencidos",
};

function Chip({texto, activo, alPresionar}: {texto: string; activo: boolean; alPresionar: () => void}) {
    return (
        <Pressable
            onPress={alPresionar}
            style={{
                paddingHorizontal: 12,
                paddingVertical: 6,
                borderRadius: 999,
                borderWidth: 1,
                borderColor: activo ? "#0d2035" : "#d1d5db",
                backgroundColor: activo ? "#0d2035" : "#ffffff",
            }}
        >
            <Text style={{fontSize: 13, color: activo ? "#ffffff" : "#374151", fontWeight: activo ? "600" : "400"}}>{texto}</Text>
        </Pressable>
    );
}

export default function BandejaConduccionScreen() {
    const router = useRouter();
    const usuario = useUsuarioConduccion();
    const {width} = useWindowDimensions();
    const compacto = width < 860;
    const esCoordinador = usuario?.rol === "COORDINADOR";

    const [cohortes, setCohortes] = useState<Cohorte[]>([]);
    const [cohorteId, setCohorteId] = useState<string | null>(null);
    const [resumen, setResumen] = useState<Record<string, number>>({});
    const [estado, setEstado] = useState<string | null>(null);
    const [buscar, setBuscar] = useState("");
    const [busquedaAplicada, setBusquedaAplicada] = useState("");
    const [pagina, setPagina] = useState(1);
    const [legajos, setLegajos] = useState<LegajoFila[] | null>(null);
    const [total, setTotal] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [cambiandoInscripcion, setCambiandoInscripcion] = useState(false);

    const cohorte = cohortes.find((c) => c.id === cohorteId) ?? null;

    function manejarError(e: unknown) {
        const err = e as ApiError;
        if (err.status === 401) router.replace("/login");
        else setError(err.message);
    }

    // Cohortes: se elige primero la que tiene la inscripción abierta
    useEffect(() => {
        if (!usuario) return;
        listarCohortes()
            .then((lista) => {
                setCohortes(lista);
                setCohorteId((lista.find((c) => c.inscripcion_abierta) ?? lista[0])?.id ?? null);
            })
            .catch(manejarError);
    }, [usuario]);

    // La búsqueda se aplica cuando se deja de escribir (0,4 s)
    useEffect(() => {
        const espera = setTimeout(() => {
            setBusquedaAplicada(buscar.trim().length >= 2 ? buscar.trim() : "");
            setPagina(1);
        }, 400);
        return () => clearTimeout(espera);
    }, [buscar]);

    useEffect(() => {
        if (!usuario || !cohorteId) return;
        resumenLegajos(cohorteId).then(setResumen).catch(manejarError);
    }, [usuario, cohorteId]);

    useEffect(() => {
        if (!usuario || !cohorteId) return;
        setLegajos(null);
        listarLegajos({
            cohorte_id: cohorteId,
            estado: estado ?? undefined,
            buscar: busquedaAplicada || undefined,
            pagina,
            por_pagina: POR_PAGINA,
        })
            .then((r) => {
                setLegajos(r.legajos);
                setTotal(r.total);
            })
            .catch(manejarError);
    }, [usuario, cohorteId, estado, busquedaAplicada, pagina]);

    async function alternarInscripcion() {
        if (!cohorte) return;
        setCambiandoInscripcion(true);
        try {
            const actualizada = await cambiarInscripcionCohorte(cohorte.id, !cohorte.inscripcion_abierta);
            setCohortes((lista) => lista.map((c) => (c.id === actualizada.id ? actualizada : c)));
        } catch (e) {
            manejarError(e);
        } finally {
            setCambiandoInscripcion(false);
        }
    }

    const elegirEstado = (nuevo: string | null) => {
        setEstado(nuevo);
        setPagina(1);
    };
    const totalPaginas = Math.max(1, Math.ceil(total / POR_PAGINA));
    const totalCohorte = Object.values(resumen).reduce((a, b) => a + b, 0);

    return (
        <PortalConduccion usuario={usuario} titulo="Inscriptos y legajos">
            {error ? (
                <Tarjeta estilo={{borderColor: "#fca5a5", backgroundColor: "#fef2f2"}}>
                    <Text style={{color: "#b91c1c", fontSize: 13}}>{error}</Text>
                </Tarjeta>
            ) : null}

            {/* Cohorte + apertura y cierre de la inscripción (BR-009) */}
            <Tarjeta titulo="Cohorte">
                {cohortes.length === 0 ? (
                    <Text style={{fontSize: 13, color: "#6b7280"}}>No hay cohortes cargadas.</Text>
                ) : (
                    <View style={{flexDirection: "row", flexWrap: "wrap", gap: 8}}>
                        {cohortes.map((c) => (
                            <Chip
                                key={c.id}
                                texto={`${c.nombre}${c.inscripcion_abierta ? " · abierta" : ""}`}
                                activo={c.id === cohorteId}
                                alPresionar={() => {
                                    setCohorteId(c.id);
                                    setPagina(1);
                                }}
                            />
                        ))}
                    </View>
                )}
                {cohorte ? (
                    <View style={{
                        marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: "#f3f4f6",
                        flexDirection: compacto ? "column" : "row", gap: 12,
                        alignItems: compacto ? "flex-start" : "center", justifyContent: "space-between",
                    }}>
                        <View style={{flexDirection: "row", alignItems: "center", gap: 8}}>
                            <View style={{
                                width: 10, height: 10, borderRadius: 5,
                                backgroundColor: cohorte.inscripcion_abierta ? "#16a34a" : "#9ca3af",
                            }}/>
                            <Text style={{fontSize: 14, color: "#111827"}}>
                                Inscripción {cohorte.inscripcion_abierta ? "abierta" : "cerrada"}
                                <Text style={{color: "#6b7280"}}> · {totalCohorte} legajos en {cohorte.nombre}</Text>
                            </Text>
                        </View>
                        {esCoordinador ? (
                            <Boton
                                texto={cambiandoInscripcion ? "Guardando..." : cohorte.inscripcion_abierta ? "Cerrar inscripción" : "Abrir inscripción"}
                                tipo={cohorte.inscripcion_abierta ? "peligro" : "exito"}
                                alPresionar={alternarInscripcion}
                                deshabilitado={cambiandoInscripcion}
                            />
                        ) : (
                            <Text style={{fontSize: 12, color: "#6b7280"}}>Solo la coordinación abre o cierra la inscripción.</Text>
                        )}
                    </View>
                ) : null}
            </Tarjeta>

            {/* Resumen por estado: cada tarjeta filtra la lista */}
            <View style={{flexDirection: "row", flexWrap: "wrap", gap: 10}}>
                {ESTADOS_RESUMEN.map((e) => {
                    const activo = estado === e;
                    const color = ESTADOS[e]?.color ?? "#374151";
                    return (
                        <Pressable
                            key={e}
                            onPress={() => elegirEstado(activo ? null : e)}
                            style={{
                                flexGrow: 1, flexBasis: compacto ? "45%" : 110,
                                backgroundColor: "#ffffff", borderRadius: 8, padding: 12,
                                borderWidth: activo ? 2 : 1, borderColor: activo ? color : "#e5e7eb",
                            }}
                        >
                            <Text style={{fontSize: 22, fontWeight: "700", color}}>{resumen[e] ?? 0}</Text>
                            <Text style={{fontSize: 12, color: "#6b7280"}}>{NOMBRE_CORTO[e]}</Text>
                        </Pressable>
                    );
                })}
            </View>

            {/* Filtros y listado */}
            <Tarjeta>
                <View style={{flexDirection: compacto ? "column" : "row", gap: 12, marginBottom: 12}}>
                    <TextInput
                        value={buscar}
                        onChangeText={setBuscar}
                        placeholder="Buscar por apellido, nombre, documento, email o N° de legajo"
                        placeholderTextColor="#9ca3af"
                        style={{
                            flex: 1, borderWidth: 1, borderColor: "#d1d5db", borderRadius: 6,
                            paddingHorizontal: 12, paddingVertical: 9, fontSize: 14, backgroundColor: "#ffffff",
                        }}
                    />
                </View>
                <View style={{flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 16}}>
                    <Chip texto="Todos" activo={estado === null} alPresionar={() => elegirEstado(null)}/>
                    {ESTADOS_RESUMEN.map((e) => (
                        <Chip key={e} texto={NOMBRE_CORTO[e]} activo={estado === e} alPresionar={() => elegirEstado(e)}/>
                    ))}
                </View>

                {!compacto ? (
                    <View style={{flexDirection: "row", paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: "#e5e7eb"}}>
                        <Text style={[celda.encabezado, {flex: 2.2}]}>Aspirante</Text>
                        <Text style={[celda.encabezado, {flex: 1.2}]}>Documento</Text>
                        <Text style={[celda.encabezado, {flex: 2.4}]}>Carrera</Text>
                        <Text style={[celda.encabezado, {flex: 1.8}]}>Estado</Text>
                        <Text style={[celda.encabezado, {flex: 0.8}]}>Beca</Text>
                    </View>
                ) : null}

                {legajos === null ? (
                    <View style={{padding: 24, alignItems: "center"}}><ActivityIndicator color="#0d2035"/></View>
                ) : legajos.length === 0 ? (
                    <Text style={{padding: 24, textAlign: "center", color: "#6b7280", fontSize: 13}}>
                        No hay legajos que coincidan con los filtros.
                    </Text>
                ) : (
                    legajos.map((l) => {
                        const est = ESTADOS[l.estado] ?? {texto: l.estado, color: "#374151", fondo: "#f3f4f6"};
                        return (
                            <Pressable
                                key={l.id}
                                onPress={() => router.push(`/conduccion/legajo/${l.id}` as never)}
                                // "hovered" existe en web (mouse encima); en el celular se usa "pressed"
                                style={(estadoFila) => ({
                                    flexDirection: compacto ? "column" : "row",
                                    alignItems: compacto ? "flex-start" : "center",
                                    gap: compacto ? 4 : 0,
                                    paddingVertical: 12,
                                    borderBottomWidth: 1,
                                    borderBottomColor: "#f3f4f6",
                                    backgroundColor:
                                        (estadoFila as {hovered?: boolean}).hovered || estadoFila.pressed ? "#f9fafb" : "transparent",
                                })}
                            >
                                <View style={{flex: compacto ? undefined : 2.2, paddingRight: 12}}>
                                    <Text style={{fontSize: 14, fontWeight: "600", color: "#111827"}}>{l.apellido}, {l.nombre}</Text>
                                    <Text numberOfLines={1} style={{fontSize: 12, color: "#6b7280"}}>{l.email} · N° {l.numero_legajo}</Text>
                                </View>
                                <Text style={[celda.texto, {flex: compacto ? undefined : 1.2}]}>
                                    {l.tipo_documento === "PASAPORTE" ? "Pas. " : ""}{l.documento}
                                </Text>
                                <Text style={[celda.texto, {flex: compacto ? undefined : 2.4}]}>{l.carrera ?? "—"}</Text>
                                <View style={{flex: compacto ? undefined : 1.8}}>
                                    <InsigniaEstado texto={est.texto} color={est.color} fondo={est.fondo}/>
                                </View>
                                <Text style={[celda.texto, {flex: compacto ? undefined : 0.8}]}>
                                    {l.solicita_beca ? `${l.tipo_beca ?? "?"}%` : "—"}
                                </Text>
                            </Pressable>
                        );
                    })
                )}

                <View style={{flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: 16}}>
                    <Text style={{fontSize: 12, color: "#6b7280"}}>
                        {total} {total === 1 ? "legajo" : "legajos"} · página {pagina} de {totalPaginas}
                    </Text>
                    <View style={{flexDirection: "row", gap: 8}}>
                        <Boton texto="‹ Anterior" tipo="secundario" alPresionar={() => setPagina((p) => p - 1)} deshabilitado={pagina <= 1}/>
                        <Boton texto="Siguiente ›" tipo="secundario" alPresionar={() => setPagina((p) => p + 1)} deshabilitado={pagina >= totalPaginas}/>
                    </View>
                </View>
            </Tarjeta>
        </PortalConduccion>
    );
}

const celda = {
    encabezado: {fontSize: 11, fontWeight: "700" as const, color: "#6b7280", textTransform: "uppercase" as const, letterSpacing: 0.5},
    texto: {fontSize: 13, color: "#374151"},
};