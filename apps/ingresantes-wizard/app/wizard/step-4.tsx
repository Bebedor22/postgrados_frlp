import { useState } from "react";
import { Link } from "expo-router";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";
import { scheduleTestNotification } from "../../src/lib/notifications";

export default function Step4Screen() {
  const [scheduled, setScheduled] = useState(false);

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.step}>4 / 4</Text>
        <Text style={styles.title}>Documentación y notificaciones</Text>
        <Text style={styles.subtitle}>
          Acá más adelante van a ir los uploads y el aviso de estado de trámite.
        </Text>

        <View style={styles.notice}>
          <Text style={styles.noticeTitle}>Boilerplate listo</Text>
          <Text style={styles.noticeText}>Expo Notifications ya está instalado y conectado.</Text>
        </View>

        <Pressable
          style={styles.secondaryButton}
          onPress={async () => {
            await scheduleTestNotification();
            setScheduled(true);
            Alert.alert("Notificación", "Se programó una notificación de prueba.");
          }}
        >
          <Text style={styles.secondaryButtonText}>Probar notificación</Text>
        </Pressable>

        {scheduled && <Text style={styles.success}>Notificación de prueba programada.</Text>}
      </View>

      <View style={styles.row}>
        <Link href="/wizard/step-3" asChild>
          <Pressable style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonText}>Volver</Text>
          </Pressable>
        </Link>
        <Link href="/" asChild>
          <Pressable style={styles.primaryButton}>
            <Text style={styles.primaryButtonText}>Finalizar</Text>
          </Pressable>
        </Link>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, gap: 16, justifyContent: "center" },
  card: { backgroundColor: "#fff", borderRadius: 24, padding: 24, gap: 12 },
  step: { color: "#2d7a65", fontWeight: "700" },
  title: { fontSize: 28, fontWeight: "800", color: "#111827" },
  subtitle: { color: "#4b5563", fontSize: 15, lineHeight: 22 },
  notice: { backgroundColor: "#eef6ff", borderRadius: 16, padding: 16, gap: 4 },
  noticeTitle: { fontWeight: "700", color: "#1d4ed8" },
  noticeText: { color: "#1e3a8a" },
  success: { color: "#1d6b59", fontWeight: "700" },
  row: { flexDirection: "row", gap: 12 },
  primaryButton: {
    flex: 1,
    backgroundColor: "#0d2035",
    paddingVertical: 16,
    borderRadius: 16,
    alignItems: "center",
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: "#e8f3ef",
    paddingVertical: 16,
    borderRadius: 16,
    alignItems: "center",
  },
  primaryButtonText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  secondaryButtonText: { color: "#1d6b59", fontSize: 16, fontWeight: "700" },
});
