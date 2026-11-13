/**
 * Paso 4: documentación (PDFs) y beca. Desde acá se envía la inscripción.
 *
 * Los documentos se suben apenas se eligen: no hace falta "guardar". La lista de
 * documentos la arma el backend según lo declarado (si pidió beca, se agrega el
 * formulario de beca; si declaró un título de posgrado, se pide su copia).
 */
import {useState} from "react";
import {useRouter} from "expo-router";
import {Pressable, Text, View} from "react-native";
import {BotonAccion, Cargando, Etiqueta, MensajeError, TextoError} from "../../src/components/wizard/Campos";
import {ListaDocumentos} from "../../src/components/wizard/ListaDocumentos";
import {WizardShell, wizardStyles} from "../../src/components/wizard/WizardShell";
import {useFormularioPaso} from "../../src/components/wizard/useFormularioPaso";
import {ApiError, confirmarInscripcion, eliminarDocumento, subirDocumento, urlDocumentoPropio} from "../../src/lib/api";
import {abrirEnPestania} from "../../src/lib/documentos";
import {describirFaltantes} from "../../src/lib/formulario";

const TIPOS_DE_BECA = [
    {valor: "30", titulo: "Beca parcial (30%)", detalle: "Descuento sobre el arancel"},
    {valor: "100", titulo: "Beca completa (100%)", detalle: "Exención total del arancel"},
];

export default function Step4Screen() {
    const router = useRouter();
    const {
        token, tramite, valores, set, errores, error, setError, guardando, setGuardando, validarPaso, guardarYSeguir,
        recargar,
    } = useFormularioPaso();
    const [faltantes, setFaltantes] = useState<string[]>([]);
    const [resaltarDocumentos, setResaltarDocumentos] = useState(false);
    const solicitaBeca = Boolean(valores.solicita_beca);

    const cambiosDelPaso = () => ({
        solicita_beca: solicitaBeca,
        tipo_beca: solicitaBeca ? valores.tipo_beca : null,
    });

    /** Al marcar o desmarcar la beca se guarda enseguida: así aparece (o no) el formulario de beca en la lista. */
    async function cambiarBeca() {
        const nuevo = !solicitaBeca;
        set("solicita_beca", nuevo);
        set("tipo_beca", null);
        await guardarYSeguir({solicita_beca: nuevo, tipo_beca: null});
    }

    async function subir(tipo: string, archivo: File) {
        if (!token) return;
        await subirDocumento(token, tipo, archivo, archivo.name);
        await recargar();
    }

    async function quitar(documentoId: string) {
        if (!token) return;
        await eliminarDocumento(token, documentoId);
        await recargar();
    }

    async function enviar() {
        setFaltantes([]);
        if (solicitaBeca && !validarPaso({tipo_beca: ["requerido"]})) return;
        // 1) Guardar la beca  2) Controlar formulario y documentos  3) Confirmar: BORRADOR → PENDIENTE
        const guardado = await guardarYSeguir(cambiosDelPaso());
        if (!guardado || !token) return;
        const documentosFaltantes = guardado.documentos.filter((d) => d.obligatorio && !d.presentado);
        if (!guardado.progreso.completo || documentosFaltantes.length > 0) {
            setError("Todavía faltan datos para enviar la inscripción:");
            setFaltantes([
                ...describirFaltantes(guardado.progreso.faltantes_por_paso),
                ...(documentosFaltantes.length
                    ? [`Documentos: ${documentosFaltantes.map((d) => d.descripcion).join(", ")}`]
                    : []),
            ]);
            setResaltarDocumentos(true);
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

    return (
        <WizardShell
            currentStep={4}
            title="Documentación y Archivos"
            subtitle="Adjuntá los documentos escaneados en PDF. Se guardan apenas los elegís."
            aviso={tramite ? <MensajeError mensaje={error} lista={faltantes}/> : null}
            footer={
                <>
                    <Pressable style={wizardStyles.secondaryButton} onPress={() => guardarYSeguir(cambiosDelPaso(), "/wizard/step-3")}>
                        <Text style={wizardStyles.secondaryButtonText}>‹ Anterior</Text>
                    </Pressable>
                    <BotonAccion texto="Enviar Inscripción ✓" alPresionar={enviar} ocupado={guardando} exito/>
                </>
            }
        >
            {!tramite ? <MensajeError mensaje={error}/> : null}
            {!tramite && !error ? <Cargando/> : null}

            {tramite ? (
                <>
                    <View style={wizardStyles.section}>
                        <Text style={wizardStyles.sectionTitle}>Documentos</Text>
                        <Text style={{marginBottom: 12, color: "#6b7280", fontSize: 13}}>
                            Los marcados con <Text style={{color: "#dc2626"}}>*</Text> son obligatorios para enviar la
                            inscripción. Si subís otro archivo del mismo tipo, reemplaza al anterior.
                        </Text>
                        <ListaDocumentos
                            requisitos={tramite.documentos}
                            resaltarFaltantes={resaltarDocumentos}
                            alVer={(d) => token && abrirEnPestania(urlDocumentoPropio(token, d.id))}
                            alSubir={subir}
                            alQuitar={(d) => quitar(d.id)}
                        />
                    </View>

                    <View style={[wizardStyles.section, {backgroundColor: "#f0f9ff", borderColor: "#bae6fd", borderWidth: 1}]}>
                        <Text style={[wizardStyles.sectionTitle, {color: "#0369a1"}]}>Solicitud de Beca (opcional)</Text>

                        <Pressable style={wizardStyles.radioItem} onPress={cambiarBeca} disabled={guardando}>
                            <View style={[wizardStyles.checkbox, solicitaBeca && {backgroundColor: "#0d2035", borderColor: "#0d2035"}]}>
                                {solicitaBeca && <Text style={{color: "white", fontSize: 10, textAlign: "center"}}>✓</Text>}
                            </View>
                            <Text style={wizardStyles.checkboxLabel}>Deseo solicitar una beca para esta carrera</Text>
                        </Pressable>

                        {solicitaBeca && (
                            <View style={{marginTop: 16, paddingLeft: 24}}>
                                <Etiqueta texto="Tipo de beca solicitada" requerido/>
                                <View style={{gap: 10, marginBottom: 12}}>
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
                                                    padding: 12,
                                                    marginBottom: 0,
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
                                    <TextoError mensaje={errores.tipo_beca && "Elegí el tipo de beca"}/>
                                </View>
                                <Text style={{fontSize: 12, color: "#0369a1"}}>
                                    Adjuntá el formulario de beca firmado en la lista de documentos de arriba.
                                </Text>
                            </View>
                        )}
                    </View>
                </>
            ) : null}
        </WizardShell>
    );
}