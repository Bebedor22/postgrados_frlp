/**
 * Marco del portal de conducción: barra superior, menú lateral y encabezado.
 * Imita los colores del portal docente existente (marco.tsx), pero con
 * componentes de React Native, así funciona en web y en el celular.
 */
import {usePathname, useRouter} from "expo-router";
import {type ReactNode, useEffect, useState} from "react";
import {Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions} from "react-native";
import type {Usuario} from "../../lib/api";
import {cerrarSesion, obtenerSesion} from "../../lib/sesion";

export const ROLES_CONDUCCION = ["COORDINADOR", "DIRECCION"];

const MENU = [
    {texto: "Inscriptos y legajos", ruta: "/conduccion", icono: "📋"},
];

/** Devuelve el usuario logueado; si no hay sesión o no tiene un rol de conducción, manda al login. */
export function useUsuarioConduccion(): Usuario | null {
    const router = useRouter();
    const [usuario, setUsuario] = useState<Usuario | null>(null);
    useEffect(() => {
        const sesion = obtenerSesion();
        if (!sesion || !ROLES_CONDUCCION.includes(sesion.usuario.rol)) {
            router.replace("/login");
            return;
        }
        setUsuario(sesion.usuario);
    }, []);
    return usuario;
}

export function PortalConduccion({usuario, titulo, accion, children}: {
    usuario: Usuario | null;
    titulo: string;
    accion?: ReactNode;
    children: ReactNode;
}) {
    const router = useRouter();
    const ruta = usePathname();
    const {width} = useWindowDimensions();
    const compacto = width < 860;

    function salir() {
        cerrarSesion();
        router.replace("/login");
    }

    return (
        <View style={estilos.pagina}>
            <View style={estilos.barra}>
                <Text style={estilos.barraTitulo}>🎓  Sistema de Gestión de Posgrado</Text>
                <View style={estilos.barraDerecha}>
                    {usuario && !compacto ? (
                        <Text style={estilos.barraUsuario}>
                            {usuario.nombre} · {usuario.rol === "DIRECCION" ? "Dirección de Posgrado" : "Coordinación"}
                        </Text>
                    ) : null}
                    <Pressable onPress={salir}>
                        <Text style={estilos.barraAccion}>Cerrar sesión</Text>
                    </Pressable>
                </View>
            </View>

            <View style={[estilos.cuerpo, compacto && {flexDirection: "column"}]}>
                {!compacto ? (
                    <View style={estilos.menu}>
                        <Text style={estilos.menuTitulo}>Portal de Conducción</Text>
                        <Text style={estilos.menuGrupo}>GESTIÓN DE INSCRIPCIONES</Text>
                        {MENU.map((item) => {
                            const activo = ruta === item.ruta || (item.ruta !== "/" && ruta.startsWith(`${item.ruta}/`));
                            return (
                                <Pressable
                                    key={item.ruta}
                                    style={[estilos.menuItem, activo && estilos.menuItemActivo]}
                                    onPress={() => router.push(item.ruta as never)}
                                >
                                    <Text style={estilos.menuTexto}>{item.icono}  {item.texto}</Text>
                                </Pressable>
                            );
                        })}
                    </View>
                ) : null}

                <View style={{flex: 1}}>
                    <View style={estilos.encabezado}>
                        <Text style={estilos.encabezadoTitulo}>{titulo}</Text>
                        {accion}
                    </View>
                    <ScrollView contentContainerStyle={[estilos.contenido, compacto && {padding: 12}]}>
                        {children}
                    </ScrollView>
                </View>
            </View>
        </View>
    );
}

/** Tarjeta blanca de contenido. */
export function Tarjeta({titulo, children, estilo}: {titulo?: string; children: ReactNode; estilo?: object}) {
    return (
        <View style={[estilos.tarjeta, estilo]}>
            {titulo ? <Text style={estilos.tarjetaTitulo}>{titulo}</Text> : null}
            {children}
        </View>
    );
}

