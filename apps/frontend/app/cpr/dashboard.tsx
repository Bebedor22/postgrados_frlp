import type {ReactNode} from "react";
import {Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View} from "react-native";
import Svg, {Circle as SvgCircle, Line, Polyline, Rect} from "react-native-svg";
import {AppLayout} from "../../src/components/layout/AppLayout";

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
  {name: "En proceso", value: 45, color: "#f59e0b"},
  { name: "Aprobados", value: 35, color: "#22c55e" },
  {name: "No iniciados", value: 20, color: "#ef4444"},
];

const resumenCarreras = [
  {
    carrera: "Maestría en Ingeniería Gerencial",
    inscriptos: 98,
    cursando: 76,
    graduados: 68,
    desgranamiento: "22%",
    tesis: 28,
  },
  {
    carrera: "Doctorado en Materiales",
    inscriptos: 56,
    cursando: 42,
    graduados: 24,
    desgranamiento: "25%",
    tesis: 19,
  },
  {
    carrera: "Especialización Ingeniería Ambiental",
    inscriptos: 32,
    cursando: 24,
    graduados: 12,
    desgranamiento: "38%",
    tesis: 9,
  },
];

const navItems = [
  { icon: "📊", label: "Dashboard", to: "/cpr/dashboard", group: "Portal Conducción" },
  { icon: "📋", label: "Gestión de Inscripciones", to: "/cpr/gestionDeInscripciones", group: "Portal Conducción" },
  { icon: "🔍", label: "Buscador de Estudiantes", to: "/cpr/buscadorEstudiantes", group: "Portal Conducción" },
  { icon: "📑", label: "Reportes y Exportación", to: "/cpr/dashboard", group: "Portal Conducción" },
  { icon: "📄", label: "Gestión de Tesis", to: "/cpr/gestionDeTesis", group: "Portal Conducción" },
  { icon: "⏳", label: "Alertas y Vencimientos", to: "/cpr/dashboard", group: "Portal Conducción" },
  { icon: "⚙️", label: "Configuración", to: "/cpr/dashboard", group: "Portal Conducción" },
];

function KpiCard({
                   label,
                   value,
                   sub,
                   icon,
                   dark,
                 }: {
  label: string;
  value: string | number;
  sub: string;
  icon: ReactNode;
  dark?: boolean;
}) {
  return (
      <View style={[styles.kpiCard, dark && styles.kpiCardDark]}>
        <View style={styles.kpiHeader}>
          <Text style={[styles.kpiLabel, dark && styles.kpiLabelDark]}>{label}</Text>
          <Text style={[styles.kpiIcon, dark && styles.kpiIconDark]}>{icon}</Text>
        </View>
        <Text style={[styles.kpiValue, dark && styles.kpiValueDark]}>{value}</Text>
        <Text style={[styles.kpiSub, dark && styles.kpiSubDark]}>{sub}</Text>
      </View>
  );
}

function LineChart() {
  const width = 420;
  const height = 170;
  const padding = 24;
  const max = Math.max(...lineData.map((item) => item.inscriptos));
  const min = Math.min(...lineData.map((item) => item.inscriptos));
  const range = max - min || 1;
  const points = lineData
      .map((item, index) => {
        const x = padding + (index / (lineData.length - 1)) * (width - padding * 2);
        const y = padding + ((max - item.inscriptos) / range) * (height - padding * 2);
        return `${x},${y}`;
      })
      .join(" ");

  return (
      <View style={styles.chartBlock}>
        <Svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
          <Line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#e5e7eb"/>
          <Line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#e5e7eb"/>
          <Polyline points={points} fill="none" stroke="#1d6b59" strokeWidth={3} strokeLinecap="round"
                    strokeLinejoin="round"/>
          {lineData.map((item, index) => {
            const x = padding + (index / (lineData.length - 1)) * (width - padding * 2);
            const y = padding + ((max - item.inscriptos) / range) * (height - padding * 2);
            return <SvgCircle key={item.year} cx={x} cy={y} r={4} fill="#1d6b59"/>;
          })}
        </Svg>
        <View style={styles.axisLabels}>
          {lineData.map((item) => (
              <Text key={item.year} style={styles.axisLabel}>
                {item.year}
              </Text>
          ))}
        </View>
      </View>
  );
}

