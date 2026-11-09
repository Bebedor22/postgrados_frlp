/**
 * Pantalla previa al wizard: el aspirante elige carrera y deja sus datos mínimos.
 * Con eso el backend crea el legajo en BORRADOR y devuelve el token del trámite.
 */
import {useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {Text, TextInput, View, useWindowDimensions} from "react-native";
import {BotonAccion, Cargando, MensajeError, OpcionesRadio} from "../../src/components/wizard/Campos";
import {WizardShell, wizardStyles} from "../../src/components/wizard/WizardShell";
import {ApiError, Carrera, Cohorte, iniciarInscripcion, listarCarreras, listarCohortesAbiertas} from "../../src/lib/api";
import {guardarTokenTramite} from "../../src/lib/sesion";

const TIPOS: Record<Carrera["tipo"], string> = {
    Especializacion: "Especialización",
    Maestria: "Maestría",
    Doctorado: "Doctorado",
};

export default function InicioInscripcionScreen() {
    const router = useRouter();
    const {width} = useWindowDimensions();
    const halfOrFull = width < 860 ? wizardStyles.fullField : wizardStyles.halfField;

    const [carreras, setCarreras] = useState<Carrera[] | null>(null);
    const [cohortes, setCohortes] = useState<Cohorte[]>([]);
    const [carreraId, setCarreraId] = useState<string | null>(null);
    const [cohorteId, setCohorteId] = useState<string | null>(null);
    const [tipoDocumento, setTipoDocumento] = useState<"DNI" | "PASAPORTE">("DNI");
    const [documento, setDocumento] = useState("");
    const [nombre, setNombre] = useState("");
    const [apellido, setApellido] = useState("");
    const [email, setEmail] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [enviando, setEnviando] = useState(false);

    useEffect(() => {
        Promise.all([listarCarreras(), listarCohortesAbiertas()])
            .then(([c, co]) => {
                setCarreras(c);
                setCohortes(co);
                if (co.length === 1) setCohorteId(co[0].id);
            })
            .catch((e: ApiError) => setError(e.message));
    }, []);

    async function comenzar() {
        if (!carreraId || !cohorteId) {
            setError("Elegí la carrera y la cohorte.");
            return;
        }
        if (!documento.trim() || !nombre.trim() || !apellido.trim() || !email.trim()) {
            setError("Completá documento, nombre, apellido y correo electrónico.");
            return;
        }
        setEnviando(true);
        setError(null);
        try {
            const respuesta = await iniciarInscripcion({
                cohorte_id: cohorteId,
                carrera_id: carreraId,
                tipo_documento: tipoDocumento,
                numero_documento: documento.replace(/\./g, "").trim(),
                nombre,
                apellido,
                email,
            });
            guardarTokenTramite(respuesta.token);
            router.push("/wizard/step-1");
        } catch (e) {
            setError((e as ApiError).message);
        } finally {
            setEnviando(false);
        }
    }

    return (
        <WizardShell
            currentStep={0}
            title="Comenzar inscripción"
            subtitle="Elegí la carrera y dejá tus datos básicos. Después vas a poder completar el formulario en 4 pasos, guardar y retomarlo cuando quieras."
            footer={<BotonAccion texto="Comenzar ›" alPresionar={comenzar} ocupado={enviando}/>}
        >
            <MensajeError mensaje={error}/>

            {carreras === null && !error ? <Cargando texto="Buscando carreras disponibles..."/> : null}

            {carreras && cohortes.length === 0 ? (
                <MensajeError mensaje="En este momento no hay cohortes con la inscripción abierta."/>
            ) : null}

            {carreras && cohortes.length > 0 ? (
                <>
                    <View style={wizardStyles.section}>
                        <Text style={wizardStyles.sectionTitle}>Carrera a inscribirse</Text>
                        {carreras.length === 0 ? (
                            <Text style={wizardStyles.checkboxLabel}>Todavía no hay carreras cargadas.</Text>
                        ) : (
                            <OpcionesRadio
                                enFila={false}
                                opciones={carreras.map((c) => ({
                                    valor: c.id,
                                    texto: c.nombre,
                                    detalle: `${TIPOS[c.tipo]} · ${c.duracion_anios} ${c.duracion_anios === 1 ? "año" : "años"}`,
                                }))}
                                valor={carreraId}
                                alCambiar={setCarreraId}
                            />
                        )}
                        {cohortes.length > 1 ? (
                            <>
                                <Text style={wizardStyles.label}>Cohorte</Text>
                                <OpcionesRadio
                                    opciones={cohortes.map((c) => ({valor: c.id, texto: c.nombre}))}
                                    valor={cohorteId}
                                    alCambiar={setCohorteId}
                                />
                            </>
                        ) : (
                            <Text style={{fontSize: 13, color: "#6b7280"}}>Cohorte: {cohortes[0].nombre}</Text>
                        )}
                    </View>

                    <View style={wizardStyles.section}>
                        <Text style={wizardStyles.sectionTitle}>Tus datos</Text>
                        <Text style={wizardStyles.label}>Tipo de documento</Text>
                        <OpcionesRadio
                            opciones={[
                                {valor: "DNI" as const, texto: "DNI"},
                                {valor: "PASAPORTE" as const, texto: "Pasaporte"},
                            ]}
                            valor={tipoDocumento}
                            alCambiar={setTipoDocumento}
                        />
                        <View style={wizardStyles.twoColumns}>
                            <View style={halfOrFull}>
                                <Text style={wizardStyles.label}>{tipoDocumento === "DNI" ? "DNI (sin puntos)" : "Pasaporte"}</Text>
                                <TextInput
                                    placeholder={tipoDocumento === "DNI" ? "12345678" : "AAB123456"}
                                    keyboardType={tipoDocumento === "DNI" ? "numeric" : "default"}
                                    style={wizardStyles.input}
                                    value={documento}
                                    onChangeText={setDocumento}
                                />
                            </View>
                            <View style={halfOrFull}>
                                <Text style={wizardStyles.label}>Correo electrónico</Text>
                                <TextInput
                                    placeholder="ejemplo@email.com"
                                    keyboardType="email-address"
                                    autoCapitalize="none"
                                    style={wizardStyles.input}
                                    value={email}
                                    onChangeText={setEmail}
                                />
                            </View>
                            <View style={halfOrFull}>
                                <Text style={wizardStyles.label}>Nombre(s)</Text>
                                <TextInput placeholder="Juan" style={wizardStyles.input} value={nombre} onChangeText={setNombre}/>
                            </View>
                            <View style={halfOrFull}>
                                <Text style={wizardStyles.label}>Apellido(s)</Text>
                                <TextInput placeholder="Pérez" style={wizardStyles.input} value={apellido} onChangeText={setApellido}/>
                            </View>
                        </View>
                    </View>
                </>
            ) : null}
        </WizardShell>
    );
}