import {useEffect, useState} from "react";
import {Pressable, Text, View, useWindowDimensions} from "react-native";
import {
    BotonAccion, CampoTexto, Cargando, Etiqueta, MensajeError, NotaObligatorios, OpcionesRadio, TextoError,
} from "../../src/components/wizard/Campos";
import {WizardShell, wizardStyles} from "../../src/components/wizard/WizardShell";
import {useFormularioPaso} from "../../src/components/wizard/useFormularioPaso";
import {listarCarreras} from "../../src/lib/api";
import {OPCIONES_COMO_CONOCIO} from "../../src/lib/formulario";
import {LARGO_MINIMO_MOTIVACION, Regla} from "../../src/lib/validaciones";

const SI_NO = [
    {valor: true, texto: "Sí"},
    {valor: false, texto: "No"},
];
const LARGO_MAXIMO_MOTIVACION = 500;

export default function Step3Screen() {
    const {width} = useWindowDimensions();
    const isCompact = width < 860;
    const halfOrFull = isCompact ? wizardStyles.fullField : wizardStyles.halfField;
    const {tramite, valores, campo, set, errores, error, guardando, validarPaso, guardarYSeguir} = useFormularioPaso();
    const [carrera, setCarrera] = useState("");
    const [tienePosgrado, setTienePosgrado] = useState(false);
    const motivacion = String(valores.motivacion ?? "");

    useEffect(() => {
        if (!tramite) return;
        setTienePosgrado(Boolean(tramite.datos.titulo_posgrado));
        listarCarreras()
            .then((carreras) => setCarrera(carreras.find((c) => c.id === tramite.carrera_id)?.nombre ?? ""))
            .catch(() => setCarrera(""));
    }, [tramite?.legajo_id]);

    const cambiosDelPaso = () => {
        const anio = String(valores.anio_graduacion ?? "").trim();
        return {
            titulo_grado: valores.titulo_grado,
            institucion_grado: valores.institucion_grado,
            anio_graduacion: /^\d{4}$/.test(anio) ? Number(anio) : null,
            titulo_posgrado: tienePosgrado ? valores.titulo_posgrado : null,
            motivacion: valores.motivacion,
            trabaja_en_area: valores.trabaja_en_area,
            como_conocio: valores.como_conocio,
            como_conocio_detalle: valores.como_conocio === "OTROS" ? valores.como_conocio_detalle : null,
        };
    };

    function siguiente() {
        const reglas: Record<string, Regla[]> = {
            titulo_grado: ["requerido"],
            institucion_grado: ["requerido"],
            anio_graduacion: ["requerido", "anio"],
            motivacion: ["requerido", "motivacion"],
            como_conocio: ["requerido"],
        };
        if (tienePosgrado) reglas.titulo_posgrado = ["requerido"];
        if (valores.como_conocio === "OTROS") reglas.como_conocio_detalle = ["requerido"];
        if (validarPaso(reglas)) guardarYSeguir(cambiosDelPaso(), "/wizard/step-4");
    }

    return (
        <WizardShell
            currentStep={3}
            title="Antecedentes y Motivaciones"
            subtitle="Información académica y razones para tu postulación."
            aviso={tramite ? <MensajeError mensaje={error}/> : null}
            footer={
                <>
                    <Pressable style={wizardStyles.secondaryButton} onPress={() => guardarYSeguir(cambiosDelPaso(), "/wizard/step-2")}>
                        <Text style={wizardStyles.secondaryButtonText}>‹ Anterior</Text>
                    </Pressable>
                    <BotonAccion texto="Siguiente ›" alPresionar={siguiente} ocupado={guardando}/>
                </>
            }
        >
            {!tramite ? <MensajeError mensaje={error}/> : null}
            {!tramite && !error ? <Cargando/> : null}
            <View style={wizardStyles.section}>
                <Text style={wizardStyles.sectionTitle}>Antecedentes académicos</Text>
                <View style={wizardStyles.twoColumns}>
                    <CampoTexto contenedor={halfOrFull} etiqueta="Título de grado obtenido" requerido placeholder="Ej.: Lic. en Sociología" {...campo("titulo_grado")}/>
                    <CampoTexto contenedor={halfOrFull} etiqueta="Institución" requerido placeholder="Ej.: Universidad Nacional de La Plata" {...campo("institucion_grado")}/>
                    <CampoTexto
                        contenedor={halfOrFull}
                        etiqueta="Año de graduación"
                        requerido
                        placeholder="Ej.: 2019"
                        keyboardType="numeric"
                        maxLength={4}
                        {...campo("anio_graduacion", (t) => t.replace(/\D/g, ""))}
                    />
                    <CampoTexto contenedor={halfOrFull} etiqueta="Carrera a inscribirse" editable={false} value={carrera}/>
                </View>

                <Etiqueta texto="¿Posee otro título de posgrado?"/>
                <OpcionesRadio opciones={SI_NO} valor={tienePosgrado} alCambiar={setTienePosgrado}/>
                {tienePosgrado ? (
                    <CampoTexto
                        contenedor={[wizardStyles.fullField, {marginBottom: 12}]}
                        etiqueta="Título de posgrado"
                        requerido
                        placeholder="Ej.: Especialización en Docencia Universitaria"
                        {...campo("titulo_posgrado")}
                    />
                ) : null}
            </View>

            <View style={wizardStyles.section}>
                <Text style={wizardStyles.sectionTitle}>Motivaciones y perfil</Text>
                <CampoTexto
                    contenedor={wizardStyles.fullField}
                    etiqueta="¿Por qué desea realizar esta carrera?"
                    requerido
                    placeholder="Contanos tus motivaciones y qué esperás de la carrera..."
                    multiline
                    numberOfLines={4}
                    maxLength={LARGO_MAXIMO_MOTIVACION}
                    style={wizardStyles.textArea}
                    {...campo("motivacion")}
                />
                <Text style={{
                    fontSize: 12,
                    textAlign: "right",
                    marginTop: 4,
                    color: motivacion.trim().length >= LARGO_MINIMO_MOTIVACION ? "#047857" : "#6b7280",
                }}>
                    {motivacion.length}/{LARGO_MAXIMO_MOTIVACION} caracteres · mínimo {LARGO_MINIMO_MOTIVACION}
                </Text>

                <View style={{marginTop: 16}}>
                    <Etiqueta texto="¿Actualmente trabaja en el área de la carrera?"/>
                    <OpcionesRadio
                        opciones={SI_NO}
                        valor={valores.trabaja_en_area as boolean | null}
                        alCambiar={(v) => set("trabaja_en_area", v)}
                    />
                </View>

                <View style={[wizardStyles.fullField, {marginTop: 16}]}>
                    <Etiqueta texto="¿Cómo conoció la oferta académica?" requerido/>
                    <OpcionesRadio
                        enFila={false}
                        opciones={OPCIONES_COMO_CONOCIO.map((o) => ({valor: o.valor, texto: o.texto}))}
                        valor={valores.como_conocio as string | null}
                        alCambiar={(v) => set("como_conocio", v)}
                    />
                    <TextoError mensaje={errores.como_conocio}/>
                    {valores.como_conocio === "OTROS" ? (
                        <CampoTexto etiqueta="¿Cuál?" requerido placeholder="Ej.: Una charla en mi trabajo" {...campo("como_conocio_detalle")}/>
                    ) : null}
                </View>
            </View>
            <NotaObligatorios/>
        </WizardShell>
    );
}