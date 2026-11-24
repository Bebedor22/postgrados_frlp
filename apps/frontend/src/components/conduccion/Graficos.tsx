/**
 * Gráficos simples hechos con View (sin librerías externas): funcionan igual en web y en el celular.
 */
import {Text, View} from "react-native";

export interface Barra {
    etiqueta: string;
    valor: number;
    /** Texto que se muestra junto a la barra (por defecto, el valor). */
    texto?: string;
    color?: string;
}

/** Barras horizontales: una fila por categoría (por ejemplo, legajos por estado). */
export function BarrasHorizontales({datos, maximo, color = "#1d6b59"}: {
    datos: Barra[];
    maximo?: number;
    color?: string;
}) {
    const tope = maximo ?? Math.max(1, ...datos.map((d) => d.valor));
    return (
        <View style={{gap: 8}}>
            {datos.map((d) => (
                <View key={d.etiqueta} style={{flexDirection: "row", alignItems: "center", gap: 10}}>
                    <Text style={{width: 110, fontSize: 12, color: "#374151"}} numberOfLines={1}>{d.etiqueta}</Text>
                    <View style={{flex: 1, height: 14, backgroundColor: "#f3f4f6", borderRadius: 4, overflow: "hidden"}}>
                        <View style={{
                            width: `${Math.min(100, (d.valor / tope) * 100)}%`, height: "100%",
                            backgroundColor: d.color ?? color,
                        }}/>
                    </View>
                    <Text style={{width: 54, fontSize: 12, fontWeight: "600", color: "#111827", textAlign: "right"}}>
                        {d.texto ?? String(d.valor)}
                    </Text>
                </View>
            ))}
        </View>
    );
}

/** Barras verticales para comparar cohortes entre sí. */
export function BarrasVerticales({datos, maximo, color = "#1d6b59", alto = 150}: {
    datos: Barra[];
    maximo?: number;
    color?: string;
    alto?: number;
}) {
    const tope = maximo ?? Math.max(1, ...datos.map((d) => d.valor));
    return (
        <View style={{flexDirection: "row", alignItems: "flex-end", gap: 16, height: alto + 44}}>
            {datos.map((d) => (
                <View key={d.etiqueta} style={{flex: 1, maxWidth: 110, alignItems: "center", justifyContent: "flex-end"}}>
                    <Text style={{fontSize: 12, fontWeight: "700", color: "#111827", marginBottom: 4}}>
                        {d.texto ?? String(d.valor)}
                    </Text>
                    <View style={{
                        width: "70%", height: Math.max(2, (d.valor / tope) * alto),
                        backgroundColor: d.color ?? color, borderTopLeftRadius: 4, borderTopRightRadius: 4,
                    }}/>
                    <Text style={{fontSize: 11, color: "#6b7280", marginTop: 6, textAlign: "center"}} numberOfLines={1}>
                        {d.etiqueta}
                    </Text>
                </View>
            ))}
        </View>
    );
}
