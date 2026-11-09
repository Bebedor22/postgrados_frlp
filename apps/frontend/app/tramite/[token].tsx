/**
 * Estado del trámite del aspirante: se entra con el link personal (token).
 * Muestra el estado, el porcentaje completado, lo que falta, las observaciones
 * del coordinador y el historial. Si se puede editar, permite seguir completando.
 */
import {Link, useLocalSearchParams, useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {Platform, Pressable, Text, View} from "react-native";
import {Cargando, MensajeError} from "../../src/components/wizard/Campos";
import {WizardShell, wizardStyles} from "../../src/components/wizard/WizardShell";
import {ApiError, Tramite, consultarTramite} from "../../src/lib/api";
import {ESTADOS, describirFaltantes} from "../../src/lib/formulario";
import {guardarTokenTramite} from "../../src/lib/sesion";

function formatearFecha(iso: string): string {
    // El backend guarda la hora en UTC sin zona horaria: se marca como UTC para mostrarla en hora local
    const conZona = /(Z|[+-]\d{2}:\d{2})$/.test(iso) ? iso : `${iso}Z`;
    const fecha = new Date(conZona);
    return `${fecha.toLocaleDateString("es-AR")} ${fecha.toLocaleTimeString("es-AR", {hour: "2-digit", minute: "2-digit"})}`;
}

export default function TramiteScreen() {
    const {token} = useLocalSearchParams<{token: string}>();
    const router = useRouter();
    const [tramite, setTramite] = useState<Tramite | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token) return;
        guardarTokenTramite(token);
        consultarTramite(token)
            .then(setTramite)
            .catch((e: ApiError) => setError(e.message));
    }, [token]);

    const estado = tramite ? ESTADOS[tramite.estado] ?? {texto: tramite.estado, color: "#374151", fondo: "#f3f4f6"} : null;
    const observacion = tramite?.estado === "OBSERVADO"
        ? [...tramite.historial].reverse().find((h) => h.estado_nuevo === "OBSERVADO")?.comentario
        : null;
    const pasoPendiente = tramite
        ? Object.entries(tramite.progreso.faltantes_por_paso).find(([, campos]) => campos.length > 0)?.[0] ?? "4"
        : "1";
    const link = Platform.OS === "web" && typeof window !== "undefined" ? window.location.href : `/tramite/${token}`;

    return (
        <WizardShell
            currentStep={0}
            title="Estado de tu inscripción"
            subtitle="Guardá esta página: con este link podés volver a ver tu trámite cuando quieras."
            showCancel={false}
            footer={
                <>
                    <Link href="/" asChild>
                        <Pressable style={wizardStyles.secondaryButton}>
                            <Text style={wizardStyles.secondaryButtonText}>Volver al inicio</Text>
                        </Pressable>
                    </Link>
                    {tramite?.puede_editar ? (
                        <Pressable style={wizardStyles.primaryButton} onPress={() => router.push(`/wizard/step-${pasoPendiente}` as never)}>
                            <Text style={wizardStyles.primaryButtonText}>
                                {tramite.estado === "OBSERVADO" ? "Corregir y reenviar ›" : "Continuar inscripción ›"}
                            </Text>
                        </Pressable>
                    ) : null}
                </>
            }
        >
            <MensajeError mensaje={error}/>
            {!tramite && !error ? <Cargando texto="Buscando tu trámite..."/> : null}

            {tramite && estado ? (
                <>
                    <View style={[wizardStyles.section, {backgroundColor: estado.fondo, borderWidth: 1, borderColor: estado.color}]}>
                        <Text style={{fontSize: 12, color: estado.color, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.6}}>
                            Estado
                        </Text>
                        <Text style={{fontSize: 20, fontWeight: "700", color: estado.color, marginTop: 4}}>{estado.texto}</Text>
                        <Text style={{fontSize: 13, color: "#4b5563", marginTop: 6}}>
                            {tramite.datos.apellido}, {tramite.datos.nombre} · Legajo N° {tramite.numero_legajo}
                        </Text>
                    </View>

                    {observacion ? (
                        <View style={[wizardStyles.section, {backgroundColor: "#fffbeb", borderWidth: 1, borderColor: "#f59e0b"}]}>
                            <Text style={[wizardStyles.sectionTitle, {color: "#b45309"}]}>Observación de la coordinación</Text>
                            <Text style={{fontSize: 14, color: "#78350f"}}>{observacion}</Text>
                        </View>
                    ) : null}

                    <View style={wizardStyles.section}>
                        <Text style={wizardStyles.sectionTitle}>Carga del formulario</Text>
                        <View style={{height: 10, backgroundColor: "#e5e7eb", borderRadius: 5, overflow: "hidden"}}>
                            <View style={{
                                width: `${tramite.progreso.porcentaje}%`,
                                height: "100%",
                                backgroundColor: tramite.progreso.completo ? "#2d7a65" : "#0d2035",
                            }}/>
                        </View>
                        <Text style={{fontSize: 13, color: "#374151", marginTop: 8}}>
                            {tramite.progreso.porcentaje}% completado
                        </Text>
                        {tramite.puede_editar && !tramite.progreso.completo ? (
                            <View style={{marginTop: 10}}>
                                <Text style={wizardStyles.label}>Te falta completar:</Text>
                                {describirFaltantes(tramite.progreso.faltantes_por_paso).map((linea) => (
                                    <Text key={linea} style={{fontSize: 13, color: "#4b5563", marginTop: 2}}>• {linea}</Text>
                                ))}
                            </View>
                        ) : null}
                    </View>

                    <View style={wizardStyles.section}>
                        <Text style={wizardStyles.sectionTitle}>Historial</Text>
                        {tramite.historial.map((cambio, i) => (
                            <View key={i} style={{flexDirection: "row", gap: 10, marginBottom: 10}}>
                                <View style={{width: 8, height: 8, borderRadius: 4, marginTop: 6, backgroundColor: ESTADOS[cambio.estado_nuevo]?.color ?? "#6b7280"}}/>
                                <View style={{flex: 1}}>
                                    <Text style={{fontSize: 13, fontWeight: "600", color: "#111827"}}>
                                        {ESTADOS[cambio.estado_nuevo]?.texto ?? cambio.estado_nuevo}
                                    </Text>
                                    {cambio.comentario ? <Text style={{fontSize: 13, color: "#4b5563"}}>{cambio.comentario}</Text> : null}
                                    <Text style={{fontSize: 11, color: "#9ca3af"}}>{formatearFecha(cambio.fecha)}</Text>
                                </View>
                            </View>
                        ))}
                    </View>

                    <View style={[wizardStyles.section, {backgroundColor: "#f0f9ff", borderWidth: 1, borderColor: "#bae6fd"}]}>
                        <Text style={[wizardStyles.sectionTitle, {color: "#0369a1"}]}>Tu link de seguimiento</Text>
                        <Text selectable style={{fontSize: 12, color: "#0c4a6e"}}>{link}</Text>
                    </View>
                </>
            ) : null}
        </WizardShell>
    );
}