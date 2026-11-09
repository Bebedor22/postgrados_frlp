/** Piezas chicas del wizard, armadas con los estilos que ya existen en WizardShell. */
import {ActivityIndicator, Pressable, Text, View} from "react-native";
import {wizardStyles} from "./WizardShell";

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