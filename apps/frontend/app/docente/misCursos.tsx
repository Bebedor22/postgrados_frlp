/**
 * Portal Docente (Módulo B): seminarios asignados al docente.
 *
 * Los datos salen de la API: el backend filtra los seminarios por el email del
 * docente logueado. La planilla de asistencia completa queda fuera del alcance
 * mínimo del módulo; acá solo se gestiona la nota final de cada estudiante.
 */
import {useRouter} from "expo-router";
import {type CSSProperties, useEffect, useState} from "react";
import {EncabezadoPagina, MarcoDocente} from "../../src/components/portal/MarcoPortal";
import {
    ApiError, Carrera, EstudianteSeminario, Seminario,
    listarCarreras, listarInscriptosSeminario, listarSeminarios,
} from "../../src/lib/api";
import {obtenerSesion} from "../../src/lib/sesion";

const BOTON_PRINCIPAL: CSSProperties = {
    display: "flex", alignItems: "center", gap: "4px", padding: "9px 18px",
    backgroundColor: "#0d2035", color: "white", border: "none", borderRadius: "6px",
    fontSize: "13px", fontWeight: 500, cursor: "pointer",
};

export default function MisCursosScreen() {
    const router = useRouter();
    const sesion = obtenerSesion();
    const [seminarios, setSeminarios] = useState<Seminario[] | null>(null);
    const [carreras, setCarreras] = useState<Carrera[]>([]);
    const [inscriptos, setInscriptos] = useState<Record<string, EstudianteSeminario[]>>({});
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!sesion || sesion.usuario.rol !== "DOCENTE") {
            router.replace("/login");
            return;
        }
        function falló(e: unknown) {
            const err = e as ApiError;
            if (err.status === 401) router.replace("/login");
            else setError(err.message);
        }
        Promise.all([listarSeminarios(), listarCarreras()])
            .then(async ([lista, carreras]) => {
                setSeminarios(lista);
                setCarreras(carreras);
                const filas = await Promise.all(lista.map((s) => listarInscriptosSeminario(s.id)));
                setInscriptos(Object.fromEntries(lista.map((s, i) => [s.id, filas[i]])));
            })
            .catch(falló);
    }, []);

    const nombreCarrera = (id: string) => carreras.find((c) => c.id === id)?.nombre ?? "Carrera";

    return (
        <MarcoDocente>
            <EncabezadoPagina titulo="Mis cursos"/>
            <div style={{padding: "24px", maxWidth: "900px"}}>
                {error ? (
                    <div style={{
                        backgroundColor: "#fef2f2", color: "#b91c1c", border: "1px solid #fecaca",
                        borderRadius: "6px", padding: "12px 16px", marginBottom: "16px", fontSize: "13px",
                    }}>
                        {error}
                    </div>
                ) : null}
                {seminarios === null && !error ? (
                    <p style={{color: "#6b7280", fontSize: "13px"}}>Cargando seminarios…</p>
                ) : null}
                {seminarios?.length === 0 ? (
                    <div style={{
                        backgroundColor: "white", border: "1px solid #e5e7eb", borderRadius: "8px",
                        padding: "24px", fontSize: "14px", color: "#374151",
                    }}>
                        No tenés seminarios asignados. Conducción debe asignarte uno al crear el seminario.
                    </div>
                ) : null}

                {seminarios?.map((seminario) => {
                    const lista = inscriptos[seminario.id] ?? [];
                    const conNota = lista.filter((e) => e.nota_final !== null).length;
                    return (
                        <div
                            key={seminario.id}
                            style={{
                                backgroundColor: "white", border: "1px solid #e5e7eb", borderRadius: "8px",
                                padding: "16px 20px", display: "flex", alignItems: "center", gap: "16px",
                                marginBottom: "16px", boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                            }}
                        >
                            <div style={{
                                width: "44px", height: "44px", color: "#FFF", fontSize: "1.6em",
                                backgroundColor: "#0d2035", borderRadius: "10px", display: "flex",
                                alignItems: "center", justifyContent: "center", flexShrink: 0,
                            }}>
                                🕮
                            </div>
                            <div style={{flex: 1, minWidth: 0}}>
                                <div style={{fontSize: "15px", fontWeight: 600, color: "#111", marginBottom: "4px"}}>
                                    {seminario.nombre}
                                </div>
                                <div style={{display: "flex", gap: "16px", fontSize: "12px", color: "#6b7280", flexWrap: "wrap"}}>
                                    <span>📘 {seminario.codigo}</span>
                                    <span>🎓 {nombreCarrera(seminario.carrera_id)}</span>
                                    <span>⏱ {seminario.horas_catedra} horas cátedra</span>
                                    <span>👥 {lista.length} estudiantes</span>
                                    <span style={{color: conNota === lista.length && lista.length > 0 ? "#16a34a" : "#d97706"}}>
                                        ✎ {conNota}/{lista.length} notas cargadas
                                    </span>
                                    <span style={{
                                        color: seminario.es_obligatorio ? "#1d6b59" : "#6b7280",
                                        fontWeight: seminario.es_obligatorio ? 600 : 400,
                                    }}>
                                        {seminario.es_obligatorio ? "Obligatorio" : "Optativo"}
                                    </span>
                                </div>
                            </div>
                            <button
                                onClick={() => router.push(`/docente/seminario/${seminario.id}`)}
                                style={BOTON_PRINCIPAL}
                            >
                                Gestionar {">"}
                            </button>
                        </div>
                    );
                })}
            </div>
        </MarcoDocente>
    );
}
