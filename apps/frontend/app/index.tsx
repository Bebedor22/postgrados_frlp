import {Link} from "expo-router";
import {useEffect, useState} from "react";
import {Pressable, StyleSheet, Text, View} from "react-native";
import {scheduleTestNotification} from "../src/lib/notifications";
import {obtenerTokenTramite} from "../src/lib/sesion";

export default function HomeScreen() {
    // Si el aspirante ya empezó una inscripción en este navegador, puede retomarla
    const [tokenTramite, setTokenTramite] = useState<string | null>(null);
    useEffect(() => setTokenTramite(obtenerTokenTramite()), []);

    return (
        <View style={styles.container}>
            <View style={styles.card}>
                <Text style={styles.kicker}>Sistema de Posgrado</Text>
                <Text style={styles.title}>Wizard de Ingresantes</Text>
                <Text style={styles.subtitle}>
                    Base Expo + React Native para la inscripción pública. Login y portal principal van aparte.
                </Text>

                <View style={styles.actions}>
                    <Link href="/wizard/inicio" asChild>
                        <Pressable style={styles.primaryButton}>
                            <Text style={styles.primaryButtonText}>Comenzar inscripción</Text>
                        </Pressable>
                    </Link>

                    {tokenTramite ? (
                        <Link href={`/tramite/${tokenTramite}`} asChild>
                            <Pressable style={styles.secondaryButton}>
                                <Text style={styles.secondaryButtonText}>Ver mi inscripción</Text>
                            </Pressable>
                        </Link>
                    ) : null}

                    <Link href="/login" asChild>
                        <Pressable style={styles.secondaryButton}>
                            <Text style={styles.secondaryButtonText}>Iniciar sesión (personal de posgrado)</Text>
                        </Pressable>
                    </Link>

                    <Pressable style={styles.secondaryButton} onPress={scheduleTestNotification}>
                        <Text style={styles.secondaryButtonText}>Probar notificación</Text>
                    </Pressable>
                </View>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
    },
    card: {
        width: "100%",
        maxWidth: 520,
        backgroundColor: "#fff",
        borderRadius: 24,
        padding: 24,
        gap: 12,
    },
    kicker: {
        fontSize: 13,
        color: "#2d7a65",
        fontWeight: "700",
        textTransform: "uppercase",
        letterSpacing: 0.8,
    },
    title: {
        fontSize: 32,
        fontWeight: "800",
        color: "#111827",
    },
    subtitle: {
        fontSize: 16,
        lineHeight: 24,
        color: "#4b5563",
    },
    actions: {
        marginTop: 8,
        gap: 12,
    },
    primaryButton: {
        backgroundColor: "#0d2035",
        paddingVertical: 14,
        borderRadius: 14,
        alignItems: "center",
    },
    primaryButtonText: {
        color: "#fff",
        fontSize: 16,
        fontWeight: "700",
    },
    secondaryButton: {
        backgroundColor: "#e8f3ef",
        paddingVertical: 14,
        borderRadius: 14,
        alignItems: "center",
    },
    secondaryButtonText: {
        color: "#1d6b59",
        fontSize: 16,
        fontWeight: "700",
    },
});