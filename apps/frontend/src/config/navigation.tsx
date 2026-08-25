import {Bell, BookOpen, ClipboardCheck, ClipboardList, DollarSign, FileText} from "lucide-react-native";
import type {ReactNode} from "react";

export interface NavItem {
    icon: ReactNode;
    label: string;
    to: string;
    group?: string;
}

export const ALUMNO_NAV: NavItem[] = [
    {icon: <BookOpen size={18} color="white"/>, label: "Mi Avance", to: "/alumno/miAvance"},
    {icon: <ClipboardCheck size={18} color="white"/>, label: "Estado de Trámite", to: "/alumno/estadoDeTramite"},
    {icon: <FileText size={18} color="white"/>, label: "Inscripción", to: "/alumno/inscripcion"},
];

export const DOCENTE_NAV: NavItem[] = [
    {
        icon: <BookOpen size={18} color="white"/>,
        label: "Mis Cursos",
        to: "/docente/misCursos",
        group: "Gestión Académica"
    },
    {
        icon: <ClipboardList size={18} color="white"/>,
        label: "Planilla de Carga",
        to: "/docente/planilla",
        group: "Gestión Académica"
    },
    {
        icon: <Bell size={18} color="white"/>,
        label: "Notificaciones",
        to: "/docente/notificaciones",
        group: "Gestión Académica"
    },
    {icon: <DollarSign size={18} color="white"/>, label: "Recibos de Sueldo", to: "/docente/recibos", group: "RRHH"},
];
