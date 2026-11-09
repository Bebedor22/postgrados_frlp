import {useEffect, useState} from "react";
import {StyleSheet, Text, TextInput, View, useWindowDimensions} from "react-native";
import {BotonAccion, Cargando, MensajeError} from "../../src/components/wizard/Campos";
import {WizardShell, wizardStyles} from "../../src/components/wizard/WizardShell";
import {useFormularioPaso} from "../../src/components/wizard/useFormularioPaso";
import {fechaAIso, isoAFecha} from "../../src/lib/formulario";

export default function Step1Screen() {
    const {width} = useWindowDimensions();
    const isCompact = width < 860;
    const halfOrFull = isCompact ? wizardStyles.fullField : wizardStyles.halfField;
    const {tramite, valores, campo, error, setError, guardando, guardarYSeguir} = useFormularioPaso();
    const [fecha, setFecha] = useState("");

    useEffect(() => setFecha(isoAFecha(valores.fecha_nacimiento)), [tramite?.legajo_id]);

    function siguiente() {
        const fechaIso = fechaAIso(fecha);
        if (fechaIso === undefined) {
            setError("La fecha de nacimiento tiene que tener el formato DD/MM/AAAA.");
            return;
        }
        guardarYSeguir(
            {
                nombre: valores.nombre,
                apellido: valores.apellido,
                nacionalidad: valores.nacionalidad,
                fecha_nacimiento: fechaIso,
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
            footer={<BotonAccion texto="Siguiente ›" alPresionar={siguiente} ocupado={guardando}/>}
        >
            <MensajeError mensaje={error}/>
            {!tramite && !error ? <Cargando/> : null}
            <View style={wizardStyles.twoColumns}>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Nombre(s)</Text>
                    <TextInput placeholder="Juan" style={wizardStyles.input} {...campo("nombre")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Apellido(s)</Text>
                    <TextInput placeholder="Pérez" style={wizardStyles.input} {...campo("apellido")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>{valores.tipo_documento === "PASAPORTE" ? "Pasaporte" : "DNI"}</Text>
                    <TextInput
                        placeholder="12.345.678"
                        keyboardType="numeric"
                        style={[wizardStyles.input, {backgroundColor: "#f3f4f6"}]}
                        editable={false}
                        value={String(valores.numero_documento ?? "")}
                    />
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Nacionalidad</Text>
                    <TextInput placeholder="Argentina" style={wizardStyles.input} {...campo("nacionalidad")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Fecha de Nacimiento</Text>
                    <TextInput placeholder="DD/MM/AAAA" style={wizardStyles.input} value={fecha} onChangeText={setFecha}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Género</Text>
                    <TextInput placeholder="Seleccionar" style={wizardStyles.input} {...campo("genero")}/>
                </View>
            </View>
            <View style={wizardStyles.radioItem}>
                <View style={wizardStyles.checkbox}/>
                <Text style={wizardStyles.checkboxLabel}>¿Posee discapacidad?</Text>
            </View>
        </WizardShell>
    );
}

const styles = StyleSheet.create({});