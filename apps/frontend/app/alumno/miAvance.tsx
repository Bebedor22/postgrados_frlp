/**
 * Portal del Alumno (Módulo B): "Mi Avance" con datos reales.
 *
 * El alumno se identifica con el token de su link de inscripción (guardado al
 * abrir el trámite). La API junta el progreso de seminarios, el semáforo de
 * riesgo y el trabajo final; no requiere iniciar sesión.
 */
import {useEffect, useState} from "react";
import {Link} from "expo-router";
import {type CSSProperties} from "react";
import {MarcoAlumno} from "../../src/components/portal/MarcoPortal";
import {ApiError, AvanceAlumno, avanceAlumno} from "../../src/lib/api";
import {obtenerTokenTramite} from "../../src/lib/sesion";

const TABS = ["Resumen", "Seminarios", "TFI / Tesis", "Alertas"] as const;
type Tab = typeof TABS[number];

const COLOR_SEMAFORO: Record<string, string> = {
    VERDE: "#16a34a", AMARILLO: "#f59e0b", ROJO: "#dc2626",
};
const COLOR_ESTADO: Record<string, string> = {
    CURSANDO: "#d97706", APROBADO: "#16a34a", DESAPROBADO: "#dc2626",
};
const CELDA: CSSProperties = {padding: "11px 12px", borderBottom: "1px solid #f3f4f6", textAlign: "left"};

function Alerta({texto, amarillo}: { texto: string; amarillo?: boolean }) {
    return (
        <div style={{
            display: "flex", alignItems: "center", gap: "10px", padding: "12px 16px",
            backgroundColor: amarillo ? "#fefce8" : "#eff6ff",
            border: `1px solid ${amarillo ? "#fde68a" : "#bfdbfe"}`,
            borderRadius: "6px", fontSize: "13px", color: amarillo ? "#92400e" : "#1e40af",
        }}>
            {amarillo ? "⚠️" : "ℹ️"} {texto}
        </div>
    );
}

