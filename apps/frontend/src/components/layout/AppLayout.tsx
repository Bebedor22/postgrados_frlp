import type {ReactNode} from "react";
import {Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View} from "react-native";
import {Link, usePathname, useRouter} from "expo-router";

export interface NavItem {
  icon: ReactNode;
  label: string;
  to: string;
  group?: string;
}

interface AppLayoutProps {
  portalTitle: string;
  navItems: NavItem[];
  children: ReactNode;
}

const NAV_BG = "#0d2035";
const HEADER_BG = "#1d6b59";
const ACTIVE_BG = "#1a4b78";

export function AppLayout({ portalTitle, navItems, children }: AppLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { width } = useWindowDimensions();
  const isCompact = width < 760;

  const groups = navItems.reduce<Record<string, NavItem[]>>((acc, item) => {
    const key = item.group ?? "_default";
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {});
  const groupOrder = Array.from(new Set(navItems.map((i) => i.group ?? "_default")));

  const handleLogout = () => {
    router.replace("/");
  };

  return (
    <View style={styles.page}>
      <View style={styles.header}>
        <View style={styles.brand}>
          <Text style={styles.brandIcon}>🎓</Text>
          <Text style={styles.headerTitle}>Sistema de Gestión de Posgrado</Text>
        </View>
        <View style={styles.headerActions}>
          <Text style={styles.bellIcon}>🔔</Text>
          <Pressable onPress={handleLogout} hitSlop={8}>
            <Text style={styles.logoutText}>Cerrar sesión</Text>
          </Pressable>
        </View>
      </View>

      <View style={styles.body}>
        {!isCompact && (
          <ScrollView style={styles.sidebar} contentContainerStyle={styles.sidebarContent}>
            <Text style={styles.portalTitle}>{portalTitle}</Text>

            {groupOrder.map((groupKey) => (
              <View key={groupKey}>
                {groupKey !== "_default" && <Text style={styles.groupLabel}>{groupKey}</Text>}
                {(groups[groupKey] ?? []).map((item) => {
                  const isActive = pathname === item.to;
                  return (
                      <Link key={`${groupKey}-${item.label}-${item.to}`} href={item.to} asChild>
                      <Pressable
                        style={({ pressed }) => [
                          styles.navItem,
                          isActive && styles.navItemActive,
                          pressed && styles.navItemPressed,
                        ]}
                      >
                        {typeof item.icon === "string" ? (
                            <Text style={styles.navIcon}>{item.icon}</Text>
                        ) : (
                            <View style={styles.navIcon}>{item.icon}</View>
                        )}
                        <Text style={styles.navLabel}>{item.label}</Text>
                      </Pressable>
                    </Link>
                  );
                })}
              </View>
            ))}
          </ScrollView>
        )}

        <View style={[styles.main, isCompact && styles.mainCompact]}>{children}</View>
      </View>
    </View>
  );
}

export function PageHeader({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <View style={pageHeaderStyles.bar}>
      <Text style={pageHeaderStyles.title}>{title}</Text>
      {action ? <View>{action}</View> : null}
    </View>
  );
}

const pageHeaderStyles = StyleSheet.create({
  bar: {
    backgroundColor: "#2d7a65",
    paddingHorizontal: 24,
    paddingVertical: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "600",
  },
});

const styles = StyleSheet.create({
  page: {
    flex: 1,
    backgroundColor: "#f2f3f5",
  },
  header: {
    height: 48,
    paddingHorizontal: 20,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: HEADER_BG,
  },
  brand: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  brandIcon: {
    fontSize: 16,
  },
  headerTitle: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "500",
  },
  headerActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 18,
  },
  bellIcon: {
    fontSize: 15,
  },
  logoutText: {
    color: "#ffffff",
    fontSize: 13,
  },
  body: {
    flex: 1,
    flexDirection: "row",
  },
  sidebar: {
    flex: 1,
    backgroundColor: NAV_BG,
  },
  sidebarContent: {
    paddingBottom: 24,
  },
  portalTitle: {
    padding: 16,
    paddingBottom: 14,
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "600",
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255,255,255,0.08)",
  },
  groupLabel: {
    paddingTop: 12,
    paddingHorizontal: 16,
    paddingBottom: 4,
    color: "rgba(255,255,255,0.4)",
    fontSize: 10,
    fontWeight: "600",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  navItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginHorizontal: 8,
    marginVertical: 1,
    paddingHorizontal: 10,
    paddingVertical: 9,
    borderRadius: 6,
  },
  navItemActive: {
    backgroundColor: ACTIVE_BG,
  },
  navItemPressed: {
    backgroundColor: ACTIVE_BG,
  },
  navIcon: {
    width: 18,
    alignItems: "center",
  },
  navLabel: {
    color: "#ffffff",
    fontSize: 13,
  },
  main: {
    flex: 4,
    backgroundColor: "#f2f3f5",
  },
  mainCompact: {
    paddingTop: 12,
  },
});
