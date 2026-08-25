import {useRouter} from "expo-router";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {BookOpen, Calendar, ChevronRight, Users} from "lucide-react-native";
import {PageHeader} from "../../src/components/layout/AppLayout";

const cursosActivos = [
  {
    id: 1,
    nombre: "Seminario de Investigación Cuantitativa",
    cohorte: "2024",
    cuatrimestre: "1° Cuatr. 2025",
    estudiantes: 18,
    estado: "Activo",
  },
];

const otrosCursos = [
  {
    id: 2,
    nombre: "Metodología de la Investigación",
    cohorte: "2024",
    cuatrimestre: "2° Cuatr. 2024",
    estudiantes: 22,
    estado: "Finalizado",
  },
  {
    id: 3,
    nombre: "Seminario de Tesis I",
    cohorte: "2023",
    cuatrimestre: "1° Cuatr. 2024",
    estudiantes: 15,
    estado: "Finalizado",
  },
  {
    id: 4,
    nombre: "Seminario de Investigación Cualitativa",
    cohorte: "2025",
    cuatrimestre: "2° Cuatr. 2025",
    estudiantes: null,
    estado: "Próximo",
  },
];

function EstadoBadge({ estado }: { estado: string }) {
  const map: Record<string, string> = {
    Activo: "#16a34a",
    Finalizado: "#6b7280",
    Próximo: "#2563eb",
  };
  return (
    <Text style={[styles.estadoBadge, { color: map[estado] ?? "#374151" }]}>{estado}</Text>
  );
}

export default function MisCursosScreen() {
  const router = useRouter();

  return (
      <>
        <PageHeader title="Mis Cursos"/>
      <View style={styles.page}>
        <View style={styles.legendRow}>
          <View style={styles.legendDot} />
          <Text style={styles.legendText}>Cursos en curso</Text>
        </View>
        {cursosActivos.map((curso) => (
          <View key={curso.id} style={styles.cursoCard}>
            <View style={styles.cursoIcon}>
              <BookOpen size={22} color="white"/>
            </View>
            <View style={styles.cursoInfo}>
              <Text style={styles.cursoNombre}>{curso.nombre}</Text>
              <View style={styles.cursoMetaRow}>
                <View style={styles.metaItem}>
                  <Calendar size={14} color="#6b7280"/>
                  <Text style={styles.cursoMeta}>
                    Cohorte {curso.cohorte} · {curso.cuatrimestre}
                  </Text>
                </View>
                <View style={styles.metaItem}>
                  <Users size={14} color="#6b7280"/>
                  <Text style={styles.cursoMeta}>{curso.estudiantes} estudiantes</Text>
                </View>
                <EstadoBadge estado={curso.estado} />
              </View>
            </View>
            <Pressable style={styles.primaryButton} onPress={() => router.push("/docente/planilla")}>
              <Text style={styles.primaryButtonText}>Gestionar</Text>
              <ChevronRight size={14} color="white"/>
            </Pressable>
          </View>
        ))}

        <Text style={styles.otrosTitulo}>Otros cursos</Text>
        <View style={styles.otrosCard}>
          {otrosCursos.map((curso, i) => (
            <View
              key={curso.id}
              style={[styles.otroCursoRow, i < otrosCursos.length - 1 && styles.otroCursoRowBorder]}
            >
              <View style={styles.otroCursoIcon}>
                <BookOpen size={18} color="#6b7280"/>
              </View>
              <View style={styles.cursoInfo}>
                <Text style={styles.otroCursoNombre}>{curso.nombre}</Text>
                <View style={styles.cursoMetaRow}>
                  <View style={styles.metaItem}>
                    <Calendar size={12} color="#6b7280"/>
                    <Text style={styles.cursoMetaSmall}>
                      Cohorte {curso.cohorte} · {curso.cuatrimestre}
                    </Text>
                  </View>
                  {curso.estudiantes !== null && (
                      <View style={styles.metaItem}>
                        <Users size={12} color="#6b7280"/>
                        <Text style={styles.cursoMetaSmall}>{curso.estudiantes} estudiantes</Text>
                      </View>
                  )}
                  <EstadoBadge estado={curso.estado} />
                </View>
              </View>
              {curso.estado === "Finalizado" && (
                <Pressable style={styles.secondaryButton}>
                  <Text style={styles.secondaryButtonText}>Ver actas</Text>
                  <ChevronRight size={12} color="#374151"/>
                </Pressable>
              )}
            </View>
          ))}
        </View>
      </View>
      </>
  );
}

const styles = StyleSheet.create({
  page: {
    flex: 1,
    padding: 24,
    maxWidth: 900,
    width: "100%",
    alignSelf: "center",
  },
  legendRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 12,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#22c55e",
  },
  legendText: {
    fontSize: 13,
    fontWeight: "500",
    color: "#374151",
  },
  cursoCard: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
    paddingVertical: 16,
    paddingHorizontal: 20,
    flexDirection: "row",
    alignItems: "center",
    gap: 16,
    marginBottom: 16,
  },
  cursoIcon: {
    width: 44,
    height: 44,
    borderRadius: 10,
    backgroundColor: "#0d2035",
    alignItems: "center",
    justifyContent: "center",
  },
  cursoIconActive: {
    color: "#ffffff",
    fontSize: 22,
  },
  cursoInfo: {
    flex: 1,
    minWidth: 180,
  },
  cursoNombre: {
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 4,
  },
  cursoMetaRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 16,
    alignItems: "center",
  },
  metaItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  cursoMeta: {
    fontSize: 12,
    color: "#6b7280",
  },
  cursoMetaSmall: {
    fontSize: 11,
    color: "#6b7280",
  },
  primaryButton: {
    flexDirection: "row",
    paddingVertical: 9,
    paddingHorizontal: 18,
    backgroundColor: "#0d2035",
    borderRadius: 6,
    alignItems: "center",
    gap: 6,
  },
  primaryButtonText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "500",
  },
  otrosTitulo: {
    fontSize: 13,
    fontWeight: "500",
    color: "#374151",
    marginVertical: 12,
  },
  otrosCard: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
    overflow: "hidden",
  },
  otroCursoRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 16,
    paddingVertical: 14,
    paddingHorizontal: 20,
  },
  otroCursoRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
  },
  otroCursoIcon: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: "#f3f4f6",
    alignItems: "center",
    justifyContent: "center",
  },
  otroCursoIconText: {
    fontSize: 17,
  },
  otroCursoNombre: {
    fontSize: 14,
    fontWeight: "500",
    color: "#111827",
    marginBottom: 2,
  },
  secondaryButton: {
    flexDirection: "row",
    paddingVertical: 7,
    paddingHorizontal: 14,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 5,
    alignItems: "center",
    gap: 4,
  },
  secondaryButtonText: {
    color: "#374151",
    fontSize: 12,
  },
  estadoBadge: {
    fontSize: 12,
    fontWeight: "500",
  },
});
