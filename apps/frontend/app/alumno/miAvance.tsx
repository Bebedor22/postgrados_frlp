import {useState} from "react";
import {Pressable, ScrollView, StyleSheet, Text, View} from "react-native";
import {AlertTriangle, CheckCircle2, Circle, Clock, Download, FileText, Info, User} from "lucide-react-native";

const TABS = ["Resumen", "Seminarios", "TFI / Tesis", "Documentación", "Alertas", "Historial"];

const seminarios = [
  { id: 1, nombre: "Seminario de Investigación I", asistencia: 95, calificacion: 9, fecha: "Mar 2024", estado: "Aprobado" },
  { id: 2, nombre: "Metodología de la Investigación", asistencia: 88, calificacion: 8, fecha: "Abr 2024", estado: "Aprobado" },
  { id: 3, nombre: "Seminario de Tesis", asistencia: 92, calificacion: null, fecha: "En curso", estado: "Cursando" },
  { id: 4, nombre: "Seminario de Análisis de Datos", asistencia: null, calificacion: null, fecha: null, estado: "Pendiente" },
  { id: 5, nombre: "Trabajo Final Integrador", asistencia: null, calificacion: null, fecha: null, estado: "No iniciado" },
];

function StatusIcon({ estado }: { estado: string }) {
    if (estado === "Aprobado") return <CheckCircle2 size={22} color="#22c55e"/>;
    if (estado === "Cursando") return <Clock size={22} color="#f59e0b"/>;
    return <Circle size={22} color="#d1d5db"/>;
}

function StatusBadge({ estado }: { estado: string }) {
  const colors: Record<string, string> = {
    Aprobado: "#16a34a",
    Cursando: "#d97706",
    Pendiente: "#9ca3af",
    "No iniciado": "#9ca3af",
  };
  return (
    <Text style={[styles.statusBadge, { color: colors[estado] ?? "#374151" }]}>{estado}</Text>
  );
}

