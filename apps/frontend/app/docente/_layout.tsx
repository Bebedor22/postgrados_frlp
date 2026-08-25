import {Slot} from "expo-router";
import {AppLayout} from "../../src/components/layout/AppLayout";
import {DOCENTE_NAV} from "../../src/config/navigation";

export default function DocenteLayout() {
    return (
        <AppLayout portalTitle="Portal Docente" navItems={DOCENTE_NAV}>
            <Slot/>
        </AppLayout>
    );
}
