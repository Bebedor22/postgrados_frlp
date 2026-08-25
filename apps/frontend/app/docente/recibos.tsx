import {StyleSheet, Text, View} from "react-native";

export default function Recibos() {
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Recibos de Sueldo</Text>
            <Text style={styles.subtitle}>Sección disponible próximamente.</Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        padding: 24,
    },
    title: {
        fontSize: 18,
        fontWeight: "600",
        color: "#111827",
    },
    subtitle: {
        fontSize: 14,
        color: "#6b7280",
    },
});
