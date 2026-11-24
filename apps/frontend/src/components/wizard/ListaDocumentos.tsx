/**
 * Lista de documentos del legajo (RF-CORE-002).
 *
 * La usan el paso 4 del wizard (para subir, reemplazar y quitar), la pantalla del
 * trámite y el detalle del legajo de la conducción (solo para ver).
 * Si se pasan `alSubir` y `alQuitar`, la lista es editable.
 */
import {useState} from "react";
import {ActivityIndicator, Pressable, Text, View} from "react-native";
import {ApiError, DocumentoSubido, RequisitoDocumental} from "../../lib/api";
import {elegirArchivoPdf, esWeb, formatearTamanio, TAMANIO_MAXIMO_MB, validarArchivoPdf} from "../../lib/documentos";
import {wizardStyles} from "./WizardShell";

type Props = {
    requisitos: RequisitoDocumental[];
    alVer: (documento: DocumentoSubido) => void;
    alSubir?: (tipo: string, archivo: File) => Promise<void>;
    alQuitar?: (documento: DocumentoSubido) => Promise<void>;
    /** Marca en rojo los obligatorios que faltan (al intentar enviar). */
    resaltarFaltantes?: boolean;
};

function BotonChico({texto, alPresionar, peligro, deshabilitado}: {
    texto: string;
    alPresionar: () => void;
    peligro?: boolean;
    deshabilitado?: boolean;
}) {
    return (
        <Pressable
            style={[wizardStyles.dropzoneAction, peligro && {borderColor: "#fca5a5"}, deshabilitado && {opacity: 0.5}]}
            onPress={alPresionar}
            disabled={deshabilitado}
        >
            <Text style={[wizardStyles.dropzoneActionText, peligro && {color: "#dc2626"}]}>{texto}</Text>
        </Pressable>
    );
}

export function ListaDocumentos({requisitos, alVer, alSubir, alQuitar, resaltarFaltantes}: Props) {
    const editable = Boolean(alSubir && alQuitar);
    const [ocupado, setOcupado] = useState<string | null>(null); // tipo que se está subiendo o quitando
    const [errores, setErrores] = useState<Record<string, string>>({});

    const ponerError = (tipo: string, mensaje: string | null) =>
        setErrores(({[tipo]: _, ...resto}) => (mensaje ? {...resto, [tipo]: mensaje} : resto));

    async function seleccionar(tipo: string) {
        const archivo = await elegirArchivoPdf();
        if (!archivo || !alSubir) return;
        const invalido = validarArchivoPdf(archivo);
        ponerError(tipo, invalido);
        if (invalido) return; // Se rechaza antes de transferir (SRS)
        setOcupado(tipo);
        try {
            await alSubir(tipo, archivo);
        } catch (e) {
            ponerError(tipo, (e as ApiError).message);
        } finally {
            setOcupado(null);
        }
    }

    async function quitar(requisito: RequisitoDocumental) {
        if (!requisito.documento || !alQuitar) return;
        ponerError(requisito.tipo, null);
        setOcupado(requisito.tipo);
        try {
            await alQuitar(requisito.documento);
        } catch (e) {
            ponerError(requisito.tipo, (e as ApiError).message);
        } finally {
            setOcupado(null);
        }
    }

    return (
        <View style={{gap: 10}}>
            {editable && !esWeb ? (
                <Text style={{fontSize: 13, color: "#b45309"}}>
                    La carga de archivos está disponible desde el navegador (versión web).
                </Text>
            ) : null}
            {requisitos.map((r) => {
                const falta = Boolean(resaltarFaltantes && r.obligatorio && !r.presentado);
                const error = errores[r.tipo];
                const enCurso = ocupado === r.tipo;
                return (
                    <View
                        key={r.tipo}
                        style={[
                            wizardStyles.dropzone,
                            {marginBottom: 0, gap: 12, flexWrap: "wrap"},
                            r.presentado && wizardStyles.dropzoneActive,
                            r.presentado && {borderStyle: "solid"},
                            (falta || error) && {borderColor: "#dc2626", backgroundColor: "#fef2f2"},
                        ]}
                    >
                        <View style={{flex: 1, minWidth: 200, gap: 2}}>
                            <Text style={wizardStyles.dropzoneText}>
                                {r.descripcion}
                                {r.obligatorio
                                    ? <Text style={{color: "#dc2626"}}> *</Text>
                                    : <Text style={{color: "#9ca3af", fontWeight: "400"}}> (opcional)</Text>}
                            </Text>
                            {r.documento ? (
                                <Text style={{fontSize: 12, color: "#047857"}}>
                                    ✓ {r.documento.nombre_original} · {formatearTamanio(r.documento.tamanio_bytes)}
                                </Text>
                            ) : (
                                <Text style={wizardStyles.dropzoneSubtext}>
                                    {editable ? `Solo PDF · máx. ${TAMANIO_MAXIMO_MB} MB` : "No presentado"}
                                </Text>
                            )}
                            {falta && !error ? (
                                <Text style={{fontSize: 12, color: "#dc2626"}}>Falta adjuntar este documento</Text>
                            ) : null}
                            {error ? <Text style={{fontSize: 12, color: "#dc2626"}}>{error}</Text> : null}
                        </View>

                        <View style={{flexDirection: "row", gap: 6, alignItems: "center"}}>
                            {enCurso ? <ActivityIndicator size="small" color="#0d2035"/> : null}
                            {r.documento ? <BotonChico texto="Ver" alPresionar={() => alVer(r.documento!)}/> : null}
                            {editable && esWeb ? (
                                <>
                                    <BotonChico
                                        texto={r.presentado ? "Reemplazar" : "Seleccionar PDF"}
                                        alPresionar={() => seleccionar(r.tipo)}
                                        deshabilitado={ocupado !== null}
                                    />
                                    {r.presentado ? (
                                        <BotonChico texto="Quitar" peligro alPresionar={() => quitar(r)} deshabilitado={ocupado !== null}/>
                                    ) : null}
                                </>
                            ) : null}
                        </View>
                    </View>
                );
            })}
        </View>
    );
}