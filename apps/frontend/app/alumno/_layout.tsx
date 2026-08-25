import {Slot} from "expo-router";
import {AppLayout} from "../../src/components/layout/AppLayout";
import {ALUMNO_NAV} from "../../src/config/navigation";

export default function AlumnoLayout() {
    return (
        <AppLayout portalTitle="Portal Estudiante" navItems={ALUMNO_NAV}>
            <Slot/>
        </AppLayout>
    );
}
