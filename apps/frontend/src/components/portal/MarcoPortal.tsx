/**
 * Marco (barra superior + menú lateral) de los portales Docente y Alumno.
 *
 * Estas pantallas son del Módulo B y del portal del alumno: muestran datos de
 * ejemplo y todavía no están conectadas al backend. Están armadas con etiquetas
 * HTML (div, header, nav), así que funcionan en la versión web.
 *
 * Antes este marco estaba copiado en app/marco.tsx y app/docente/components/navLeft.tsx.
 * Expo Router trata cada archivo de app/ como una pantalla, así que esas copias
 * aparecían como rutas (/marco) y daban advertencias. Ahora vive en src/.
 */
import {usePathname, useRouter} from "expo-router";
import type {ReactNode} from "react";
import {cerrarSesion} from "../../lib/sesion";

export interface ItemMenu {
    icono: string;
    texto: string;
    ruta: string;
    grupo?: string;
    /** Sección que todavía no existe: se muestra en gris y no navega. */
    proximamente?: boolean;
}

const FONDO_MENU = "#0d2035";
const FONDO_BARRA = "#1d6b59";
const FONDO_ACTIVO = "#1a4b78";
const FUENTE = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";

export function MarcoPortal({titulo, items, children}: {titulo: string; items: ItemMenu[]; children: ReactNode}) {
    const router = useRouter();
    const rutaActual = usePathname();
    // Los ítems agrupados, respetando el orden en que aparecen
    const grupos = new Map<string, ItemMenu[]>();
    for (const item of items) {
        const grupo = item.grupo ?? "";
        grupos.set(grupo, [...(grupos.get(grupo) ?? []), item]);
    }

    function salir() {
        cerrarSesion();
        router.replace("/login");
    }

    return (
        // Misma tipografía que el resto de la app (las etiquetas HTML usan la del navegador por defecto)
        <div style={{display: "flex", flexDirection: "column", height: "100vh", fontFamily: FUENTE}}>
            <header style={{
                backgroundColor: FONDO_BARRA, height: "48px", display: "flex", alignItems: "center",
                justifyContent: "space-between", padding: "0 20px", flexShrink: 0,
            }}>
                <div style={{display: "flex", alignItems: "center", gap: "10px", color: "white"}}>
                    🎓
                    <span style={{fontSize: "14px", fontWeight: 500}}>Sistema de Gestión de Posgrado</span>
                </div>
                <button
                    onClick={salir}
                    style={{background: "none", border: "none", color: "white", cursor: "pointer", fontSize: "13px"}}
                >
                    Cerrar sesión
                </button>
            </header>

            <div style={{display: "flex", flex: 1, overflow: "hidden"}}>
                <aside style={{
                    backgroundColor: FONDO_MENU, width: "240px", flexShrink: 0,
                    display: "flex", flexDirection: "column", overflowY: "auto",
                }}>
                    <div style={{
                        padding: "16px 16px 14px", color: "white", fontSize: "15px", fontWeight: 600,
                        borderBottom: "1px solid rgba(255,255,255,0.08)",
                    }}>
                        {titulo}
                    </div>
                    <nav style={{paddingTop: "8px"}}>
                        {[...grupos.entries()].map(([grupo, itemsDelGrupo]) => (
                            <div key={grupo || "general"}>
                                {grupo ? (
                                    <div style={{
                                        padding: "12px 16px 4px", color: "rgba(255,255,255,0.4)", fontSize: "10px",
                                        fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase",
                                    }}>
                                        {grupo}
                                    </div>
                                ) : null}
                                {itemsDelGrupo.map((item) => {
                                    const activo = rutaActual === item.ruta;
                                    return (
                                        <a
                                            key={item.ruta}
                                            href={item.proximamente ? undefined : item.ruta}
                                            onClick={(e) => {
                                                e.preventDefault();
                                                if (!item.proximamente) router.push(item.ruta as never);
                                            }}
                                            title={item.proximamente ? "Próximamente" : undefined}
                                            style={{
                                                display: "flex", alignItems: "center", gap: "10px",
                                                margin: "1px 8px", padding: "9px 10px", borderRadius: "6px",
                                                backgroundColor: activo ? FONDO_ACTIVO : "transparent",
                                                color: item.proximamente ? "rgba(255,255,255,0.35)" : "white",
                                                cursor: item.proximamente ? "default" : "pointer",
                                                textDecoration: "none", fontSize: "13px",
                                            }}
                                        >
                                            <span>{item.icono}</span>
                                            {item.texto}
                                        </a>
                                    );
                                })}
                            </div>
                        ))}
                    </nav>
                </aside>

                <main style={{flex: 1, overflow: "auto", backgroundColor: "#f2f3f5"}}>{children}</main>
            </div>
        </div>
    );
}

/** Barra verde con el título de la pantalla (y un botón opcional a la derecha). */
export function EncabezadoPagina({titulo, accion}: {titulo: string; accion?: ReactNode}) {
    return (
        <div style={{
            backgroundColor: "#2d7a65", padding: "14px 24px", display: "flex",
            alignItems: "center", justifyContent: "space-between",
        }}>
            <h2 style={{color: "white", fontSize: "15px", fontWeight: 600, margin: 0}}>{titulo}</h2>
            {accion ? <div>{accion}</div> : null}
        </div>
    );
}

const MENU_DOCENTE: ItemMenu[] = [
    {icono: "🕮", texto: "Mis Cursos", ruta: "/docente/misCursos", grupo: "Gestión Académica"},
    {icono: "📋", texto: "Planilla de Carga", ruta: "/docente/planilla", grupo: "Gestión Académica"},
    {icono: "🔔", texto: "Notificaciones", ruta: "/docente/notificaciones", grupo: "Gestión Académica", proximamente: true},
    {icono: "$", texto: "Recibos de Sueldo", ruta: "/docente/recibos", grupo: "RRHH", proximamente: true},
];

const MENU_ALUMNO: ItemMenu[] = [
    {icono: "🕮", texto: "Mi Avance", ruta: "/alumno/miAvance", grupo: "Cursadas"},
    {icono: "📋", texto: "Estado de trámite", ruta: "/alumno/estadoDeTramite", grupo: "Gestión", proximamente: true},
    {icono: "📋", texto: "Inscripción", ruta: "/alumno/inscripcion", grupo: "Gestión", proximamente: true},
];

export const MarcoDocente = ({children}: {children: ReactNode}) => (
    <MarcoPortal titulo="Portal Docente" items={MENU_DOCENTE}>{children}</MarcoPortal>
);

export const MarcoAlumno = ({children}: {children: ReactNode}) => (
    <MarcoPortal titulo="Portal del Alumno" items={MENU_ALUMNO}>{children}</MarcoPortal>
);