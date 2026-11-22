/** Indicador visual del semáforo (Módulo C). El color siempre viene de la API. */
import {Text, View} from "react-native";

export const COLOR_SEMAFORO: Record<string, string> = {
    VERDE: "#16a34a",
    AMARILLO: "#f59e0b",
    ROJO: "#dc2626",
};

const FONDO: Record<string, string> = {
    VERDE: "#ecfdf5",
    AMARILLO: "#fffbeb",
    ROJO: "#fef2f2",
};

export function SemaforoBadge({color}: {color: string}) {
    return (
        <View style={{
            backgroundColor: FONDO[color] ?? "#f3f4f6", borderRadius: 999,
            paddingHorizontal: 10, paddingVertical: 4, alignSelf: "flex-start",
            flexDirection: "row", alignItems: "center", gap: 6,
        }}>
            <View style={{
                width: 9, height: 9, borderRadius: 5, backgroundColor: COLOR_SEMAFORO[color] ?? "#9ca3af",
            }}/>
            <Text style={{color: COLOR_SEMAFORO[color] ?? "#374151", fontSize: 12, fontWeight: "700"}}>
                {color}
            </Text>
        </View>
    );
}
