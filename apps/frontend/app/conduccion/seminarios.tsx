/**
 * Conducción (Módulo B): catálogo de seminarios por carrera y alta de nuevos
 * seminarios. Los obligatorios son los que alimentan el progreso y el semáforo.
 */
import {useEffect, useState} from "react";
import {Pressable, Text, TextInput, View} from "react-native";
import {
    Boton, PortalConduccion, Tarjeta, useUsuarioConduccion,
} from "../../src/components/conduccion/PortalConduccion";
import {
    ApiError, Carrera, FiltrosSeminarios, Seminario,
    crearSeminario, listarCarreras, listarInscriptosSeminario, listarSeminarios,
} from "../../src/lib/api";

type Formulario = {
    nombre: string;
    codigo: string;
    horas_catedra: string;
    docente_email: string;
};

const VACIO: Formulario = {nombre: "", codigo: "", horas_catedra: "32", docente_email: ""};

export default function SeminariosConduccionScreen() {
    const usuario = useUsuarioConduccion();
    const [seminarios, setSeminarios] = useState<Seminario[] | null>(null);
    const [carreras, setCarreras] = useState<Carrera[]>([]);
    const [inscriptos, setInscriptos] = useState<Record<string, number>>({});
    const [filtro, setFiltro] = useState<FiltrosSeminarios>({});
    const [formulario, setFormulario] = useState<Formulario>(VACIO);
    const [carreraId, setCarreraId] = useState<string | null>(null);
    const [obligatorio, setObligatorio] = useState(true);
    const [mostrarFormulario, setMostrarFormulario] = useState(false);
    const [guardando, setGuardando] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [aviso, setAviso] = useState<string | null>(null);

    async function cargar() {
        try {
            const [lista, opciones] = await Promise.all([
                listarSeminarios(filtro), listarCarreras(),
            ]);
            setSeminarios(lista);
            setCarreras(opciones);
            setCarreraId((actual) => actual ?? opciones[0]?.id ?? null);
            const cantidades = await Promise.all(lista.map((s) => listarInscriptosSeminario(s.id)));
            setInscriptos(Object.fromEntries(lista.map((s, i) => [s.id, cantidades[i].length])));
        } catch (e) {
            setError((e as ApiError).message);
        }
    }

    useEffect(() => {
        if (usuario) cargar();
    }, [usuario, filtro.carrera_id, filtro.solo_obligatorios]);

    async function guardar() {
        if (!carreraId) {
            setError("Elegí una carrera.");
            return;
        }
        setGuardando(true);
        setError(null);
        setAviso(null);
        try {
            await crearSeminario({
                carrera_id: carreraId,
                nombre: formulario.nombre.trim(),
                codigo: formulario.codigo.trim(),
                horas_catedra: Number(formulario.horas_catedra),
                es_obligatorio: obligatorio,
                docente_email: formulario.docente_email.trim() || null,
            });
            setAviso("Seminario creado.");
            setFormulario(VACIO);
            setMostrarFormulario(false);
            await cargar();
        } catch (e) {
            setError((e as ApiError).message);
        } finally {
            setGuardando(false);
        }
    }

    const nombreCarrera = (id: string) => carreras.find((c) => c.id === id)?.nombre ?? "Carrera";

    return (
        <PortalConduccion
            usuario={usuario}
            titulo="Seminarios por carrera"
            accion={
                <Boton
                    texto={mostrarFormulario ? "Cancelar" : "+ Nuevo seminario"}
                    tipo={mostrarFormulario ? "secundario" : "exito"}
                    alPresionar={() => setMostrarFormulario(!mostrarFormulario)}
                />
            }
        >
            {error ? <Text style={{color: "#b91c1c", fontSize: 13}}>{error}</Text> : null}
            {aviso ? <Text style={{color: "#065f46", fontSize: 13}}>{aviso}</Text> : null}

            {mostrarFormulario ? (
                <Tarjeta titulo="Nuevo seminario">
                    <Text style={{fontSize: 12, color: "#6b7280", marginBottom: 8}}>Carrera</Text>
                    <View style={{flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 14}}>
                        {carreras.map((c) => (
                            <Pressable
                                key={c.id}
                                onPress={() => setCarreraId(c.id)}
                                style={{
                                    borderWidth: 1, borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6,
                                    borderColor: carreraId === c.id ? "#0d2035" : "#d1d5db",
                                    backgroundColor: carreraId === c.id ? "#0d2035" : "#ffffff",
                                }}
                            >
                                <Text style={{fontSize: 12, color: carreraId === c.id ? "#ffffff" : "#374151"}}>
                                    {c.nombre}
                                </Text>
                            </Pressable>
                        ))}
                    </View>
                    <Text style={{fontSize: 12, color: "#6b7280", marginBottom: 4}}>Nombre</Text>
                    <TextInput
                        value={formulario.nombre}
                        onChangeText={(nombre) => setFormulario({...formulario, nombre})}
                        placeholder="Ej. Metodología de la Investigación"
                        style={campo}
                    />
                    <Text style={{fontSize: 12, color: "#6b7280", marginBottom: 4}}>Código</Text>
                    <TextInput
                        value={formulario.codigo}
                        onChangeText={(codigo) => setFormulario({...formulario, codigo})}
                        placeholder="Ej. MET-001"
                        style={campo}
                    />
                    <Text style={{fontSize: 12, color: "#6b7280", marginBottom: 4}}>Horas cátedra</Text>
                    <TextInput
                        value={formulario.horas_catedra}
                        onChangeText={(horas_catedra) => setFormulario({...formulario, horas_catedra})}
                        keyboardType="numeric"
                        style={campo}
                    />
                    <Text style={{fontSize: 12, color: "#6b7280", marginBottom: 4}}>
                        Email del docente (opcional)
                    </Text>
                    <TextInput
                        value={formulario.docente_email}
                        onChangeText={(docente_email) => setFormulario({...formulario, docente_email})}
                        placeholder="docente@fenix.test"
                        autoCapitalize="none"
                        style={campo}
                    />
                    <Pressable
                        onPress={() => setObligatorio(!obligatorio)}
                        style={{flexDirection: "row", alignItems: "center", gap: 8, marginVertical: 14}}
                    >
                        <Text style={{fontSize: 16}}>{obligatorio ? "☑" : "☐"}</Text>
                        <Text style={{fontSize: 13, color: "#374151"}}>Seminario obligatorio</Text>
                    </Pressable>
                    <Boton texto={guardando ? "Guardando…" : "Guardar"} alPresionar={guardar} deshabilitado={guardando}/>
                </Tarjeta>
            ) : null}

            <View style={{flexDirection: "row", gap: 8, flexWrap: "wrap"}}>
                <Pressable
                    onPress={() => setFiltro({})}
                    style={[chip, filtro.carrera_id ? undefined : chipActivo]}
                >
                    <Text style={[chipTexto, filtro.carrera_id ? undefined : chipTextoActivo]}>Todas</Text>
                </Pressable>
                <Pressable
                    onPress={() => setFiltro({solo_obligatorios: true})}
                    style={[chip, filtro.solo_obligatorios ? chipActivo : undefined]}
                >
                    <Text style={[chipTexto, filtro.solo_obligatorios ? chipTextoActivo : undefined]}>
                        Solo obligatorios
                    </Text>
                </Pressable>
            </View>

            {seminarios === null ? <Text style={{color: "#6b7280", fontSize: 13}}>Cargando…</Text> : null}
            {seminarios?.length === 0 ? (
                <Tarjeta><Text style={{fontSize: 13, color: "#6b7280"}}>No hay seminarios para este filtro.</Text></Tarjeta>
            ) : null}
            {seminarios?.map((s) => (
                <Tarjeta key={s.id}>
                    <View style={{flexDirection: "row", alignItems: "flex-start", gap: 12}}>
                        <View style={{flex: 1}}>
                            <Text style={{fontSize: 15, fontWeight: "600", color: "#111"}}>
                                {s.codigo} · {s.nombre}
                            </Text>
                            <Text style={{fontSize: 12, color: "#6b7280", marginTop: 4}}>
                                {nombreCarrera(s.carrera_id)} · {s.horas_catedra} horas ·{" "}
                                {s.es_obligatorio ? "Obligatorio" : "Optativo"} ·{" "}
                                {inscriptos[s.id] ?? 0} inscriptos
                            </Text>
                            <Text style={{fontSize: 12, color: "#6b7280", marginTop: 2}}>
                                Docente: {s.docente_email ?? "sin asignar"}
                            </Text>
                        </View>
                    </View>
                </Tarjeta>
            ))}
        </PortalConduccion>
    );
}

const campo = {
    borderWidth: 1, borderColor: "#d1d5db", borderRadius: 6, backgroundColor: "#ffffff",
    paddingHorizontal: 12, paddingVertical: 9, fontSize: 13, marginBottom: 12, color: "#111",
};

const chip = {
    borderWidth: 1, borderColor: "#d1d5db", backgroundColor: "#ffffff",
    borderRadius: 999, paddingHorizontal: 12, paddingVertical: 6,
};
const chipActivo = {borderColor: "#0d2035", backgroundColor: "#0d2035"};
const chipTexto = {fontSize: 12, color: "#374151"};
const chipTextoActivo = {color: "#ffffff"};