export default function MiAvance() {
    const token = obtenerTokenTramite();
    const [activeTab, setActiveTab] = useState<Tab>("Resumen");
    const [avance, setAvance] = useState<AvanceAlumno | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!token) return;
        avanceAlumno(token)
            .then(setAvance)
            .catch((e: unknown) => setError((e as ApiError).message));
    }, [token]);

    if (!token) {
        return (
            <MarcoAlumno>
                <div style={{padding: "24px", maxWidth: "1000px"}}>
                    <div style={{
                        backgroundColor: "white", border: "1px solid #e5e7eb", borderRadius: "8px",
                        padding: "32px", textAlign: "center", fontSize: "14px", color: "#374151",
                    }}>
                        Para ver tu avance abrí el link de inscripción que te enviamos por email.
                        <div style={{marginTop: "12px", fontSize: "13px"}}>
                            <Link href="/login" style={{color: "#1d6b59"}}>Ir al inicio</Link>
                        </div>
                    </div>
                </div>
            </MarcoAlumno>
        );
    }

    const total = avance?.progreso.obligatorios_total ?? 0;
    const aprobados = avance?.progreso.aprobados ?? 0;
    const porcentaje = total > 0 ? Math.round((aprobados / total) * 100) : 0;
    const seminarios = avance?.seminarios ?? [];
    const alertas: string[] = [];
    if (avance && avance.semaforo !== "VERDE") {
        alertas.push(`Semáforo ${avance.semaforo}: regularizá tu situación académica para graduarte.`);
    }
    if (avance && avance.progreso.adeudados > 0) {
        alertas.push(`Adeudás ${avance.progreso.adeudados} seminario(s) obligatorio(s).`);
    }
    if (avance && avance.estado === "ACTIVO" && avance.trabajo_final === null) {
        alertas.push("Todavía no registraste tu trabajo final (TFI o tesis).");
    }

    return (
        <MarcoAlumno>
            <div style={{padding: "24px", maxWidth: "1000px"}}>
                {error ? (
                    <div style={{
                        backgroundColor: "#fef2f2", color: "#b91c1c", border: "1px solid #fecaca",
                        borderRadius: "6px", padding: "12px 16px", marginBottom: "16px", fontSize: "13px",
                    }}>
                        {error}
                    </div>
                ) : null}
                {!avance && !error ? (
                    <p style={{color: "#6b7280", fontSize: "13px"}}>Cargando tu avance…</p>
                ) : null}

                {avance ? (
                    <>
                        <div style={{
                            backgroundColor: "white", borderRadius: "8px", padding: "20px 24px",
                            marginBottom: "16px", display: "flex", alignItems: "flex-start",
                            gap: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.06)", flexWrap: "wrap",
                        }}>
                            <div style={{
                                width: "56px", height: "56px", borderRadius: "50%", backgroundColor: "#e5e7eb",
                                display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                            }}>
                                👤
                            </div>
                            <div style={{flex: 1, minWidth: "180px"}}>
                                <div style={{fontSize: "18px", fontWeight: 600, color: "#111", marginBottom: "4px"}}>
                                    Legajo {avance.numero_legajo}
                                </div>
                                <div style={{fontSize: "13px", color: "#6b7280", lineHeight: "1.7"}}>
                                    Estado del legajo: <strong>{avance.estado}</strong><br/>
                                    Seminarios obligatorios: {aprobados} de {total} aprobados
                                </div>
                            </div>
                            <div style={{textAlign: "center"}}>
                                <div style={{
                                    width: "80px", height: "80px", borderRadius: "50%",
                                    backgroundColor: COLOR_SEMAFORO[avance.semaforo],
                                    display: "flex", flexDirection: "column", alignItems: "center",
                                    justifyContent: "center", margin: "0 auto 6px",
                                }}>
                                    <span style={{color: "white", fontSize: "10px", fontWeight: 500}}>Semáforo</span>
                                    <span style={{color: "white", fontSize: "13px", fontWeight: 700}}>
                                        {avance.semaforo}
                                    </span>
                                </div>
                                <div style={{fontSize: "12px", color: "#6b7280"}}>Riesgo académico</div>
                            </div>
                            <div style={{textAlign: "right", minWidth: "120px"}}>
                                <div style={{fontSize: "12px", color: "#6b7280", marginBottom: "4px"}}>
                                    % Avance de seminarios
                                </div>
                                <div style={{fontSize: "28px", fontWeight: 700, color: "#111", marginBottom: "6px"}}>
                                    {porcentaje}%
                                </div>
                                <div style={{
                                    width: "120px", height: "6px", backgroundColor: "#e5e7eb",
                                    borderRadius: "4px", overflow: "hidden",
                                }}>
                                    <div style={{
                                        width: `${porcentaje}%`, height: "100%", backgroundColor: "#22c55e",
                                        borderRadius: "4px",
                                    }}/>
                                </div>
                            </div>
                        </div>

                        <div style={{
                            backgroundColor: "white", borderRadius: "8px",
                            boxShadow: "0 1px 3px rgba(0,0,0,0.06)", overflow: "hidden",
                        }}>
                            <div style={{display: "flex", borderBottom: "1px solid #e5e7eb", padding: "0 16px", flexWrap: "wrap"}}>
                                {TABS.map((tab) => (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab)}
                                        style={{
                                            padding: "12px 16px", border: "none", background: "none",
                                            cursor: "pointer", fontSize: "13px",
                                            fontWeight: activeTab === tab ? 600 : 400,
                                            color: activeTab === tab ? "#0d2035" : "#6b7280",
                                            borderBottom: activeTab === tab ? "2px solid #0d2035" : "2px solid transparent",
                                            marginBottom: "-1px",
                                        }}
                                    >
                                        {tab}
                                    </button>
                                ))}
                            </div>

                            <div style={{padding: "24px"}}>
                                {(activeTab === "Resumen" || activeTab === "Seminarios") && (
                                    <>
                                        <h3 style={{fontSize: "15px", fontWeight: 600, margin: "0 0 16px", color: "#111"}}>
                                            Progreso académico
                                        </h3>
                                        {seminarios.length === 0 ? (
                                            <p style={{fontSize: "13px", color: "#6b7280"}}>
                                                Todavía no estás inscripto a ningún seminario.
                                            </p>
                                        ) : (
                                            <table style={{width: "100%", borderCollapse: "collapse", fontSize: "13px"}}>
                                                <thead>
                                                <tr style={{backgroundColor: "#f9fafb", color: "#374151"}}>
                                                    <th style={CELDA}>Código</th>
                                                    <th style={CELDA}>Seminario</th>
                                                    <th style={CELDA}>Horas</th>
                                                    <th style={CELDA}>Tipo</th>
                                                    <th style={CELDA}>Nota</th>
                                                    <th style={CELDA}>Estado</th>
                                                </tr>
                                                </thead>
                                                <tbody>
                                                {seminarios.map((s) => (
                                                    <tr key={s.seminario_id}>
                                                        <td style={CELDA}>{s.codigo}</td>
                                                        <td style={CELDA}>{s.nombre}</td>
                                                        <td style={CELDA}>{s.horas_catedra}</td>
                                                        <td style={CELDA}>
                                                            {s.es_obligatorio ? "Obligatorio" : "Optativo"}
                                                        </td>
                                                        <td style={CELDA}>
                                                            {s.nota_final === null ? "—" : s.nota_final}
                                                        </td>
                                                        <td style={{
                                                            ...CELDA, color: COLOR_ESTADO[s.estado] ?? "#374151",
                                                            fontWeight: 600,
                                                        }}>
                                                            {s.estado}
                                                        </td>
                                                    </tr>
                                                ))}
                                                </tbody>
                                            </table>
                                        )}
                                    </>
                                )}

                                {activeTab === "TFI / Tesis" && (
                                    <div>
                                        <h3 style={{fontSize: "15px", fontWeight: 600, margin: "0 0 16px", color: "#111"}}>
                                            Trabajo Final Integrador / Tesis
                                        </h3>
                                        {avance.trabajo_final ? (
                                            <div style={{fontSize: "13px", color: "#374151", lineHeight: "1.9"}}>
                                                <div><strong>Tipo:</strong> {avance.trabajo_final.tipo}</div>
                                                <div><strong>Título:</strong> {avance.trabajo_final.titulo}</div>
                                                <div>
                                                    <strong>Director:</strong> {avance.trabajo_final.director_nombre}
                                                </div>
                                                <div>
                                                    <strong>Aprobación CPR:</strong>{" "}
                                                    {avance.trabajo_final.fecha_aprobacion_cpr ?? "Pendiente"}
                                                </div>
                                            </div>
                                        ) : (
                                            <p style={{fontSize: "13px", color: "#6b7280"}}>
                                                No hay un trabajo final registrado. Cuando lo apruebes en el
                                                CPR, el sistema habilita la graduación.
                                            </p>
                                        )}
                                    </div>
                                )}

                                {(activeTab === "Alertas" || activeTab === "Resumen") && (
                                    <div style={{marginTop: activeTab === "Resumen" ? "24px" : 0}}>
                                        <h3 style={{fontSize: "15px", fontWeight: 600, marginBottom: "12px", color: "#111"}}>
                                            Alertas
                                        </h3>
                                        <div style={{display: "flex", flexDirection: "column", gap: "8px"}}>
                                            {alertas.length === 0 ? (
                                                <p style={{fontSize: "13px", color: "#6b7280"}}>
                                                    No tenés alertas por ahora.
                                                </p>
                                            ) : alertas.map((texto) => (
                                                <Alerta key={texto} texto={texto} amarillo={avance.semaforo !== "VERDE"}/>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </>
                ) : null}
            </div>
        </MarcoAlumno>
    );
}