function DonutChart() {
  const size = 150;
  const strokeWidth = 22;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  return (
      <View style={styles.donutWrap}>
        <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {pieData.map((item) => {
            const length = (item.value / 100) * circumference;
            const segment = (
                <SvgCircle
                    key={item.name}
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    stroke={item.color}
                    strokeWidth={strokeWidth}
                    strokeDasharray={`${length} ${circumference - length}`}
                    strokeDashoffset={-offset}
                    strokeLinecap="butt"
                    fill="none"
                />
            );
            offset += length;
            return segment;
          })}
        </Svg>
        <View style={styles.donutCenter}>
          <Text style={styles.donutValue}>100%</Text>
          <Text style={styles.donutLabel}>TFI</Text>
        </View>
      </View>
  );
}

function BarChart() {
  const width = 560;
  const height = 190;
  const padding = 28;
  const max = Math.max(...barData.map((item) => item.graduados));
  const slotWidth = (width - padding * 2) / barData.length;
  const barWidth = 34;

  return (
      <View style={styles.chartBlock}>
        <Svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
          <Line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#e5e7eb"/>
          {barData.map((item, index) => {
            const barHeight = (item.graduados / max) * (height - padding * 2);
            const x = padding + index * slotWidth + (slotWidth - barWidth) / 2;
            const y = height - padding - barHeight;
            return <Rect key={item.cohorte} x={x} y={y} width={barWidth} height={barHeight} rx={5} fill="#0d2035"/>;
          })}
        </Svg>
        <View style={styles.axisLabels}>
          {barData.map((item) => (
              <Text key={item.cohorte} style={styles.axisLabel}>
                {item.cohorte}
              </Text>
          ))}
        </View>
      </View>
  );
}

export default function Dashboard() {
  const {width} = useWindowDimensions();
  const isCompact = width < 1040;

  return (
      <AppLayout portalTitle="Portal Conducción" navItems={navItems}>
        <ScrollView contentContainerStyle={styles.page}>
          <View style={styles.headerRow}>
            <View>
              <Text style={styles.eyebrow}>Panel CPR</Text>
              <Text style={styles.title}>Dashboard académico</Text>
            </View>
            <Pressable style={styles.exportButton}>
              <Text style={styles.exportButtonText}>Exportar</Text>
            </Pressable>
          </View>

          <View style={[styles.filtersRow, isCompact && styles.wrapRow]}>
          {[
            {label: "Carrera", value: "Todas"},
            {label: "Cohorte", value: "Todas"},
            {label: "Período", value: "Último año"},
          ].map((filter) => (
              <View key={filter.label} style={styles.filterBox}>
                <Text style={styles.filterLabel}>{filter.label}</Text>
                <Text style={styles.filterValue}>{filter.value}</Text>
              </View>
          ))}
          </View>

          <View style={[styles.kpiRow, isCompact && styles.wrapRow]}>
            <KpiCard label="Total inscriptos" value={186} sub="+12% vs año anterior" icon="👥"/>
            <KpiCard label="Cursando" value={142} sub="76% del total" icon="📚"/>
            <KpiCard label="Graduados" value={104} sub="+8% vs 2024" icon="🎓"/>
            <KpiCard label="Desgranamiento" value="28%" sub="-3% vs cohorte anterior" icon="⚠"/>
            <KpiCard label="Tesis en desarrollo" value={56} sub="39% de cursantes" icon="📝" dark/>
          </View>

          <View style={[styles.chartRow, isCompact && styles.chartRowCompact]}>
            <View style={styles.panel}>
              <Text style={styles.panelTitle}>Evolución de inscripciones</Text>
              <LineChart/>
            </View>

            <View style={styles.panel}>
              <Text style={styles.panelTitle}>Situación de trabajos finales</Text>
              <View style={styles.pieContent}>
                <DonutChart/>
                <View style={styles.legend}>
                  {pieData.map((item) => (
                      <View key={item.name} style={styles.legendItem}>
                        <View style={[styles.legendDot, {backgroundColor: item.color}]}/>
                        <Text style={styles.legendText}>
                          {item.name} {item.value}%
                        </Text>
                      </View>
                ))}
                </View>
              </View>
            </View>
          </View>

          <View style={styles.panel}>
            <Text style={styles.panelTitle}>Graduaciones por cohorte</Text>
            <BarChart/>
          </View>

          <View style={styles.panel}>
            <Text style={styles.panelTitle}>Resumen por carrera</Text>
            <View style={styles.table}>
              <View style={[styles.tableRow, styles.tableHeader]}>
                {["Carrera", "Inscriptos", "Cursando", "Graduados", "Desgran.", "Tesis"].map((column, index) => (
                    <Text key={column} style={[styles.tableHeaderText, index === 0 && styles.careerCell]}>
                      {column}
                    </Text>
                ))}
              </View>
              {resumenCarreras.map((row) => (
                  <View key={row.carrera} style={styles.tableRow}>
                    <Text style={[styles.tableCell, styles.careerCell]}>{row.carrera}</Text>
                    <Text style={styles.tableCell}>{row.inscriptos}</Text>
                    <Text style={styles.tableCell}>{row.cursando}</Text>
                    <Text style={styles.tableCell}>{row.graduados}</Text>
                    <Text style={styles.tableCell}>{row.desgranamiento}</Text>
                    <Text style={styles.tableCell}>{row.tesis}</Text>
                  </View>
              ))}
            </View>
          </View>
        </ScrollView>
    </AppLayout>
  );
}

