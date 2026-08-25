import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { AppLayout } from "../../src/components/layout/AppLayout";


const lineData = [
  { year: "2019", inscriptos: 125 },
  { year: "2020", inscriptos: 138 },
  { year: "2021", inscriptos: 150 },
  { year: "2022", inscriptos: 158 },
  { year: "2023", inscriptos: 170 },
  { year: "2024", inscriptos: 186 },
];

const barData = [
  { cohorte: "2018", graduados: 32 },
  { cohorte: "2019", graduados: 35 },
  { cohorte: "2020", graduados: 37 },
  { cohorte: "2021", graduados: 45 },
  { cohorte: "2022", graduados: 44 },
  { cohorte: "2023", graduados: 46 },
];

const pieData = [
  { name: "En Proceso", value: 45, color: "#f59e0b" },
  { name: "Aprobados", value: 35, color: "#22c55e" },
  { name: "No Iniciados", value: 20, color: "#ef4444" },
];

const resumenCarreras = [
  { carrera: "Maestría en Ingeniería Generncial", inscriptos: 98, cursando: 76, graduados: 68, desgranamiento: "22%", tesis: 28 },
  { carrera: "Doctorado en Materiales", inscriptos: 56, cursando: 42, graduados: 24, desgranamiento: "25%", tesis: 19 },
  { carrera: "Especialización Ingeniería Ambiental", inscriptos: 32, cursando: 24, graduados: 12, desgranamiento: "38%", tesis: 9 },
];

function KpiCard({ label, value, sub, icon, dark }: {
  label: string; value: string | number; sub: string; icon: React.ReactNode; dark?: boolean;
}) {
  return (
    <div style={{
      flex: 1, padding: "16px 20px",
      backgroundColor: dark ? "#0d2035" : "white",
      borderRadius: "8px",
      border: dark ? "none" : "1px solid #e5e7eb",
      display: "flex", flexDirection: "column", gap: "4px", minWidth: "0",
      boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: "12px", color: dark ? "rgba(255,255,255,0.6)" : "#6b7280" }}>{label}</span>
        <span style={{ color: dark ? "rgba(255,255,255,0.4)" : "#d1d5db" }}>{icon}</span>
      </div>
      <div style={{ fontSize: "26px", fontWeight: 700, color: dark ? "white" : "#111" }}>{value}</div>
      <div style={{ fontSize: "11px", color: dark ? "rgba(255,255,255,0.5)" : "#9ca3af" }}>{sub}</div>
    </div>
  );
}

const exportBtn = (
  <button style={{
    display: "flex", alignItems: "center", gap: "6px",
    padding: "7px 14px",
    backgroundColor: "rgba(255,255,255,0.15)", color: "white",
    border: "1px solid rgba(255,255,255,0.3)", borderRadius: "5px",
    fontSize: "12px", cursor: "pointer",
  }}>
    Exportar
  </button>
);

const navItems = [
  { icon: "📊", label: "Dashboard", to: "/cpr/dashboard", group: "Portal Conducción" },
  { icon: "📋", label: "Gestión de Inscripciones", to: "/cpr/gestionDeInscripciones", group: "Portal Conducción" },
  { icon: "🔍", label: "Buscador de Estudiantes", to: "/cpr/buscadorEstudiantes", group: "Portal Conducción" },
  { icon: "📑", label: "Reportes y Exportación", to: "/cpr/dashboard", group: "Portal Conducción" },
  { icon: "📄", label: "Gestión de Tesis", to: "/cpr/gestionDeTesis", group: "Portal Conducción" },
  { icon: "⏳", label: "Alertas y Vencimientos", to: "/cpr/dashboard", group: "Portal Conducción" },
  { icon: "⚙️", label: "Configuración", to: "/cpr/dashboard", group: "Portal Conducción" },
];

