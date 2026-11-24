import {Pressable, Text, View, useWindowDimensions} from "react-native";
import {BotonAccion, CampoTexto, Cargando, MensajeError, NotaObligatorios} from "../../src/components/wizard/Campos";
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
    const {tramite, valores, campo, error, guardando, validarPaso, guardarYSeguir} = useFormularioPaso();

    const cambiosDelPaso = () => Object.fromEntries(CAMPOS_PASO_2.map((c) => [c, valores[c] ?? null]));

    function siguiente() {
        const valido = validarPaso({
            telefono_movil: ["requerido", "telefono"],
            telefono_fijo: ["telefono"],
            email: ["requerido", "email"],
            email_alternativo: ["email"],
            pais: ["requerido"],
            provincia: ["requerido"],
            ciudad: ["requerido"],
            calle: ["requerido"],
            numero: ["requerido"],
            codigo_postal: ["requerido"],
        });
        if (valido) guardarYSeguir(cambiosDelPaso(), "/wizard/step-3");
    }

    return (
        <WizardShell
            currentStep={2}
            title="Contacto y Residencia"
            subtitle="Completá los datos de contacto y domicilio."
            aviso={tramite ? <MensajeError mensaje={error}/> : null}
            footer={
                <>
                    {/* Volver también guarda lo escrito, sin exigir los obligatorios */}
                    <Pressable style={wizardStyles.secondaryButton} onPress={() => guardarYSeguir(cambiosDelPaso(), "/wizard/step-1")}>
                        <Text style={wizardStyles.secondaryButtonText}>‹ Anterior</Text>
                    </Pressable>
                    <BotonAccion texto="Siguiente ›" alPresionar={siguiente} ocupado={guardando}/>
                </>
            }
        >
            {!tramite ? <MensajeError mensaje={error}/> : null}
            {!tramite && !error ? <Cargando/> : null}
            <View style={wizardStyles.twoColumns}>
                <CampoTexto contenedor={halfOrFull} etiqueta="Teléfono celular" requerido placeholder="Ej.: +54 9 221 123-4567" keyboardType="phone-pad" {...campo("telefono_movil")}/>
                <CampoTexto contenedor={halfOrFull} etiqueta="Teléfono fijo (opcional)" placeholder="Ej.: 0221 456-7890" keyboardType="phone-pad" {...campo("telefono_fijo")}/>
                <CampoTexto contenedor={halfOrFull} etiqueta="Correo electrónico" requerido placeholder="Ej.: nombre@email.com" keyboardType="email-address" autoCapitalize="none" {...campo("email")}/>
                <CampoTexto contenedor={halfOrFull} etiqueta="Correo alternativo (opcional)" placeholder="Ej.: otro@email.com" keyboardType="email-address" autoCapitalize="none" {...campo("email_alternativo")}/>
                <CampoTexto contenedor={halfOrFull} etiqueta="País" requerido placeholder="Ej.: Argentina" {...campo("pais")}/>
                <CampoTexto contenedor={halfOrFull} etiqueta="Provincia" requerido placeholder="Ej.: Buenos Aires" {...campo("provincia")}/>
                <CampoTexto contenedor={halfOrFull} etiqueta="Localidad" requerido placeholder="Ej.: La Plata" {...campo("ciudad")}/>
                <CampoTexto contenedor={halfOrFull} etiqueta="Calle" requerido placeholder="Ej.: Av. 7" {...campo("calle")}/>
                <CampoTexto contenedor={halfOrFull} etiqueta="Número" requerido placeholder="Ej.: 1234" keyboardType="numeric" {...campo("numero")}/>
                <CampoTexto contenedor={halfOrFull} etiqueta="Piso / Depto (opcional)" placeholder="Ej.: 2° B" {...campo("piso_depto")}/>
                <CampoTexto contenedor={halfOrFull} etiqueta="Código postal" requerido placeholder="Ej.: 1900" keyboardType="numeric" {...campo("codigo_postal")}/>
            </View>
            <NotaObligatorios/>
        </WizardShell>
    );
}