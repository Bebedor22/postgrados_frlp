/**
 * Pantalla previa al wizard: el aspirante elige carrera y deja sus datos mínimos.
 * Con eso el backend crea el legajo en BORRADOR y devuelve el token del trámite.
 */
import {useRouter} from "expo-router";
import {useEffect, useState} from "react";
import {Text, View, useWindowDimensions} from "react-native";
import {
    BotonAccion, CampoTexto, Cargando, Etiqueta, MensajeError, NotaObligatorios, OpcionesRadio, TextoError,
} from "../../src/components/wizard/Campos";
import {WizardShell, wizardStyles} from "../../src/components/wizard/WizardShell";
import {ApiError, Carrera, Cohorte, iniciarInscripcion, listarCarreras, listarCohortesAbiertas} from "../../src/lib/api";
import {guardarTokenTramite} from "../../src/lib/sesion";
import {Errores, hayErrores, validar} from "../../src/lib/validaciones";

const TIPOS: Record<Carrera["tipo"], string> = {
    Especializacion: "Especialización",
    Maestria: "Maestría",
    Doctorado: "Doctorado",
};

export default function InicioInscripcionScreen() {
    const router = useRouter();
    const {width} = useWindowDimensions();
    const halfOrFull = width < 860 ? wizardStyles.fullField : wizardStyles.halfField;

    const [carreras, setCarreras] = useState<Carrera[] | null>(null);
    const [cohortes, setCohortes] = useState<Cohorte[]>([]);
    const [datos, setDatos] = useState({
        carrera_id: "",
        cohorte_id: "",
        tipo_documento: "DNI" as "DNI" | "PASAPORTE",
        numero_documento: "",
        nombre: "",
        apellido: "",
        email: "",
    });
    const [errores, setErrores] = useState<Errores>({});
    const [error, setError] = useState<string | null>(null);
    const [enviando, setEnviando] = useState(false);

    const cambiar = (campo: keyof typeof datos, valor: string) => {
        setDatos((d) => ({...d, [campo]: valor}));
        setErrores(({[campo]: _, ...resto}) => resto);
    };
    const campo = (nombre: keyof typeof datos) => ({
        value: datos[nombre],
        onChangeText: (texto: string) => cambiar(nombre, texto),
        error: errores[nombre],
    });

    useEffect(() => {
        Promise.all([listarCarreras(), listarCohortesAbiertas()])
            .then(([c, co]) => {
                setCarreras(c);
                setCohortes(co);
                // Si hay una sola opción, se elige sola
                setDatos((d) => ({
                    ...d,
                    carrera_id: c.length === 1 ? c[0].id : d.carrera_id,
                    cohorte_id: co.length === 1 ? co[0].id : d.cohorte_id,
                }));
            })
            .catch((e: ApiError) => setError(e.message));
    }, []);

    async function comenzar() {
        const encontrados = validar(datos, {
            carrera_id: ["requerido"],
            cohorte_id: ["requerido"],
            numero_documento: ["requerido", datos.tipo_documento === "DNI" ? "dni" : "pasaporte"],
            email: ["requerido", "email"],
            nombre: ["requerido"],
            apellido: ["requerido"],
        });
        setErrores(encontrados);
        if (hayErrores(encontrados)) {
            setError("Revisá los campos marcados en rojo para poder continuar.");
            return;
        }
        setEnviando(true);
        setError(null);
        try {
            const respuesta = await iniciarInscripcion({...datos, numero_documento: datos.numero_documento.trim()});
            guardarTokenTramite(respuesta.token);
            router.push("/wizard/step-1");
        } catch (e) {
            setError((e as ApiError).message);
        } finally {
            setEnviando(false);
        }
    }

    const hayOferta = carreras !== null && carreras.length > 0 && cohortes.length > 0;

    return (
        <WizardShell
            currentStep={0}
            title="Comenzar inscripción"
            subtitle="Elegí la carrera y dejá tus datos básicos. Después vas a poder completar el formulario en 4 pasos, guardar y retomarlo cuando quieras."
            aviso={hayOferta ? <MensajeError mensaje={error}/> : null}
            footer={hayOferta ? <BotonAccion texto="Comenzar ›" alPresionar={comenzar} ocupado={enviando}/> : <View/>}
        >
            {!hayOferta ? <MensajeError mensaje={error}/> : null}
            {carreras === null && !error ? <Cargando texto="Buscando carreras disponibles..."/> : null}

            {carreras !== null && (carreras.length === 0 || cohortes.length === 0) ? (
                <View style={[wizardStyles.section, {backgroundColor: "#fffbeb", borderWidth: 1, borderColor: "#f59e0b"}]}>
                    <Text style={[wizardStyles.sectionTitle, {color: "#b45309"}]}>Inscripción no disponible</Text>
                    <Text style={{fontSize: 14, color: "#78350f"}}>
                        {cohortes.length === 0
                            ? "En este momento no hay cohortes con la inscripción abierta."
                            : "Todavía no hay carreras cargadas."}{" "}
                        Volvé a intentarlo más adelante.
                    </Text>
                </View>
            ) : null}

            {hayOferta ? (
                <>
                    <View style={wizardStyles.section}>
                        <Text style={wizardStyles.sectionTitle}>
                            Carrera a inscribirse<Text style={{color: "#dc2626"}}> *</Text>
                        </Text>
                        <OpcionesRadio
                            enFila={false}
                            opciones={carreras.map((c) => ({
                                valor: c.id,
                                texto: c.nombre,
                                detalle: `${TIPOS[c.tipo]} · ${c.duracion_anios} ${c.duracion_anios === 1 ? "año" : "años"}`,
                            }))}
                            valor={datos.carrera_id}
                            alCambiar={(v) => cambiar("carrera_id", v)}
                        />
                        <TextoError mensaje={errores.carrera_id && "Elegí una carrera"}/>
                        {cohortes.length > 1 ? (
                            <>
                                <Etiqueta texto="Cohorte" requerido/>
                                <OpcionesRadio
                                    opciones={cohortes.map((c) => ({valor: c.id, texto: c.nombre}))}
                                    valor={datos.cohorte_id}
                                    alCambiar={(v) => cambiar("cohorte_id", v)}
                                />
                                <TextoError mensaje={errores.cohorte_id && "Elegí una cohorte"}/>
                            </>
                        ) : (
                            <Text style={{fontSize: 13, color: "#6b7280", marginTop: 8}}>Cohorte: {cohortes[0].nombre}</Text>
                        )}
                    </View>

                    <View style={wizardStyles.section}>
                        <Text style={wizardStyles.sectionTitle}>Tus datos</Text>
                        <Etiqueta texto="Tipo de documento" requerido/>
                        <OpcionesRadio
                            opciones={[
                                {valor: "DNI" as const, texto: "DNI"},
                                {valor: "PASAPORTE" as const, texto: "Pasaporte"},
                            ]}
                            valor={datos.tipo_documento}
                            alCambiar={(v) => {
                                cambiar("tipo_documento", v);
                                cambiar("numero_documento", "");
                            }}
                        />
                        <View style={wizardStyles.twoColumns}>
                            <CampoTexto
                                contenedor={halfOrFull}
                                etiqueta={datos.tipo_documento === "DNI" ? "DNI (sin puntos)" : "Pasaporte"}
                                requerido
                                placeholder={datos.tipo_documento === "DNI" ? "Ej.: 12345678" : "Ej.: AAB123456"}
                                keyboardType={datos.tipo_documento === "DNI" ? "numeric" : "default"}
                                maxLength={datos.tipo_documento === "DNI" ? 8 : 12}
                                {...campo("numero_documento")}
                                onChangeText={(t) =>
                                    cambiar("numero_documento", datos.tipo_documento === "DNI" ? t.replace(/\D/g, "") : t.toUpperCase())
                                }
                            />
                            <CampoTexto
                                contenedor={halfOrFull}
                                etiqueta="Correo electrónico"
                                requerido
                                placeholder="Ej.: nombre@email.com"
                                keyboardType="email-address"
                                autoCapitalize="none"
                                {...campo("email")}
                            />
                            <CampoTexto contenedor={halfOrFull} etiqueta="Nombre(s)" requerido placeholder="Ej.: Juan" {...campo("nombre")}/>
                            <CampoTexto contenedor={halfOrFull} etiqueta="Apellido(s)" requerido placeholder="Ej.: Pérez" {...campo("apellido")}/>
                        </View>
                    </View>
                    <NotaObligatorios/>
                </>
            ) : null}
        </WizardShell>
    );
}