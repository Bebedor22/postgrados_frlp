/**
 * Detalle de un legajo para la conducción: todos los datos del aspirante,
 * la carga del formulario, los documentos PDF, el historial y las acciones del workflow.
 * Las acciones que se muestran dependen del estado; el backend vuelve a
 * validar cada cambio (si no corresponde responde 409).
 */
import {useLocalSearchParams, useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {ActivityIndicator, Text, TextInput, View, useWindowDimensions} from "react-native";
import {
    Boton, InsigniaEstado, PortalConduccion, Tarjeta, useUsuarioConduccion,
} from "../../../src/components/conduccion/PortalConduccion";
import {SemaforoBadge} from "../../../src/components/conduccion/Semaforo";
import {ListaDocumentos} from "../../../src/components/wizard/ListaDocumentos";
import {
    AccionLegajo, ApiError, DetalleLegajo, SemaforoFila, TrabajoFinal, accionLegajo,
    descargarDocumento, detalleLegajo, fijarSemaforo, listarCarreras, obtenerTrabajoFinal,
    semaforoDeLegajo,
} from "../../../src/lib/api";
import {abrirPdfDescargado} from "../../../src/lib/documentos";
import {ESTADOS, OPCIONES_COMO_CONOCIO, isoAFecha} from "../../../src/lib/formulario";

type Dato = [etiqueta: string, valor: string];

function texto(valor: unknown): string {
    if (valor === null || valor === undefined || valor === "") return "—";
    if (typeof valor === "boolean") return valor ? "Sí" : "No";
    return String(valor);
}

function secciones(d: DetalleLegajo["datos"], carrera: string): [string, Dato[]][] {
    const domicilio = [d.calle, d.numero, d.piso_depto].filter(Boolean).join(" ");
    const comoConocio = OPCIONES_COMO_CONOCIO.find((o) => o.valor === d.como_conocio)?.texto ?? d.como_conocio;
    return [
        ["Datos personales", [
            ["Apellido y nombre", `${texto(d.apellido)}, ${texto(d.nombre)}`],
            [d.tipo_documento === "PASAPORTE" ? "Pasaporte" : "DNI", texto(d.numero_documento)],
            ["Nacionalidad", texto(d.nacionalidad)],
            ["Fecha de nacimiento", texto(isoAFecha(d.fecha_nacimiento))],
            ["Género", texto(d.genero)],
        ]],
        ["Contacto y residencia", [
            ["Correo electrónico", texto(d.email)],
            ["Correo alternativo", texto(d.email_alternativo)],
            ["Teléfono celular", texto(d.telefono_movil)],
            ["Teléfono fijo", texto(d.telefono_fijo)],
            ["Domicilio", texto(domicilio)],
            ["Localidad", `${texto(d.ciudad)} (CP ${texto(d.codigo_postal)})`],
            ["Provincia / País", `${texto(d.provincia)}, ${texto(d.pais)}`],
        ]],
        ["Antecedentes y motivaciones", [
            ["Carrera", carrera || "—"],
            ["Título de grado", `${texto(d.titulo_grado)} — ${texto(d.institucion_grado)} (${texto(d.anio_graduacion)})`],
            ["Otro título de posgrado", texto(d.titulo_posgrado)],
            ["Trabaja en el área", texto(d.trabaja_en_area)],
            ["Cómo conoció la oferta", `${texto(comoConocio)}${d.como_conocio_detalle ? `: ${d.como_conocio_detalle}` : ""}`],
            ["Motivación", texto(d.motivacion)],
        ]],
        ["Beca", [
            ["Solicita beca", d.solicita_beca ? `Sí, del ${texto(d.tipo_beca)}%` : "No"],
        ]],
    ];
}

function formatearFecha(iso: string): string {
    const conZona = /(Z|[+-]\d{2}:\d{2})$/.test(iso) ? iso : `${iso}Z`;
    const fecha = new Date(conZona);
    return `${fecha.toLocaleDateString("es-AR")} ${fecha.toLocaleTimeString("es-AR", {hour: "2-digit", minute: "2-digit"})}`;
}

export default function DetalleLegajoScreen() {
    const {id} = useLocalSearchParams<{id: string}>();
    const router = useRouter();
    const usuario = useUsuarioConduccion();
    const {width} = useWindowDimensions();
    const compacto = width < 860;

    const [legajo, setLegajo] = useState<DetalleLegajo | null>(null);
    const [carrera, setCarrera] = useState("");
    const [semaforo, setSemaforo] = useState<SemaforoFila | null>(null);
    const [trabajoFinal, setTrabajoFinal] = useState<TrabajoFinal | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [exito, setExito] = useState<string | null>(null);
    const [pidiendoTexto, setPidiendoTexto] = useState<"observar" | "rechazar" | "baja" | null>(null);
    const [comentario, setComentario] = useState("");
    const [procesando, setProcesando] = useState(false);

    function cargar() {
        detalleLegajo(id)
            .then((l) => {
                setLegajo(l);
                listarCarreras().then((c) => setCarrera(c.find((x) => x.id === l.carrera_id)?.nombre ?? ""));
                if (l.estado === "ACTIVO" || l.estado === "GRADUADO") {
                    obtenerTrabajoFinal(id).then(setTrabajoFinal).catch(() => setTrabajoFinal(null));
                    if (usuario?.rol === "COORDINADOR") {
                        semaforoDeLegajo(id).then(setSemaforo).catch(() => setSemaforo(null));
                    }
                }
            })
            .catch((e: ApiError) => (e.status === 401 ? router.replace("/login") : setError(e.message)));
    }

    async function cambiarVerde(manual: boolean) {
        try {
            setSemaforo(await fijarSemaforo(id, manual));
            setExito(manual
                ? "VERDE fijado manualmente: el recálculo no lo va a pisar."
                : "Cálculo automático restaurado.");
        } catch (e) {
            setError((e as ApiError).message);
        }
    }

    useEffect(() => {
        if (usuario && id) cargar();
    }, [usuario, id]);

    async function ejecutar(accion: AccionLegajo, mensaje: string) {
        setProcesando(true);
        setError(null);
        setExito(null);
        try {
            const r = await accionLegajo(id, accion, comentario.trim() || undefined);
            setExito(accion === "aprobar" ? `${mensaje} Número de legajo asignado: ${r.numero_legajo}.` : mensaje);
            setPidiendoTexto(null);
            setComentario("");
            cargar();
        } catch (e) {
            setError((e as ApiError).message);
        } finally {
            setProcesando(false);
        }
    }

    function verDocumento(documentoId: string) {
        setError(null);
        abrirPdfDescargado(() => descargarDocumento(documentoId)).catch((e: ApiError) => setError(e.message));
    }

    const documentosFaltantes = legajo?.documentos.filter((d) => d.obligatorio && !d.presentado).length ?? 0;
    const estado = legajo ? ESTADOS[legajo.estado] ?? {texto: legajo.estado, color: "#374151", fondo: "#f3f4f6"} : null;
    const esCoordinador = usuario?.rol === "COORDINADOR";
    const e = legajo?.estado;

    return (
        <PortalConduccion
            usuario={usuario}
            titulo={legajo ? `Legajo de ${legajo.datos.apellido}, ${legajo.datos.nombre}` : "Legajo"}
            accion={<Boton texto="‹ Volver a la lista" tipo="secundario" alPresionar={() => router.push("/conduccion")}/>}
        >
            {error ? (
                <Tarjeta estilo={{borderColor: "#fca5a5", backgroundColor: "#fef2f2"}}>
                    <Text style={{color: "#b91c1c", fontSize: 13}}>{error}</Text>
                </Tarjeta>
            ) : null}
            {exito ? (
                <Tarjeta estilo={{borderColor: "#86efac", backgroundColor: "#f0fdf4"}}>
                    <Text style={{color: "#047857", fontSize: 13, fontWeight: "600"}}>✓ {exito}</Text>
                </Tarjeta>
            ) : null}

            {!legajo || !estado ? (
                !error ? <View style={{padding: 32, alignItems: "center"}}><ActivityIndicator color="#0d2035"/></View> : null
            ) : (
                <>
                    {/* Estado y acciones */}
                    <Tarjeta>
                        <View style={{flexDirection: compacto ? "column" : "row", justifyContent: "space-between", gap: 12}}>
                            <View style={{gap: 6}}>
                                <InsigniaEstado texto={estado.texto} color={estado.color} fondo={estado.fondo}/>
                                <Text style={{fontSize: 13, color: "#4b5563"}}>
                                    Legajo N° {legajo.numero_legajo} · Formulario {legajo.progreso.porcentaje}% completo
                                </Text>
                                {legajo.reserva_vence_el ? (
                                    <Text style={{fontSize: 13, color: "#b45309"}}>
                                        Reserva de vacante hasta el {isoAFecha(legajo.reserva_vence_el)}
                                    </Text>
                                ) : null}
                            </View>
                            {esCoordinador ? (
                                <View style={{flexDirection: "row", flexWrap: "wrap", gap: 8, alignItems: "flex-start"}}>
                                    {e === "PENDIENTE" ? (
                                        <Boton texto="Tomar para revisión" alPresionar={() => ejecutar("revisar", "El legajo quedó en revisión.")} deshabilitado={procesando}/>
                                    ) : null}
                                    {e === "EN_REVISION" ? (
                                        <Boton texto="Aprobar" tipo="exito" alPresionar={() => ejecutar("aprobar", "Legajo aprobado.")} deshabilitado={procesando}/>
                                    ) : null}
                                    {e === "PENDIENTE" || e === "EN_REVISION" ? (
                                        <Boton texto="Observar" tipo="secundario" alPresionar={() => setPidiendoTexto("observar")} deshabilitado={procesando}/>
                                    ) : null}
                                    {e === "EN_REVISION" ? (
                                        <Boton texto="Rechazar" tipo="peligro" alPresionar={() => setPidiendoTexto("rechazar")} deshabilitado={procesando}/>
                                    ) : null}
                                    {e === "COMPLETADO" ? (
                                        <Boton texto="Matricular" tipo="exito" alPresionar={() => ejecutar("matricular", "El aspirante pasó a estudiante activo.")} deshabilitado={procesando}/>
                                    ) : null}
                                    {e === "ACTIVO" ? (
                                        <Boton texto="Graduar" tipo="exito" alPresionar={() => ejecutar("graduar", "El legajo quedó graduado.")} deshabilitado={procesando}/>
                                    ) : null}
                                    {e === "COMPLETADO" || e === "ACTIVO" ? (
                                        <Boton texto="Dar de baja" tipo="peligro" alPresionar={() => setPidiendoTexto("baja")} deshabilitado={procesando}/>
                                    ) : null}
                                </View>
                            ) : (
                                <Text style={{fontSize: 12, color: "#6b7280"}}>Vista de solo lectura (Dirección de Posgrado).</Text>
                            )}
                        </View>

                        {pidiendoTexto ? (
                            <View style={{marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: "#f3f4f6", gap: 8}}>
                                <Text style={{fontSize: 13, fontWeight: "600", color: "#111827"}}>
                                    {{
                                        observar: "¿Qué tiene que corregir el aspirante? (lo recibe por email y lo ve en su trámite)",
                                        rechazar: "Motivo del rechazo",
                                        baja: "Motivo de la baja",
                                    }[pidiendoTexto]}
                                </Text>
                                <TextInput
                                    value={comentario}
                                    onChangeText={setComentario}
                                    multiline
                                    numberOfLines={3}
                                    placeholder={{
                                        observar: "Ej.: Falta adjuntar la copia del título de grado",
                                        rechazar: "Ej.: La documentación presentada no es válida",
                                        baja: "Ej.: El estudiante pidió la baja por motivos personales",
                                    }[pidiendoTexto]}
                                    placeholderTextColor="#9ca3af"
                                    style={{
                                        borderWidth: 1, borderColor: "#d1d5db", borderRadius: 6, padding: 10,
                                        minHeight: 72, fontSize: 14, textAlignVertical: "top",
                                    }}
                                />
                                <Text style={{fontSize: 12, color: comentario.trim().length < 10 ? "#6b7280" : "#047857"}}>
                                    Mínimo 10 caracteres ({comentario.trim().length})
                                </Text>
                                <View style={{flexDirection: "row", gap: 8}}>
                                    <Boton
                                        texto={{observar: "Enviar observación", rechazar: "Confirmar rechazo", baja: "Confirmar baja"}[pidiendoTexto]}
                                        tipo={pidiendoTexto === "observar" ? "principal" : "peligro"}
                                        deshabilitado={procesando || comentario.trim().length < 10}
                                        alPresionar={() =>
                                            ejecutar(
                                                pidiendoTexto,
                                                {
                                                    observar: "Observación enviada al aspirante.",
                                                    rechazar: "Legajo rechazado.",
                                                    baja: "El legajo fue dado de baja.",
                                                }[pidiendoTexto],
                                            )
                                        }
                                    />
                                    <Boton texto="Cancelar" tipo="secundario" alPresionar={() => { setPidiendoTexto(null); setComentario(""); }}/>
                                </View>
                            </View>
                        ) : null}
                    </Tarjeta>

                    {semaforo || trabajoFinal ? (
                        <Tarjeta titulo="Seguimiento de graduación (Módulo C)">
                            {semaforo ? (
                                <View style={{gap: 8}}>
                                    <View style={{flexDirection: "row", alignItems: "center", gap: 12, flexWrap: "wrap"}}>
                                        <SemaforoBadge color={semaforo.semaforo}/>
                                        <Text style={{fontSize: 13, color: "#374151"}}>
                                            {semaforo.seminarios_aprobados}/{semaforo.seminarios_obligatorios_total} obligatorios aprobados
                                            {semaforo.seminarios_adeudados > 0 ? ` · ${semaforo.seminarios_adeudados} adeudados` : ""}
                                            {semaforo.dias_en_riesgo > 0 ? ` · ${semaforo.dias_en_riesgo} días en este color` : ""}
                                        </Text>
                                        {esCoordinador ? (
                                            <Boton
                                                texto={semaforo.semaforo_manual ? "Restaurar cálculo" : "Fijar VERDE"}
                                                tipo="secundario"
                                                alPresionar={() => cambiarVerde(!semaforo.semaforo_manual)}
                                            />
                                        ) : null}
                                    </View>
                                    {semaforo.semaforo_manual ? (
                                        <Text style={{fontSize: 11, color: "#92400e"}}>
                                            VERDE manual (BR-008): el recálculo automático lo respeta.
                                        </Text>
                                    ) : null}
                                </View>
                            ) : null}
                            <View style={{marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: "#f3f4f6"}}>
                                <Text style={{fontSize: 11, color: "#374151", fontWeight: "700", marginBottom: 4}}>
                                    TRABAJO FINAL / TESIS
                                </Text>
                                {trabajoFinal ? (
                                    <Text style={{fontSize: 13, color: "#374151", lineHeight: 1.7}}>
                                        {trabajoFinal.tipo} · {trabajoFinal.titulo}{"\n"}
                                        Director: {trabajoFinal.director_nombre}{"\n"}
                                        Aprobación CPR: {isoAFecha(trabajoFinal.fecha_aprobacion_cpr)}
                                        {trabajoFinal.numero_resolucion ? ` · Res. ${trabajoFinal.numero_resolucion}` : ""}
                                    </Text>
                                ) : (
                                    <Text style={{fontSize: 13, color: "#6b7280"}}>
                                        Sin trabajo final registrado (lo carga el CPR).
                                    </Text>
                                )}
                            </View>
                        </Tarjeta>
                    ) : null}

                    <View style={{flexDirection: compacto ? "column" : "row", gap: 16, alignItems: "flex-start"}}>
                        {/* Datos del formulario */}
                        <View style={{flex: 2, gap: 16, width: compacto ? "100%" : undefined}}>
                            {secciones(legajo.datos, carrera).map(([titulo, datos]) => (
                                <Tarjeta key={titulo} titulo={titulo}>
                                    {datos.map(([etiqueta, valor]) => (
                                        <View key={etiqueta} style={{flexDirection: compacto ? "column" : "row", paddingVertical: 6, gap: compacto ? 2 : 12}}>
                                            <Text style={{width: compacto ? undefined : 180, fontSize: 13, color: "#6b7280"}}>{etiqueta}</Text>
                                            <Text style={{flex: 1, fontSize: 13, color: "#111827"}}>{valor}</Text>
                                        </View>
                                    ))}
                                </Tarjeta>
                            ))}
                        </View>

                        {/* Documentos e historial de estados */}
                        <View style={{flex: 1, gap: 16, width: compacto ? "100%" : undefined}}>
                            <Tarjeta titulo="Documentación">
                                {documentosFaltantes > 0 ? (
                                    <Text style={{fontSize: 12, color: "#b45309", marginBottom: 10}}>
                                        Faltan {documentosFaltantes} documento{documentosFaltantes === 1 ? "" : "s"} obligatorio{documentosFaltantes === 1 ? "" : "s"}.
                                    </Text>
                                ) : null}
                                <ListaDocumentos requisitos={legajo.documentos} alVer={(d) => verDocumento(d.id)}/>
                            </Tarjeta>
                            <Tarjeta titulo="Historial">
                                {[...legajo.historial].reverse().map((cambio, i) => (
                                    <View key={i} style={{flexDirection: "row", gap: 10, marginBottom: 12}}>
                                        <View style={{
                                            width: 8, height: 8, borderRadius: 4, marginTop: 6,
                                            backgroundColor: ESTADOS[cambio.estado_nuevo]?.color ?? "#6b7280",
                                        }}/>
                                        <View style={{flex: 1}}>
                                            <Text style={{fontSize: 13, fontWeight: "600", color: "#111827"}}>
                                                {ESTADOS[cambio.estado_nuevo]?.texto ?? cambio.estado_nuevo}
                                            </Text>
                                            {cambio.comentario ? <Text style={{fontSize: 13, color: "#4b5563"}}>{cambio.comentario}</Text> : null}
                                            <Text style={{fontSize: 11, color: "#9ca3af"}}>{formatearFecha(cambio.fecha)}</Text>
                                        </View>
                                    </View>
                                ))}
                            </Tarjeta>
                        </View>
                    </View>
                </>
            )}
        </PortalConduccion>
    );
}