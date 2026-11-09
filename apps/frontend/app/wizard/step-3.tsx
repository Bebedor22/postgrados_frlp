import {Link} from "expo-router";
import {useEffect, useState} from "react";
import {Pressable, Text, TextInput, View, useWindowDimensions} from "react-native";
import {BotonAccion, Cargando, MensajeError, OpcionesRadio} from "../../src/components/wizard/Campos";
import {WizardShell, wizardStyles} from "../../src/components/wizard/WizardShell";
import {useFormularioPaso} from "../../src/components/wizard/useFormularioPaso";
import {listarCarreras} from "../../src/lib/api";
import {OPCIONES_COMO_CONOCIO} from "../../src/lib/formulario";

const SI_NO = [
    {valor: true, texto: "Sí"},
    {valor: false, texto: "No"},
];

export default function Step3Screen() {
    const {width} = useWindowDimensions();
    const isCompact = width < 860;
    const halfOrFull = isCompact ? wizardStyles.fullField : wizardStyles.halfField;
    const {tramite, valores, campo, set, error, setError, guardando, guardarYSeguir} = useFormularioPaso();
    const [carrera, setCarrera] = useState("");
    const [tienePosgrado, setTienePosgrado] = useState(false);

    useEffect(() => {
        if (!tramite) return;
        setTienePosgrado(Boolean(tramite.datos.titulo_posgrado));
        listarCarreras()
            .then((carreras) => setCarrera(carreras.find((c) => c.id === tramite.carrera_id)?.nombre ?? ""))
            .catch(() => setCarrera(""));
    }, [tramite?.legajo_id]);

    function siguiente() {
        const anio = String(valores.anio_graduacion ?? "").trim();
        if (anio && !/^\d{4}$/.test(anio)) {
            setError("El año de graduación tiene que tener 4 dígitos.");
            return;
        }
        guardarYSeguir(
            {
                titulo_grado: valores.titulo_grado,
                institucion_grado: valores.institucion_grado,
                anio_graduacion: anio ? Number(anio) : null,
                titulo_posgrado: tienePosgrado ? valores.titulo_posgrado : null,
                motivacion: valores.motivacion,
                trabaja_en_area: valores.trabaja_en_area,
                como_conocio: valores.como_conocio,
                como_conocio_detalle: valores.como_conocio === "OTROS" ? valores.como_conocio_detalle : null,
            },
            "/wizard/step-4",
        );
    }

    return (
        <WizardShell
            currentStep={3}
            title="Antecedentes y Motivaciones"
            subtitle="Información académica y razones para tu postulación."
            footer={
                <>
                    <Link href="/wizard/step-2" asChild>
                        <Pressable style={wizardStyles.secondaryButton}>
                            <Text style={wizardStyles.secondaryButtonText}>‹ Anterior</Text>
                        </Pressable>
                    </Link>
                    <BotonAccion texto="Siguiente ›" alPresionar={siguiente} ocupado={guardando}/>
                </>
            }
        >
            <MensajeError mensaje={error}/>
            {!tramite && !error ? <Cargando/> : null}
            <View style={wizardStyles.section}>
                <Text style={wizardStyles.sectionTitle}>Antecedentes académicos</Text>
                <View style={wizardStyles.twoColumns}>
                    <View style={halfOrFull}>
                        <Text style={wizardStyles.label}>Título de grado obtenido</Text>
                        <TextInput placeholder="Lic. en Sociología" style={wizardStyles.input} {...campo("titulo_grado")}/>
                    </View>
                    <View style={halfOrFull}>
                        <Text style={wizardStyles.label}>Institución</Text>
                        <TextInput placeholder="Universidad Nacional..." style={wizardStyles.input} {...campo("institucion_grado")}/>
                    </View>
                    <View style={halfOrFull}>
                        <Text style={wizardStyles.label}>Año de graduación</Text>
                        <TextInput placeholder="2019" keyboardType="numeric" maxLength={4} style={wizardStyles.input} {...campo("anio_graduacion")}/>
                    </View>
                    <View style={halfOrFull}>
                        <Text style={wizardStyles.label}>Carrera a inscribirse</Text>
                        <TextInput
                            placeholder="Seleccionar maestría/doctorado"
                            style={[wizardStyles.input, {backgroundColor: "#f3f4f6"}]}
                            editable={false}
                            value={carrera}
                        />
                    </View>
                </View>

                <Text style={wizardStyles.label}>¿Posee otro título de posgrado?</Text>
                <OpcionesRadio opciones={SI_NO} valor={tienePosgrado} alCambiar={setTienePosgrado}/>
                {tienePosgrado ? (
                    <View style={[wizardStyles.fullField, {marginBottom: 12}]}>
                        <Text style={wizardStyles.label}>Título de posgrado</Text>
                        <TextInput placeholder="Especialización en..." style={wizardStyles.input} {...campo("titulo_posgrado")}/>
                    </View>
                ) : null}
            </View>

            <View style={wizardStyles.section}>
                <Text style={wizardStyles.sectionTitle}>Motivaciones y perfil</Text>
                <View style={wizardStyles.fullField}>
                    <Text style={wizardStyles.label}>¿Por qué desea realizar esta carrera? (máx. 500 caracteres)</Text>
                    <TextInput
                        placeholder="Describa sus motivaciones..."
                        multiline
                        numberOfLines={4}
                        maxLength={500}
                        style={[wizardStyles.input, wizardStyles.textArea]}
                        {...campo("motivacion")}
                    />
                </View>

                <View style={{marginTop: 20}}>
                    <Text style={wizardStyles.label}>¿Actualmente trabaja en el área de la carrera?</Text>
                    <OpcionesRadio
                        opciones={SI_NO}
                        valor={valores.trabaja_en_area as boolean | null}
                        alCambiar={(v) => set("trabaja_en_area", v)}
                    />
                </View>

                <View style={[wizardStyles.fullField, {marginTop: 20}]}>
                    <Text style={wizardStyles.label}>¿Cómo conoció la oferta académica?</Text>
                    <OpcionesRadio
                        enFila={false}
                        opciones={OPCIONES_COMO_CONOCIO.map((o) => ({valor: o.valor, texto: o.texto}))}
                        valor={valores.como_conocio as string | null}
                        alCambiar={(v) => set("como_conocio", v)}
                    />
                    {valores.como_conocio === "OTROS" ? (
                        <TextInput placeholder="Contanos cómo nos conociste" style={wizardStyles.input} {...campo("como_conocio_detalle")}/>
                    ) : null}
                </View>
            </View>
        </WizardShell>
    );
}