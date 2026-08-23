import { StyleSheet, Text, View } from "react-native";

export default function HealthScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Funciona!</Text>
      <Text style={styles.subtitle}>(en teoría...)</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f6f7fb",
    gap: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#111827",
  },
  subtitle: {
    fontSize: 15,
    color: "#6b7280",
  },
});