export default function Dashboard() {
  return (
    <AppLayout portalTitle="Portal Alumno" navItems={navItems}>
    <ScrollView contentContainerStyle={styles.page}>
      <div style={{ padding: "20px 24px" }}>
        {/* Filters */}
        <div style={{ display: "flex", gap: "12px", marginBottom: "20px" }}>
          {[
            { label: "Carrera", options: ["Todas", "Maestría en Ingeniería Generncial", "Doctorado en Materiales", "Especialización Ingeniería Ambiental"] },
            { label: "Cohorte", options: ["Todas", "2023", "2024", "2025", "2026"] },
            { label: "Período", options: ["Último año", "Últimos 3 años", "Histórico"] },
          ].map((f) => (
            <div key={f.label}>
              <div style={{ fontSize: "11px", color: "#6b7280", marginBottom: "4px" }}>{f.label}</div>
              <select style={{ padding: "6px 12px", border: "1px solid #d1d5db", borderRadius: "6px", fontSize: "13px", backgroundColor: "white", cursor: "pointer" }}>
                {f.options.map((o) => <option key={o}>{o}</option>)}
              </select>
            </div>
          ))}
        </div>

        {/* KPIs */}
        <div style={{ display: "flex", gap: "12px", marginBottom: "20px" }}>
          <KpiCard label="Total Inscriptos" value={186} sub="+12% vs año anterior" />
          <KpiCard label="Cursando" value={142} sub="76% del total" />
          <KpiCard label="Graduados" value={104} sub="+8% vs 2024" />
          <KpiCard label="Desgranamiento" value="28%" sub="-3% vs cohorte anterior" />
          <KpiCard label="Tesis en Desarrollo" value={56} sub="39% de cursantes" dark />
        </div>

        {/* Charts row */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
          <div style={{ backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, marginBottom: "16px", color: "#111" }}>Evolución de Inscripciones</h3>
            <>
			
			{/*Grafico de línea*/}
			
            </>
          </div>

          <div style={{ backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, marginBottom: "16px", color: "#111" }}>Situación de Trabajos Finales</h3>
            <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
              <>
                
				{/*Gráfico de torta*/}
				
              </>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {pieData.map((d) => (
                  <div key={d.name} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: d.color, flexShrink: 0 }} />
                    <span style={{ fontSize: "12px", color: "#374151" }}>{d.name} {d.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bar chart */}
        <div style={{ backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", padding: "20px", marginBottom: "16px", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <h3 style={{ fontSize: "14px", fontWeight: 600, marginBottom: "16px", color: "#111" }}>Graduaciones por Cohorte</h3>
          <div width="100%" height={180}>
            
			{/*Grafico de barras*/}
			
          </div>
        </div>

        {/* Summary table */}
        <div style={{ backgroundColor: "white", borderRadius: "8px", border: "1px solid #e5e7eb", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid #f3f4f6" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "#111" }}>Resumen por Carrera</h3>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ backgroundColor: "#f9fafb" }}>
                {["Carrera", "Inscriptos", "Cursando", "Graduados", "Desgran.", "Tesis en Des."].map((col) => (
                  <th key={col} style={{ padding: "10px 20px", textAlign: col === "Carrera" ? "left" : "center", fontSize: "12px", fontWeight: 600, color: "#6b7280" }}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {resumenCarreras.map((row, i) => (
                <tr key={i} style={{ borderTop: "1px solid #f3f4f6" }}>
                  <td style={{ padding: "12px 20px", fontSize: "13px", color: "#374151" }}>{row.carrera}</td>
                  <td style={{ padding: "12px 20px", textAlign: "center", fontSize: "13px", color: "#374151" }}>{row.inscriptos}</td>
                  <td style={{ padding: "12px 20px", textAlign: "center", fontSize: "13px", color: "#374151" }}>{row.cursando}</td>
                  <td style={{ padding: "12px 20px", textAlign: "center", fontSize: "13px", color: "#374151" }}>{row.graduados}</td>
                  <td style={{ padding: "12px 20px", textAlign: "center", fontSize: "13px", color: "#374151" }}>{row.desgranamiento}</td>
                  <td style={{ padding: "12px 20px", textAlign: "center", fontSize: "13px", color: "#374151" }}>{row.tesis}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
	</ScrollView>
    </AppLayout>
  );
}


const styles = StyleSheet.create({
  page: {
    padding: 24,
    maxWidth: 1000,
    width: "100%",
    alignSelf: "center",
  },
});