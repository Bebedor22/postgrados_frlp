import type { ReactNode } from "react";
import { Link } from "expo-router";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

export default function Step1Screen() {
  return (
    <View style={styles.container}>
      <WizardCard
        step="1 / 4"
        title="Datos personales"
        subtitle="Arrancamos con el alta del aspirante."
      >
        <TextInput placeholder="Nombre" style={styles.input} />
        <TextInput placeholder="Apellido" style={styles.input} />
        <TextInput placeholder="DNI" keyboardType="numeric" style={styles.input} />
        <TextInput placeholder="Email" keyboardType="email-address" style={styles.input} />
      </WizardCard>

      <Link href="/wizard/step-2" asChild>
        <Pressable style={styles.primaryButton}>
          <Text style={styles.primaryButtonText}>Continuar</Text>
        </Pressable>
      </Link>
    </View>
  );
}

function WizardCard({
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
  primaryButton: {
    backgroundColor: "#0d2035",
    paddingVertical: 16,
    borderRadius: 16,
    alignItems: "center",
  },
  primaryButtonText: { color: "#fff", fontSize: 16, fontWeight: "700" },
});
