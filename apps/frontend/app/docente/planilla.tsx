import { useState } from "react";
import { Link } from "expo-router";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { AppLayout } from "../../src/components/layout/AppLayout";

const FECHAS = ["12/03", "19/03", "26/03", "02/04", "09/04", "16/04"];

type EstudianteRow = {
  id: number;
  nombre: string;
  dni: string;
  asistencias: boolean[];
  calificacion: string;
};

const initialEstudiantes: EstudianteRow[] = [
  { id: 1, nombre: "Pérez, Sofía",     dni: "34.567.890", asistencias: [true,  true,  true,  true,  false, true ], calificacion: "9"  },
  { id: 2, nombre: "García, Laura",    dni: "31.234.567", asistencias: [true,  true,  false, true,  true,  true ], calificacion: "8"  },
  { id: 3, nombre: "López, Martín",    dni: "28.876.543", asistencias: [true,  false, true,  false, true,  false], calificacion: ""   },
  { id: 4, nombre: "Ramírez, Tomás",   dni: "33.117.222", asistencias: [false, true,  false, false, true,  false], calificacion: "4"  },
  { id: 5, nombre: "Silva, Valentina", dni: "30.222.333", asistencias: [true,  true,  true,  true,  true,  true ], calificacion: ""   },
  { id: 6, nombre: "Martínez, Diego",  dni: "27.543.210", asistencias: [true,  false, false, true,  false, true ], calificacion: "7"  },
];

const docenteNav = [
  { icon: "🕮", label: "Mis Cursos", to: "/docente/misCursos", group: "Gestión Académica" },
  { icon: "📋", label: "Planilla de Carga", to: "/docente/planilla", group: "Gestión Académica" },
];

function calcPct(asistencias: boolean[]) {
  return Math.round((asistencias.filter(Boolean).length / asistencias.length) * 100);
}

function autoEstado(pct: number, cal: string): { label: string; color: string } {
  if (pct < 75)         return { label: "Libre",     color: "#ef4444" };
  if (cal === "")       return { label: "Cursando",  color: "#f59e0b" };
  if (Number(cal) >= 6) return { label: "Aprobado",  color: "#22c55e" };
  return                       { label: "Reprobado", color: "#ef4444" };
}

