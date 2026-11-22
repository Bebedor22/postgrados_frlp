/**
 * Marco del portal CPR (Módulo C, BR-004): barra superior y encabezado.
 * Reutiliza la paleta del portal de conducción y las tarjetas/boletos compartidos.
 */
import {useRouter} from "expo-router";
import {type ReactNode, useEffect, useState} from "react";
import {Pressable, ScrollView, Text, View} from "react-native";
import type {Usuario} from "../../lib/api";
import {cerrarSesion, obtenerSesion} from "../../lib/sesion";

/** Devuelve el usuario CPR logueado; si no lo es, manda al login. */
export function useUsuarioCpr(): Usuario | null {
    const router = useRouter();
    const [usuario, setUsuario] = useState<Usuario | null>(null);
    useEffect(() => {
        const sesion = obtenerSesion();
        if (!sesion || sesion.usuario.rol !== "CPR") {
            router.replace("/login");
            return;
        }
        setUsuario(sesion.usuario);
    }, []);
    return usuario;
}

export function PortalCpr({usuario, titulo, accion, children}: {
    usuario: Usuario | null;
    titulo: string;
    accion?: ReactNode;
    children: ReactNode;
}) {
    const router = useRouter();
    function salir() {
        cerrarSesion();
        router.replace("/login");
    }

    return (
        <View style={{flex: 1, backgroundColor: "#f2f3f5"}}>
            <View style={{
                minHeight: 48, paddingHorizontal: 20, flexDirection: "row", alignItems: "center",
                justifyContent: "space-between", backgroundColor: "#1d6b59",
            }}>
                <Text style={{color: "#ffffff", fontSize: 14}}>🎓  Sistema de Gestión de Posgrado</Text>
                <View style={{flexDirection: "row", alignItems: "center", gap: 18}}>
                    {usuario ? (
                        <Text style={{color: "rgba(255,255,255,0.85)", fontSize: 13}}>
                            {usuario.nombre} · Comisión de Posgrado Regional
                        </Text>
                    ) : null}
                    <Pressable onPress={salir}>
                        <Text style={{color: "#ffffff", fontSize: 13}}>Cerrar sesión</Text>
                    </Pressable>
                </View>
            </View>

            <View style={{flex: 1, flexDirection: "row"}}>
                <View style={{width: 240, backgroundColor: "#0d2035", paddingBottom: 16}}>
                    <Text style={{
                        color: "#ffffff", fontSize: 15, fontWeight: "600", paddingHorizontal: 16,
                        paddingVertical: 15, borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.08)",
                    }}>
                        Portal CPR
                    </Text>
                    <Text style={{
                        color: "rgba(255,255,255,0.4)", fontSize: 10, fontWeight: "600", letterSpacing: 1,
                        paddingHorizontal: 16, paddingTop: 16, paddingBottom: 6,
                    }}>
                        GESTIÓN ACADÉMICA
                    </Text>
                    <Pressable
                        onPress={() => router.push("/cpr")}
                        style={{marginHorizontal: 8, paddingHorizontal: 10, paddingVertical: 9, borderRadius: 6,
                            backgroundColor: "#1a4b78"}}
                    >
                        <Text style={{color: "#ffffff", fontSize: 13}}>📄  Gestión de Tesis</Text>
                    </Pressable>
                </View>

                <View style={{flex: 1}}>
                    <View style={{
                        backgroundColor: "#2d7a65", paddingHorizontal: 24, paddingVertical: 12,
                        minHeight: 50, flexDirection: "row", alignItems: "center",
                        justifyContent: "space-between", gap: 12,
                    }}>
                        <Text style={{color: "#ffffff", fontSize: 15, fontWeight: "600"}}>{titulo}</Text>
                        {accion}
                    </View>
                    <ScrollView contentContainerStyle={{padding: 24, gap: 16, maxWidth: 1000, width: "100%"}}>
                        {children}
                    </ScrollView>
                </View>
            </View>
        </View>
    );
}