/** Etiqueta de color para el estado de un legajo. */
export function InsigniaEstado({texto, color, fondo}: {texto: string; color: string; fondo: string}) {
    return (
        <View style={{backgroundColor: fondo, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 3, alignSelf: "flex-start"}}>
            <Text style={{color, fontSize: 12, fontWeight: "600"}}>{texto}</Text>
        </View>
    );
}

/** Botón chico del portal. */
export function Boton({texto, alPresionar, tipo = "principal", deshabilitado}: {
    texto: string;
    alPresionar: () => void;
    tipo?: "principal" | "secundario" | "peligro" | "exito";
    deshabilitado?: boolean;
}) {
    const colores = {
        principal: {fondo: "#0d2035", texto: "#ffffff", borde: "#0d2035"},
        secundario: {fondo: "#ffffff", texto: "#374151", borde: "#d1d5db"},
        peligro: {fondo: "#ffffff", texto: "#dc2626", borde: "#fca5a5"},
        exito: {fondo: "#2d7a65", texto: "#ffffff", borde: "#2d7a65"},
    }[tipo];
    return (
        <Pressable
            onPress={alPresionar}
            disabled={deshabilitado}
            style={{
                backgroundColor: colores.fondo,
                borderColor: colores.borde,
                borderWidth: 1,
                borderRadius: 6,
                paddingHorizontal: 16,
                paddingVertical: 9,
                opacity: deshabilitado ? 0.5 : 1,
            }}
        >
            <Text style={{color: colores.texto, fontSize: 13, fontWeight: "600"}}>{texto}</Text>
        </Pressable>
    );
}

const estilos = StyleSheet.create({
    pagina: {flex: 1, backgroundColor: "#f2f3f5"},
    barra: {
        minHeight: 48,
        paddingHorizontal: 20,
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        backgroundColor: "#1d6b59",
    },
    barraTitulo: {color: "#ffffff", fontSize: 14, fontWeight: "500"},
    barraDerecha: {flexDirection: "row", alignItems: "center", gap: 18},
    barraUsuario: {color: "rgba(255,255,255,0.85)", fontSize: 13},
    barraAccion: {color: "#ffffff", fontSize: 13},
    cuerpo: {flex: 1, flexDirection: "row"},
    menu: {width: 240, backgroundColor: "#0d2035", paddingBottom: 16},
    menuTitulo: {
        color: "#ffffff",
        fontSize: 15,
        fontWeight: "600",
        paddingHorizontal: 16,
        paddingVertical: 15,
        borderBottomWidth: 1,
        borderBottomColor: "rgba(255,255,255,0.08)",
    },
    menuGrupo: {
        color: "rgba(255,255,255,0.4)",
        fontSize: 10,
        fontWeight: "600",
        letterSpacing: 1,
        paddingHorizontal: 16,
        paddingTop: 16,
        paddingBottom: 6,
    },
    menuItem: {marginHorizontal: 8, paddingHorizontal: 10, paddingVertical: 9, borderRadius: 6},
    menuItemActivo: {backgroundColor: "#1a4b78"},
    menuTexto: {color: "#ffffff", fontSize: 13},
    encabezado: {
        backgroundColor: "#2d7a65",
        paddingHorizontal: 24,
        paddingVertical: 12,
        minHeight: 50,
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
    },
    encabezadoTitulo: {color: "#ffffff", fontSize: 15, fontWeight: "600"},
    contenido: {padding: 24, gap: 16, maxWidth: 1100, width: "100%"},
    tarjeta: {backgroundColor: "#ffffff", borderWidth: 1, borderColor: "#e5e7eb", borderRadius: 8, padding: 20},
    tarjetaTitulo: {
        fontSize: 12,
        fontWeight: "700",
        color: "#374151",
        textTransform: "uppercase",
        letterSpacing: 0.6,
        marginBottom: 12,
    },
});