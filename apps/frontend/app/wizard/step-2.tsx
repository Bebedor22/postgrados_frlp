import {Link} from "expo-router";
import {Pressable, Text, TextInput, View, useWindowDimensions} from "react-native";
import {BotonAccion, Cargando, MensajeError} from "../../src/components/wizard/Campos";
import {WizardShell, wizardStyles} from "../../src/components/wizard/WizardShell";
import {useFormularioPaso} from "../../src/components/wizard/useFormularioPaso";

const CAMPOS_PASO_2 = [
    "telefono_movil", "telefono_fijo", "email", "email_alternativo",
    "pais", "provincia", "ciudad", "calle", "numero", "piso_depto", "codigo_postal",
];

export default function Step2Screen() {
    const {width} = useWindowDimensions();
    const isCompact = width < 860;
    const halfOrFull = isCompact ? wizardStyles.fullField : wizardStyles.halfField;
    const {tramite, valores, campo, error, guardando, guardarYSeguir} = useFormularioPaso();

    const siguiente = () =>
        guardarYSeguir(Object.fromEntries(CAMPOS_PASO_2.map((c) => [c, valores[c] ?? null])), "/wizard/step-3");

    return (
        <WizardShell
            currentStep={2}
            title="Contacto y Residencia"
            subtitle="Completá los datos de contacto y domicilio."
            footer={
                <>
                    <Link href="/wizard/step-1" asChild>
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
            <View style={wizardStyles.twoColumns}>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Teléfono celular</Text>
                    <TextInput placeholder="+54 9 11 1234-5678" keyboardType="phone-pad" style={wizardStyles.input} {...campo("telefono_movil")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Teléfono fijo (opcional)</Text>
                    <TextInput placeholder="0221 456-7890" keyboardType="phone-pad" style={wizardStyles.input} {...campo("telefono_fijo")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Correo electrónico</Text>
                    <TextInput placeholder="ejemplo@email.com" keyboardType="email-address" autoCapitalize="none" style={wizardStyles.input} {...campo("email")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Correo alternativo (opcional)</Text>
                    <TextInput placeholder="otro@email.com" keyboardType="email-address" autoCapitalize="none" style={wizardStyles.input} {...campo("email_alternativo")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>País</Text>
                    <TextInput placeholder="Argentina" style={wizardStyles.input} {...campo("pais")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Provincia</Text>
                    <TextInput placeholder="Buenos Aires" style={wizardStyles.input} {...campo("provincia")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Localidad</Text>
                    <TextInput placeholder="La Plata" style={wizardStyles.input} {...campo("ciudad")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Calle</Text>
                    <TextInput placeholder="Av. 7" style={wizardStyles.input} {...campo("calle")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Número</Text>
                    <TextInput placeholder="1234" keyboardType="numeric" style={wizardStyles.input} {...campo("numero")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Piso / Depto (opcional)</Text>
                    <TextInput placeholder="2° B" style={wizardStyles.input} {...campo("piso_depto")}/>
                </View>
                <View style={halfOrFull}>
                    <Text style={wizardStyles.label}>Código Postal</Text>
                    <TextInput placeholder="1900" keyboardType="numeric" style={wizardStyles.input} {...campo("codigo_postal")}/>
                </View>
            </View>
        </WizardShell>
    );
}