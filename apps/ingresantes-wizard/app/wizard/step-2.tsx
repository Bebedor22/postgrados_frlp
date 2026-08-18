import type { ReactNode } from "react";
import { Link } from "expo-router";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

export default function Step2Screen() {
  return (
    <View style={styles.container}>
      <Card step="2 / 4" title="Contacto y residencia" subtitle="Sumamos los datos de contacto.">
        <TextInput placeholder="Teléfono" keyboardType="phone-pad" style={styles.input} />
        <TextInput placeholder="Provincia" style={styles.input} />
        <TextInput placeholder="Localidad" style={styles.input} />
      </Card>

      <View style={styles.row}>
        <Link href="/wizard/step-1" asChild>
          <Pressable style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonText}>Volver</Text>
          </Pressable>
        </Link>
        <Link href="/wizard/step-3" asChild>
          <Pressable style={styles.primaryButton}>
            <Text style={styles.primaryButtonText}>Continuar</Text>
          </Pressable>
        </Link>
      </View>
    </View>
  );
}

function Card({
  step,
  title,
  subtitle,
  children,
}: {
  step: string;
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <View style={styles.card}>
      <Text style={styles.step}>{step}</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
      <View style={styles.fields}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, gap: 16, justifyContent: "center" },
  card: { backgroundColor: "#fff", borderRadius: 24, padding: 24, gap: 8 },
  step: { color: "#2d7a65", fontWeight: "700" },
  title: { fontSize: 28, fontWeight: "800", color: "#111827" },
  subtitle: { color: "#4b5563", fontSize: 15, lineHeight: 22 },
  fields: { gap: 12, marginTop: 8 },
  input: {
    backgroundColor: "#f3f4f6",
    paddingHorizontal: 14,
    paddingVertical: 14,
    borderRadius: 14,
    fontSize: 16,
  },
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
