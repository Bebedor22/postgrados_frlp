import {useState} from "react";
import {Link, useRouter} from "expo-router";
import {Alert, Pressable, Text, View} from "react-native";
import {BotonAccion, Cargando, MensajeError} from "../../src/components/wizard/Campos";
import {WizardShell, wizardStyles} from "../../src/components/wizard/WizardShell";
import {useFormularioPaso} from "../../src/components/wizard/useFormularioPaso";
import {ApiError, confirmarInscripcion} from "../../src/lib/api";
import {describirFaltantes} from "../../src/lib/formulario";
import {scheduleTestNotification} from "../../src/lib/notifications";

const TIPOS_DE_BECA = [
    {valor: "30", titulo: "Beca parcial (30%)", detalle: "Descuento sobre el arancel"},
    {valor: "100", titulo: "Beca completa (100%)", detalle: "Exención total del arancel"},
];

export default function Step4Screen() {
    const router = useRouter();
    const [scheduled, setScheduled] = useState(false);
    const {token, tramite, valores, set, error, setError, guardando, setGuardando, guardarYSeguir} = useFormularioPaso();
    const [faltantes, setFaltantes] = useState<string[]>([]);
    const solicitaBeca = Boolean(valores.solicita_beca);

    async function enviar() {
        setFaltantes([]);
        // 1) Guardar la beca  2) Confirmar: BORRADOR → PENDIENTE
        const guardado = await guardarYSeguir({
            solicita_beca: solicitaBeca,
            tipo_beca: solicitaBeca ? valores.tipo_beca : null,
        });
        if (!guardado || !token) return;
        if (!guardado.progreso.completo) {
            setError("Todavía faltan datos para enviar la inscripción:");
            setFaltantes(describirFaltantes(guardado.progreso.faltantes_por_paso));
            return;
        }
        setGuardando(true);
        try {
            await confirmarInscripcion(token);
            router.replace(`/tramite/${token}`);
        } catch (e) {
            setError((e as ApiError).message);
        } finally {
            setGuardando(false);
        }
    }

    const docs = [
        "DNI (frente y dorso)",
        "Título universitario (o constancia en trámite)",
        "Certificado analítico",
        "Partida de nacimiento",
        "Foto carnet (fondo blanco)",
        "CV actualizado",
    ];

    return (
        <WizardShell
            currentStep={4}
            title="Documentación y Archivos"
            subtitle="Subí los documentos requeridos para completar tu inscripción."
            footer={
                <>
                    <Link href="/wizard/step-3" asChild>
                        <Pressable style={wizardStyles.secondaryButton}>
                            <Text style={wizardStyles.secondaryButtonText}>‹ Anterior</Text>
                        </Pressable>
                    </Link>
                    <BotonAccion texto="Enviar Inscripción ✓" alPresionar={enviar} ocupado={guardando} exito/>
                </>
            }
        >
            <MensajeError mensaje={error} lista={faltantes}/>
            {!tramite && !error ? <Cargando/> : null}
            <Text style={{marginBottom: 12, color: "#6b7280", fontSize: 13}}>
                La carga de archivos se habilita en la próxima versión. Por ahora podés enviar la inscripción con tus datos.
            </Text>
            <View style={{marginBottom: 20}}>
                {docs.map((doc, idx) => (
                    <View key={idx} style={wizardStyles.dropzone}>
                        <View>
                            <Text style={wizardStyles.dropzoneText}>{doc}</Text>
                            <Text style={wizardStyles.dropzoneSubtext}>PDF, JPG, PNG · máx. 5 MB</Text>
                        </View>
                        <Pressable style={wizardStyles.dropzoneAction}>
                            <Text style={wizardStyles.dropzoneActionText}>Seleccionar</Text>
                        </Pressable>
                    </View>
                ))}
            </View>

            <View style={[wizardStyles.section, {backgroundColor: "#f0f9ff", borderColor: "#bae6fd", borderWidth: 1}]}>
                <Text style={[wizardStyles.sectionTitle, {color: "#0369a1"}]}>Solicitud de Beca (opcional)</Text>

                <Pressable
                    style={wizardStyles.radioItem}
                    onPress={() => set("solicita_beca", !solicitaBeca)}
                >
                    <View style={[wizardStyles.checkbox, solicitaBeca && {
                        backgroundColor: "#0d2035",
                        borderColor: "#0d2035"
                    }]}>
                        {solicitaBeca && <Text style={{color: "white", fontSize: 10, textAlign: "center"}}>✓</Text>}
                    </View>
                    <Text style={wizardStyles.checkboxLabel}>Deseo solicitar una beca para esta carrera</Text>
                </Pressable>

                {solicitaBeca && (
                    <View style={{marginTop: 16, paddingLeft: 24}}>
                        <Text style={wizardStyles.label}>Tipo de beca solicitada:</Text>
                        <View style={{gap: 10, marginBottom: 16}}>
                            {TIPOS_DE_BECA.map((beca) => {
                                const elegida = valores.tipo_beca === beca.valor;
                                return (
                                    <Pressable
                                        key={beca.valor}
                                        onPress={() => set("tipo_beca", beca.valor)}
                                        style={[wizardStyles.section, {
                                            backgroundColor: "white",
                                            borderWidth: 1,
                                            borderColor: elegida ? "#0d2035" : "#d1d5db",
                                            padding: 12
                                        }]}
                                    >
                                        <View style={wizardStyles.radioItem}>
                                            <View style={[wizardStyles.radioCircle, elegida && wizardStyles.radioCircleSelected]}>
                                                {elegida && <View style={wizardStyles.radioInner}/>}
                                            </View>
                                            <View>
                                                <Text style={{fontSize: 13, fontWeight: "600"}}>{beca.titulo}</Text>
                                                <Text style={{fontSize: 12, color: "#6b7280"}}>{beca.detalle}</Text>
                                            </View>
                                        </View>
                                    </Pressable>
                                );
                            })}
                        </View>

                        <Text style={wizardStyles.label}>Formulario de solicitud de beca:</Text>
                        <View style={wizardStyles.dropzone}>
                            <Text style={wizardStyles.dropzoneText}>Formulario firmado</Text>
                            <Pressable style={wizardStyles.dropzoneAction}>
                                <Text style={wizardStyles.dropzoneActionText}>Seleccionar</Text>
                            </Pressable>
                        </View>
                    </View>
                )}
            </View>

            <View style={[wizardStyles.section, {marginTop: 20}]}>
                <Text style={wizardStyles.sectionTitle}>Prueba de Notificaciones</Text>
                <Text style={wizardStyles.stepSubtitle}>
                    Podés probar el sistema de notificaciones local antes de finalizar.
                </Text>
                <Pressable
                    style={wizardStyles.secondaryButton}
                    onPress={async () => {
                        await scheduleTestNotification();
                        setScheduled(true);
                        Alert.alert("Notificación", "Se programó una notificación de prueba.");
                    }}
                >
                    <Text style={wizardStyles.secondaryButtonText}>Probar notificación</Text>
                </Pressable>
                {scheduled && (
                    <Text style={{color: "#2d7a65", fontWeight: "600", marginTop: 8, fontSize: 12}}>
                        ✓ Notificación programada correctamente
                    </Text>
                )}
            </View>
        </WizardShell>
    );
}