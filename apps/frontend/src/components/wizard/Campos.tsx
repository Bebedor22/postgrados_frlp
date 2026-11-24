/** Piezas chicas del wizard, armadas con los estilos que ya existen en WizardShell. */
import type {ComponentProps} from "react";
import {ActivityIndicator, Pressable, StyleProp, Text, TextInput, View, ViewStyle} from "react-native";
import {wizardStyles} from "./WizardShell";

const COLOR_PLACEHOLDER = "#9ca3af";
const COLOR_ERROR = "#dc2626";

/** Etiqueta de un campo; si es obligatorio muestra un asterisco rojo. */
export function Etiqueta({texto, requerido}: {texto: string; requerido?: boolean}) {
    return (
        <Text style={wizardStyles.label}>
            {texto}
            {requerido ? <Text style={{color: COLOR_ERROR}}> *</Text> : null}
        </Text>
    );
}

export function TextoError({mensaje}: {mensaje?: string}) {
    if (!mensaje) return null;
    return <Text style={{color: COLOR_ERROR, fontSize: 12, marginTop: 4}}>{mensaje}</Text>;
}

/**
 * Campo de texto del formulario: etiqueta (con * si es obligatorio), ejemplo en
 * gris para no confundirlo con lo escrito, y borde rojo + mensaje si hay error.
 */
export function CampoTexto({
    etiqueta,
    requerido,
    error,
    contenedor,
    editable = true,
    style,
    ...props
}: {
    etiqueta: string;
    requerido?: boolean;
    error?: string;
    contenedor?: StyleProp<ViewStyle>;
} & ComponentProps<typeof TextInput>) {
    return (
        <View style={contenedor}>
            <Etiqueta texto={etiqueta} requerido={requerido && editable}/>
            <TextInput
                placeholderTextColor={COLOR_PLACEHOLDER}
                editable={editable}
                style={[
                    wizardStyles.input,
                    !editable && {backgroundColor: "#f3f4f6", color: "#6b7280"},
                    error ? {borderColor: COLOR_ERROR} : null,
                    style,
                ]}
                {...props}
            />
            <TextoError mensaje={error}/>
        </View>
    );
}

/** Nota al pie de la tarjeta: "* Campos obligatorios". */
export function NotaObligatorios() {
    return (
        <Text style={{fontSize: 12, color: "#6b7280", marginTop: 8}}>
            Los campos marcados con <Text style={{color: COLOR_ERROR}}>*</Text> son obligatorios.
            Tus datos se guardan cada vez que avanzás o volvés de paso.
        </Text>
    );
}

/** Grupo de opciones con los mismos círculos de "radio" del diseño original. */
export function OpcionesRadio<T extends string | boolean>({
    opciones,
    valor,
    alCambiar,
    enFila = true,
}: {
    opciones: {valor: T; texto: string; detalle?: string}[];
    valor: T | null | undefined;
    alCambiar: (valor: T) => void;
    enFila?: boolean;
}) {
    return (
        <View style={enFila ? wizardStyles.radioRow : {gap: 10, marginBottom: 16}}>
            {opciones.map((opcion) => {
                const elegida = opcion.valor === valor;
                return (
                    <Pressable key={String(opcion.valor)} style={wizardStyles.radioItem} onPress={() => alCambiar(opcion.valor)}>
                        <View style={[wizardStyles.radioCircle, elegida && wizardStyles.radioCircleSelected]}>
                            {elegida && <View style={wizardStyles.radioInner}/>}
                        </View>
                        <View>
                            <Text style={[wizardStyles.checkboxLabel, elegida && {fontWeight: "600"}]}>{opcion.texto}</Text>
                            {opcion.detalle ? <Text style={{fontSize: 12, color: "#6b7280"}}>{opcion.detalle}</Text> : null}
                        </View>
                    </Pressable>
                );
            })}
        </View>
    );
}

export function MensajeError({mensaje, lista}: {mensaje?: string | null; lista?: string[]}) {
    if (!mensaje && !lista?.length) return null;
    return (
        <View style={{backgroundColor: "#fef2f2", borderColor: "#fca5a5", borderWidth: 1, borderRadius: 6, padding: 12, marginBottom: 16}}>
            {mensaje ? <Text style={{color: "#b91c1c", fontSize: 13, fontWeight: "600"}}>{mensaje}</Text> : null}
            {lista?.map((linea) => (
                <Text key={linea} style={{color: "#b91c1c", fontSize: 13, marginTop: 4}}>• {linea}</Text>
            ))}
        </View>
    );
}

export function Cargando({texto = "Cargando..."}: {texto?: string}) {
    return (
        <View style={{padding: 24, alignItems: "center", gap: 8}}>
            <ActivityIndicator color="#0d2035"/>
            <Text style={{color: "#6b7280", fontSize: 13}}>{texto}</Text>
        </View>
    );
}

/** Botón principal que muestra "Guardando..." mientras espera al backend. */
export function BotonAccion({texto, alPresionar, ocupado, exito = false}: {
    texto: string;
    alPresionar: () => void;
    ocupado?: boolean;
    exito?: boolean;
}) {
    return (
        <Pressable
            style={[exito ? wizardStyles.successButton : wizardStyles.primaryButton, ocupado && {opacity: 0.6}]}
            onPress={alPresionar}
            disabled={ocupado}
        >
            <Text style={wizardStyles.primaryButtonText}>{ocupado ? "Guardando..." : texto}</Text>
        </Pressable>
    );
}