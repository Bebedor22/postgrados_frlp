/**
 * Portal Docente (Módulo B): estudiantes inscriptos a un seminario y carga de notas.
 *
 * La nota final se guarda en lote con PATCH /seminarios/{id}/notas. El backend
 * valida que esté entre 1 y 10 (BR-003: nota >= 4 aprueba, < 4 desaprueba).
 */
import {useLocalSearchParams, useRouter} from "expo-router";
import {type CSSProperties, useEffect, useState} from "react";
import {EncabezadoPagina, MarcoDocente} from "../../../src/components/portal/MarcoPortal";
import {
    ApiError, EstudianteSeminario, Seminario,
    obtenerSeminario, listarInscriptosSeminario, registrarNotasSeminario,
} from "../../../src/lib/api";
import {obtenerSesion} from "../../../src/lib/sesion";

const CELDA: CSSProperties = {padding: "10px 12px", borderBottom: "1px solid #f3f4f6", textAlign: "left"};
const COLOR_ESTADO: Record<string, string> = {
    CURSANDO: "#d97706", APROBADO: "#16a34a", DESAPROBADO: "#dc2626",
};

export default function SeminarioDocenteScreen() {
    const router = useRouter();
    const {id} = useLocalSearchParams<{id: string}>();
    const sesion = obtenerSesion();

    const [seminario, setSeminario] = useState<Seminario | null>(null);
    const [estudiantes, setEstudiantes] = useState<EstudianteSeminario[]>([]);
    const [notas, setNotas] = useState<Record<string, string>>({});
    const [cargando, setCargando] = useState(true);
    const [guardando, setGuardando] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [aviso, setAviso] = useState<string | null>(null);

    function falló(e: unknown) {
        const err = e as ApiError;
        if (err.status === 401) router.replace("/login");
        else setError(err.message);
    }

    async function cargar() {
        setCargando(true);
        setError(null);
        try {
            const [sem, filas] = await Promise.all([
                obtenerSeminario(id), listarInscriptosSeminario(id),
            ]);
            setSeminario(sem);
            setEstudiantes(filas);
            setNotas(Object.fromEntries(
                filas.map((f) => [f.legajo_id, f.nota_final === null ? "" : String(f.nota_final)])
            ));
        } catch (e) {
            falló(e);
        } finally {
            setCargando(false);
        }
    }

    useEffect(() => {
        if (!sesion || sesion.usuario.rol !== "DOCENTE") {
            router.replace("/login");
            return;
        }
        if (id) cargar();
    }, [id]);

    async function guardar() {
        const cargadas = estudiantes
            .map((f) => ({legajo_id: f.legajo_id, nota: Number(notas[f.legajo_id])}))
            .filter((n) => notas[n.legajo_id] !== "" && Number.isFinite(n.nota));
        if (cargadas.length === 0) {
            setError("Ingresá al menos una nota.");
            return;
        }
        setGuardando(true);
        setError(null);
        setAviso(null);
        try {
            await registrarNotasSeminario(id, cargadas);
            setAviso(`${cargadas.length} nota(s) guardada(s). El progreso y el semáforo ya están actualizados.`);
            await cargar();
        } catch (e) {
            falló(e);
        } finally {
            setGuardando(false);
        }
    }

    return (
        <MarcoDocente>
            <EncabezadoPagina
                titulo={seminario ? `${seminario.codigo} · ${seminario.nombre}` : "Seminario"}
                accion={null}
            />
            <div style={{padding: "24px", maxWidth: "1000px"}}>
                <button
                    onClick={() => router.push("/docente/misCursos")}
                    style={{background: "none", border: "none", color: "#1d6b59", cursor: "pointer", fontSize: "13px", padding: 0, marginBottom: "16px"}}
                >
                    ← Volver a mis cursos
                </button>

                {error ? (
                    <div style={{
                        backgroundColor: "#fef2f2", color: "#b91c1c", border: "1px solid #fecaca",
                        borderRadius: "6px", padding: "12px 16px", marginBottom: "16px", fontSize: "13px",
                    }}>
                        {error}
                    </div>
                ) : null}
                {aviso ? (
                    <div style={{
                        backgroundColor: "#ecfdf5", color: "#065f46", border: "1px solid #a7f3d0",
                        borderRadius: "6px", padding: "12px 16px", marginBottom: "16px", fontSize: "13px",
                    }}>
                        {aviso}
                    </div>
                ) : null}
                {cargando ? (
                    <p style={{color: "#6b7280", fontSize: "13px"}}>Cargando estudiantes…</p>
                ) : null}

                {!cargando && seminario ? (
                    <div style={{
                        backgroundColor: "white", border: "1px solid #e5e7eb", borderRadius: "8px",
                        overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                    }}>
                        <div style={{padding: "16px 20px", borderBottom: "1px solid #e5e7eb"}}>
                            <div style={{fontSize: "14px", fontWeight: 600, color: "#111"}}>
                                Estudiantes inscriptos ({estudiantes.length})
                            </div>
                            <div style={{fontSize: "12px", color: "#6b7280", marginTop: "4px"}}>
                                {seminario.horas_catedra} horas cátedra ·{" "}
                                {seminario.es_obligatorio ? "Seminario obligatorio" : "Seminario optativo"}
                                {seminario.fecha_limite_actas
                                    ? ` · Límite de actas: ${seminario.fecha_limite_actas}` : ""}
                            </div>
                        </div>

                        {estudiantes.length === 0 ? (
                            <div style={{padding: "24px", color: "#6b7280", fontSize: "13px"}}>
                                Todavía no hay estudiantes inscriptos en este seminario.
                            </div>
                        ) : (
                            <table style={{width: "100%", borderCollapse: "collapse", fontSize: "13px"}}>
                                <thead>
                                <tr style={{backgroundColor: "#f9fafb", color: "#374151"}}>
                                    <th style={CELDA}>Legajo</th>
                                    <th style={CELDA}>Apellido y nombre</th>
                                    <th style={CELDA}>Email</th>
                                    <th style={CELDA}>Estado</th>
                                    <th style={CELDA}>Nota final</th>
                                </tr>
                                </thead>
                                <tbody>
                                {estudiantes.map((f) => (
                                    <tr key={f.legajo_id}>
                                        <td style={CELDA}>{f.numero_legajo}</td>
                                        <td style={CELDA}>{f.apellido}, {f.nombre}</td>
                                        <td style={CELDA}>{f.email}</td>
                                        <td style={CELDA}>
                                            <span style={{
                                                color: COLOR_ESTADO[f.estado] ?? "#374151", fontWeight: 600,
                                            }}>
                                                {f.estado}
                                            </span>
                                        </td>
                                        <td style={CELDA}>
                                            <input
                                                type="number" min="1" max="10" step="0.1"
                                                value={notas[f.legajo_id] ?? ""}
                                                placeholder="—"
                                                onChange={(e) => setNotas({
                                                    ...notas, [f.legajo_id]: e.target.value,
                                                })}
                                                style={{
                                                    width: "80px", padding: "6px 8px", border: "1px solid #d1d5db",
                                                    borderRadius: "5px", fontSize: "13px",
                                                }}
                                            />
                                        </td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        )}

                        <div style={{padding: "16px 20px", borderTop: "1px solid #e5e7eb"}}>
                            <button
                                onClick={guardar}
                                disabled={guardando || estudiantes.length === 0}
                                style={{
                                    padding: "10px 20px", backgroundColor: "#0d2035", color: "white",
                                    border: "none", borderRadius: "6px", fontSize: "13px", fontWeight: 500,
                                    cursor: guardando ? "default" : "pointer", opacity: guardando ? 0.6 : 1,
                                }}
                            >
                                {guardando ? "Guardando…" : "💾 Guardar notas finales"}
                            </button>
                            <span style={{fontSize: "12px", color: "#6b7280", marginLeft: "12px"}}>
                                Nota ≥ 4 aprueba el seminario.
                            </span>
                        </div>
                    </div>
                ) : null}
            </div>
        </MarcoDocente>
    );
}