export default function PlanillaDocente() {
  const [rows, setRows] = useState<EstudianteRow[]>(initialEstudiantes);
  const [saved, setSaved] = useState(false);

  const toggleAsistencia = (rowId: number, fechaIdx: number) => {
    setRows((prev) =>
      prev.map((r) =>
        r.id === rowId
          ? { ...r, asistencias: r.asistencias.map((v, i) => (i === fechaIdx ? !v : v)) }
          : r
      )
    );
    setSaved(false);
  };

  const setCalificacion = (rowId: number, val: string) => {
    const n = val.replace(/[^0-9]/g, "");
    if (n !== "" && Number(n) > 10) return;
    setRows((prev) => prev.map((r) => (r.id === rowId ? { ...r, calificacion: n } : r)));
    setSaved(false);
  };

  const handleGuardar = () => setSaved(true);

  return (
    <AppLayout portalTitle="Portal Docente" navItems={docenteNav}>
      <ScrollView contentContainerStyle={styles.page}>
        {/* Seminar info bar */}
        <View style={styles.infoBar}>
          <View style={styles.infoStats}>
            {[
              { label: "Cohorte", value: "2024" },
              { label: "Período", value: "1° Cuatr. 2025" },
              { label: "Estudiantes", value: `${rows.length}` },
              { label: "Clases registradas", value: `${FECHAS.length}` },
            ].map((item) => (
              <View key={item.label} style={styles.statItem}>
                <Text style={styles.statLabel}>{item.label}</Text>
                <Text style={styles.statValue}>{item.value}</Text>
              </View>
            ))}
          </View>
          <Link href="/docente/misCursos" asChild>
            <Pressable hitSlop={6}>
              <Text style={styles.backText}>‹ Volver a mis cursos</Text>
            </Pressable>
          </Link>
        </View>

        {/* Table */}
        <View style={styles.tableCard}>
          <View style={[styles.headerRow, styles.rowBorder]}>
            <View style={styles.colStudent}>
              <Text style={styles.headerText}>Estudiante</Text>
            </View>
            {FECHAS.map((f) => (
              <View key={f} style={styles.colFecha}>
                <Text style={styles.headerTextSmall}>{f}</Text>
              </View>
            ))}
            <View style={styles.colPct}>
              <Text style={styles.headerText}>% Asist.</Text>
            </View>
            <View style={styles.colCal}>
              <Text style={styles.headerText}>Calificación</Text>
            </View>
            <View style={styles.colEstado}>
              <Text style={styles.headerText}>Estado</Text>
            </View>
          </View>

          {rows.map((row) => {
            const pct = calcPct(row.asistencias);
            const estado = autoEstado(pct, row.calificacion);
            return (
              <View key={row.id} style={[styles.bodyRow, styles.rowBorder]}>
                <View style={styles.colStudent}>
                  <Text style={styles.studentNombre}>{row.nombre}</Text>
                  <Text style={styles.studentDni}>{row.dni}</Text>
                </View>

                {row.asistencias.map((present, fi) => (
                  <View key={fi} style={styles.colFecha}>
                    <Pressable
                      onPress={() => toggleAsistencia(row.id, fi)}
                      hitSlop={8}
                      accessibilityRole="checkbox"
                      accessibilityState={{ checked: present }}
                    >
                      <View style={[styles.checkbox, present && styles.checkboxChecked]}>
                        {present && <Text style={styles.checkMark}>✓</Text>}
                      </View>
                    </Pressable>
                  </View>
                ))}

                <View style={styles.colPct}>
                  <Text style={[styles.pctText, { color: pct >= 75 ? "#16a34a" : "#ef4444" }]}>
                    {pct}%
                  </Text>
                </View>

                <View style={styles.colCal}>
                  <TextInput
                    style={styles.calInput}
                    keyboardType="number-pad"
                    maxLength={2}
                    value={row.calificacion}
                    onChangeText={(v) => setCalificacion(row.id, v)}
                    placeholder="—"
                  />
                </View>

                <View style={styles.colEstado}>
                  <Text style={[styles.estadoBadge, { color: estado.color, backgroundColor: `${estado.color}18` }]}>
                    {estado.label}
                  </Text>
                </View>
              </View>
            );
          })}
        </View>

        {/* Footer actions */}
        <View style={styles.footerRow}>
          <View>
            {saved && <Text style={styles.savedText}>✓ Cambios guardados correctamente</Text>}
          </View>
          <View style={styles.footerActions}>
            <Pressable style={styles.secondaryAction} onPress={handleGuardar}>
              <Text style={styles.secondaryActionText}>💾 Guardar borrador</Text>
            </Pressable>
            <Pressable style={styles.primaryAction} onPress={handleGuardar}>
              <Text style={styles.primaryActionText}>🖱 Guardar y Enviar Actas</Text>
            </Pressable>
          </View>
        </View>
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
  infoBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: 12,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
    paddingVertical: 14,
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  infoStats: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 32,
  },
  statItem: {},
  statLabel: {
    fontSize: 11,
    color: "#6b7280",
    marginBottom: 2,
  },
  statValue: {
    fontSize: 14,
    fontWeight: "600",
    color: "#111827",
  },
  backText: {
    fontSize: 13,
    color: "#6b7280",
  },
  tableCard: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
    overflow: "hidden",
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#f9fafb",
    paddingVertical: 10,
  },
  bodyRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
  },
  rowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
  },
  colStudent: {
    flex: 3,
    minWidth: 160,
    paddingHorizontal: 16,
    gap: 2,
  },
  colFecha: {
    width: 48,
    alignItems: "center",
  },
  colPct: {
    width: 64,
    alignItems: "center",
    borderLeftWidth: 2,
    borderLeftColor: "#e5e7eb",
    alignSelf: "stretch",
    justifyContent: "center",
  },
  colCal: {
    width: 90,
    alignItems: "center",
  },
  colEstado: {
    width: 96,
    alignItems: "center",
  },
  headerText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#6b7280",
  },
  headerTextSmall: {
    fontSize: 11,
    fontWeight: "600",
    color: "#6b7280",
  },
  studentNombre: {
    fontSize: 13,
    fontWeight: "500",
    color: "#111827",
  },
  studentDni: {
    fontSize: 11,
    color: "#6b7280",
  },
  checkbox: {
    width: 18,
    height: 18,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: "#9ca3af",
    backgroundColor: "#ffffff",
    alignItems: "center",
    justifyContent: "center",
  },
  checkboxChecked: {
    backgroundColor: "#2d7a65",
    borderColor: "#2d7a65",
  },
  checkMark: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "700",
  },
  pctText: {
    fontSize: 13,
    fontWeight: "600",
  },
  calInput: {
    width: 52,
    minHeight: 34,
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 5,
    fontSize: 13,
    textAlign: "center",
    color: "#111827",
    backgroundColor: "#ffffff",
  },
  estadoBadge: {
    fontSize: 12,
    fontWeight: "600",
    overflow: "hidden",
    paddingVertical: 3,
    paddingHorizontal: 10,
    borderRadius: 12,
  },
  footerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 20,
    gap: 12,
  },
  savedText: {
    fontSize: 13,
    color: "#16a34a",
    fontWeight: "500",
  },
  footerActions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  secondaryAction: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 20,
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
  primaryAction: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: "#0d2035",
    borderRadius: 6,
  },
  primaryActionText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "500",
  },
});