export default function MiAvance() {
  const [activeTab, setActiveTab] = useState("Resumen");
  const progreso = 62;

  return (
      <ScrollView contentContainerStyle={styles.page}>
        {/* Student card */}
        <View style={styles.card}>
          <View style={styles.avatar}>
              <User size={28} color="#9ca3af"/>
          </View>

          <View style={styles.studentInfo}>
            <Text style={styles.studentName}>Sofía Pérez</Text>
            <Text style={styles.studentMeta}>DNI: 34.567.890</Text>
            <Text style={styles.studentMeta}>Cohorte: 2023</Text>
            <Text style={styles.studentMeta}>Carrera: Maestría en Ciencias Sociales</Text>
          </View>

          <View style={styles.estadoCol}>
            <View style={styles.estadoCircle}>
              <Text style={styles.estadoLabel}>Estado</Text>
              <Text style={styles.estadoValue}>Regular</Text>
            </View>
            <Text style={styles.metaSmall}>Estado del Legajo</Text>
            <Text style={styles.legajoOk}>✓ Completo</Text>
          </View>

          <View style={styles.progresoCol}>
            <Text style={styles.metaSmall}>% Avance de Carrera</Text>
            <Text style={styles.progresoValue}>{progreso}%</Text>
            <View style={styles.progresoTrack}>
              <View style={[styles.progresoBar, { width: `${progreso}%` }]} />
            </View>
          </View>
        </View>

        {/* Tabs */}
        <View style={styles.cardTabs}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabsRow}>
            {TABS.map((tab) => (
              <Pressable key={tab} onPress={() => setActiveTab(tab)} hitSlop={4}>
                <Text
                  style={[
                    styles.tab,
                    activeTab === tab && styles.tabActive,
                  ]}
                >
                  {tab}
                </Text>
              </Pressable>
            ))}
          </ScrollView>

          <View style={styles.tabContent}>
            {activeTab === "Resumen" && (
              <>
                <Text style={styles.sectionTitle}>Progreso Académico</Text>
                <View>
                  {seminarios.map((s, i) => (
                    <View
                      key={s.id}
                      style={[styles.seminarioRow, i < seminarios.length - 1 && styles.seminarioRowBorder]}
                    >
                      <StatusIcon estado={s.estado} />
                      <View style={styles.seminarioInfo}>
                        <Text style={styles.seminarioNombre}>{s.nombre}</Text>
                        <Text style={styles.seminarioMeta}>
                          Asistencia: {s.asistencia !== null ? `${s.asistencia}%` : "-"}   ·   Calificación:{" "}
                          {s.calificacion !== null ? s.calificacion : "-"}   ·   Fecha: {s.fecha ?? "-"}
                        </Text>
                      </View>
                      <StatusBadge estado={s.estado} />
                    </View>
                  ))}
                </View>

                <Text style={[styles.sectionTitle, styles.sectionTitleSpaced]}>Alertas</Text>
                <View style={styles.alertsCol}>
                  <View style={styles.alertWarning}>
                      <AlertTriangle size={15} color="#d97706"/>
                    <Text style={styles.alertWarningText}>
                        Vencimiento de Seminario: 30 días restantes
                    </Text>
                  </View>
                  <View style={styles.alertInfo}>
                      <Info size={15} color="#3b82f6"/>
                    <Text style={styles.alertInfoText}>
                        Plazo TFI: 180 días restantes
                    </Text>
                  </View>
                </View>

                <View style={styles.actionsRow}>
                  <Pressable style={styles.primaryAction}>
                      <Download size={14} color="white"/>
                    <Text style={styles.primaryActionText}>Descargar Certificado Analítico</Text>
                  </Pressable>
                  <Pressable style={styles.secondaryAction}>
                    <Text style={styles.secondaryActionText}>Ver Historial Detallado</Text>
                  </Pressable>
                </View>
              </>
            )}

            {activeTab === "Alertas" && (
              <View style={styles.alertsCol}>
                <View style={styles.alertWarning}>
                    <AlertTriangle size={15} color="#d97706"/>
                  <Text style={styles.alertWarningText}>
                      Vencimiento de Seminario: 30 días restantes
                  </Text>
                </View>
                <View style={styles.alertInfo}>
                    <Info size={15} color="#3b82f6"/>
                    <Text style={styles.alertInfoText}>Plazo TFI: 180 días restantes</Text>
                </View>
              </View>
            )}

            {!["Resumen", "Alertas"].includes(activeTab) && (
                <View style={styles.placeholderContainer}>
                    <FileText size={36} color="#d1d5db" style={{marginBottom: 12}}/>
                    <Text style={styles.placeholder}>Sección disponible próximamente.</Text>
                </View>
            )}
          </View>
        </View>
      </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: {
    padding: 24,
    maxWidth: 1000,
    width: "100%",
    alignSelf: "center",
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 8,
    paddingVertical: 20,
    paddingHorizontal: 24,
    marginBottom: 16,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 20,
    flexWrap: "wrap",
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: "#e5e7eb",
    alignItems: "center",
    justifyContent: "center",
  },
  avatarIcon: {
    fontSize: 26,
  },
  studentInfo: {
    flex: 1,
    minWidth: 220,
  },
  studentName: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 4,
  },
  studentMeta: {
    fontSize: 13,
    color: "#6b7280",
    lineHeight: 22,
  },
  estadoCol: {
    alignItems: "center",
  },
  estadoCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "#f59e0b",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 6,
  },
  estadoLabel: {
    color: "#ffffff",
    fontSize: 10,
    fontWeight: "500",
  },
  estadoValue: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "700",
  },
  metaSmall: {
    fontSize: 12,
    color: "#6b7280",
    marginBottom: 2,
  },
  legajoOk: {
    fontSize: 12,
    color: "#16a34a",
    fontWeight: "500",
  },
  progresoCol: {
    minWidth: 120,
  },
  progresoValue: {
    fontSize: 28,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 6,
  },
  progresoTrack: {
    width: 120,
    height: 6,
    backgroundColor: "#e5e7eb",
    borderRadius: 4,
    overflow: "hidden",
  },
  progresoBar: {
    height: "100%",
    backgroundColor: "#22c55e",
    borderRadius: 4,
  },
  cardTabs: {
    backgroundColor: "#ffffff",
    borderRadius: 8,
    overflow: "hidden",
  },
  tabsRow: {
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
    gap: 8,
  },
  tab: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    fontSize: 13,
    color: "#6b7280",
  },
  tabActive: {
    fontWeight: "600",
    color: "#0d2035",
  },
  tabContent: {
    padding: 24,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: "600",
    marginBottom: 16,
    color: "#111827",
  },
  sectionTitleSpaced: {
    marginTop: 24,
    marginBottom: 12,
  },
  seminarioRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 16,
    paddingVertical: 14,
  },
  seminarioRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
  },
  statusIcon: {
    fontSize: 15,
  },
  seminarioInfo: {
    flex: 1,
  },
  seminarioNombre: {
    fontSize: 14,
    fontWeight: "500",
    color: "#111827",
    marginBottom: 3,
  },
  seminarioMeta: {
    fontSize: 12,
    color: "#6b7280",
  },
  statusBadge: {
    fontSize: 13,
    fontWeight: "500",
  },
  alertsCol: {
    gap: 8,
  },
  alertWarning: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: "#fefce8",
    borderWidth: 1,
    borderColor: "#fde68a",
    borderRadius: 6,
  },
  alertWarningText: {
    fontSize: 13,
    color: "#92400e",
  },
  alertInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: "#eff6ff",
    borderWidth: 1,
    borderColor: "#bfdbfe",
    borderRadius: 6,
  },
  alertInfoText: {
    fontSize: 13,
    color: "#1e40af",
  },
  actionsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
    marginTop: 24,
  },
  primaryAction: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 18,
    backgroundColor: "#0d2035",
    borderRadius: 6,
  },
  primaryActionText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "500",
  },
  secondaryAction: {
    paddingVertical: 10,
    paddingHorizontal: 18,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 6,
  },
  secondaryActionText: {
    color: "#374151",
    fontSize: 13,
    fontWeight: "500",
  },
    placeholderContainer: {
        alignItems: "center",
        justifyContent: "center",
        paddingVertical: 40,
    },
  placeholder: {
    color: "#6b7280",
    fontSize: 14,
    textAlign: "center",
  },
});