const styles = StyleSheet.create({
  page: {
    width: "100%",
    maxWidth: 1120,
    alignSelf: "center",
    padding: 24,
    gap: 16,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 16,
  },
  eyebrow: {
    color: "#6b7280",
    fontSize: 12,
    fontWeight: "600",
    textTransform: "uppercase",
  },
  title: {
    marginTop: 3,
    color: "#111827",
    fontSize: 22,
    fontWeight: "700",
  },
  exportButton: {
    minHeight: 36,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0d2035",
    borderRadius: 6,
  },
  exportButtonText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "600",
  },
  filtersRow: {
    flexDirection: "row",
    gap: 12,
  },
  wrapRow: {
    flexWrap: "wrap",
  },
  filterBox: {
    minWidth: 160,
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
  },
  filterLabel: {
    marginBottom: 3,
    color: "#6b7280",
    fontSize: 11,
    fontWeight: "500",
  },
  filterValue: {
    color: "#111827",
    fontSize: 13,
    fontWeight: "600",
  },
  kpiRow: {
    flexDirection: "row",
    gap: 12,
  },
  kpiCard: {
    flex: 1,
    minWidth: 170,
    padding: 16,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
  },
  kpiCardDark: {
    backgroundColor: "#0d2035",
    borderColor: "#0d2035",
  },
  kpiHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 8,
  },
  kpiLabel: {
    color: "#6b7280",
    fontSize: 12,
  },
  kpiLabelDark: {
    color: "rgba(255,255,255,0.66)",
  },
  kpiIcon: {
    color: "#9ca3af",
    fontSize: 16,
  },
  kpiIconDark: {
    color: "rgba(255,255,255,0.52)",
  },
  kpiValue: {
    marginTop: 8,
    color: "#111827",
    fontSize: 26,
    fontWeight: "700",
  },
  kpiValueDark: {
    color: "#ffffff",
  },
  kpiSub: {
    marginTop: 2,
    color: "#9ca3af",
    fontSize: 11,
  },
  kpiSubDark: {
    color: "rgba(255,255,255,0.56)",
  },
  chartRow: {
    flexDirection: "row",
    gap: 16,
  },
  chartRowCompact: {
    flexDirection: "column",
  },
  panel: {
    flex: 1,
    minWidth: 0,
    padding: 20,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
  },
  panelTitle: {
    marginBottom: 14,
    color: "#111827",
    fontSize: 14,
    fontWeight: "600",
  },
  chartBlock: {
    width: "100%",
  },
  axisLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 12,
  },
  axisLabel: {
    color: "#6b7280",
    fontSize: 10,
  },
  pieContent: {
    minHeight: 176,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 24,
  },
  donutWrap: {
    width: 150,
    height: 150,
    alignItems: "center",
    justifyContent: "center",
  },
  donutCenter: {
    position: "absolute",
    alignItems: "center",
  },
  donutValue: {
    color: "#111827",
    fontSize: 18,
    fontWeight: "700",
  },
  donutLabel: {
    color: "#6b7280",
    fontSize: 11,
    fontWeight: "600",
  },
  legend: {
    gap: 10,
  },
  legendItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  legendText: {
    color: "#374151",
    fontSize: 12,
  },
  table: {
    borderWidth: 1,
    borderColor: "#f3f4f6",
    borderRadius: 6,
    overflow: "hidden",
  },
  tableRow: {
    flexDirection: "row",
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: "#f3f4f6",
  },
  tableHeader: {
    borderTopWidth: 0,
    backgroundColor: "#f9fafb",
  },
  tableHeaderText: {
    flex: 1,
    paddingHorizontal: 10,
    paddingVertical: 10,
    color: "#6b7280",
    fontSize: 11,
    fontWeight: "700",
    textAlign: "center",
  },
  tableCell: {
    flex: 1,
    paddingHorizontal: 10,
    paddingVertical: 12,
    color: "#374151",
    fontSize: 12,
    textAlign: "center",
  },
  careerCell: {
    flex: 2.4,
    textAlign: "left",
  },
});
