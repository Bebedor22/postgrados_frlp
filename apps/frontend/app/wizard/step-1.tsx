import {useEffect} from "react";
import {Text, View, useWindowDimensions} from "react-native";
import {BotonAccion, CampoTexto, Cargando, Etiqueta, MensajeError, NotaObligatorios, OpcionesRadio} from "../../src/components/wizard/Campos";
import {WizardShell, wizardStyles} from "../../src/components/wizard/WizardShell";
import {useFormularioPaso} from "../../src/components/wizard/useFormularioPaso";
import {fechaAIso, isoAFecha} from "../../src/lib/formulario";
import {enmascararFecha} from "../../src/lib/validaciones";

const GENEROS = ["Femenino", "Masculino", "No binario", "Prefiero no decirlo"].map((g) => ({valor: g, texto: g}));

export default function Step1Screen() {
    const {width} = useWindowDimensions();
    const isCompact = width < 860;
    const halfOrFull = isCompact ? wizardStyles.fullField : wizardStyles.halfField;
    const {tramite, valores, campo, set, error, guardando, validarPaso, guardarYSeguir} = useFormularioPaso();

    // La fecha se edita como DD/MM/AAAA y se guarda como AAAA-MM-DD
    useEffect(() => {
        if (tramite) set("fecha_nacimiento", isoAFecha(tramite.datos.fecha_nacimiento));
    }, [tramite?.legajo_id]);

    function siguiente() {
        const valido = validarPaso({
            nombre: ["requerido"],
            apellido: ["requerido"],
            nacionalidad: ["requerido"],
            fecha_nacimiento: ["requerido", "fecha"],
        });
        if (!valido) return;
        guardarYSeguir(
            {
                nombre: valores.nombre,
                apellido: valores.apellido,
                nacionalidad: valores.nacionalidad,
                fecha_nacimiento: fechaAIso(String(valores.fecha_nacimiento ?? "")) ?? null,
                genero: valores.genero,
            },
            "/wizard/step-2",
        );
    }

    return (
        <WizardShell
            currentStep={1}
            title="Datos Personales"
            subtitle="Completá la información básica del aspirante."
            aviso={tramite ? <MensajeError mensaje={error}/> : null}
            footer={<BotonAccion texto="Siguiente ›" alPresionar={siguiente} ocupado={guardando}/>}
        >
            {!tramite ? <MensajeError mensaje={error}/> : null}
            {!tramite && !error ? <Cargando/> : null}
            <View style={wizardStyles.twoColumns}>
                <CampoTexto contenedor={halfOrFull} etiqueta="Nombre(s)" requerido placeholder="Ej.: Juan" {...campo("nombre")}/>
                <CampoTexto contenedor={halfOrFull} etiqueta="Apellido(s)" requerido placeholder="Ej.: Pérez" {...campo("apellido")}/>
                <CampoTexto
                    contenedor={halfOrFull}
                    etiqueta={valores.tipo_documento === "PASAPORTE" ? "Pasaporte" : "DNI"}
                    editable={false}
                    value={String(valores.numero_documento ?? "")}
                />
                <CampoTexto contenedor={halfOrFull} etiqueta="Nacionalidad" requerido placeholder="Ej.: Argentina" {...campo("nacionalidad")}/>
                <CampoTexto
                    contenedor={halfOrFull}
                    etiqueta="Fecha de nacimiento"
                    requerido
                    placeholder="DD/MM/AAAA"
                    keyboardType="numeric"
                    maxLength={10}
                    {...campo("fecha_nacimiento", enmascararFecha)}
                />
            </View>
            <View style={{marginTop: 4}}>
                <Etiqueta texto="Género (opcional)"/>
                <OpcionesRadio opciones={GENEROS} valor={valores.genero as string | null} alCambiar={(v) => set("genero", v)}/>
            </View>
            <View style={[wizardStyles.radioItem, {marginTop: 8}]}>
                <View style={wizardStyles.checkbox}/>
                <Text style={wizardStyles.checkboxLabel}>¿Posee discapacidad?</Text>
            </View>
            <NotaObligatorios/>
        </WizardShell>
    );
}