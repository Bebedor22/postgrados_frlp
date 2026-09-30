import { useState } from "react";
import { Link } from "expo-router";
import { Pressable, Text, TextInput, View, useWindowDimensions } from "react-native";
import { WizardShell, wizardStyles } from "../../src/components/wizard/WizardShell";

export default function Step3Screen() {
  const { width } = useWindowDimensions();
  const isCompact = width < 860;
  const halfOrFull = isCompact ? wizardStyles.fullField : wizardStyles.halfField;

  // Estados para controlar qué opción está seleccionada (por defecto en 'false' = No)
  const [otroTitulo, setOtroTitulo] = useState(false);
  const [trabajaEnArea, setTrabajaEnArea] = useState(false);

  return (
    <WizardShell
      currentStep={3}
      title="Antecedentes y Motivaciones"
      subtitle="Información académica y razones para tu postulación."
      footer={
        <>
          <Link href="/wizard/step-2" asChild>
            <Pressable style={wizardStyles.secondaryButton}>
              <Text style={wizardStyles.secondaryButtonText}>‹ Anterior</Text>
            </Pressable>
          </Link>
          <Link href="/wizard/step-4" asChild>
            <Pressable style={wizardStyles.primaryButton}>
              <Text style={wizardStyles.primaryButtonText}>Siguiente ›</Text>
            </Pressable>
          </Link>
        </>
      }
    >
      <View style={wizardStyles.section}>
        <Text style={wizardStyles.sectionTitle}>Antecedentes académicos</Text>
        <View style={wizardStyles.twoColumns}>
          <View style={halfOrFull}>
            <Text style={wizardStyles.label}>Título de grado obtenido</Text>
            <TextInput placeholder="Lic. en Sociología" placeholderTextColor="#9ca3af" style={wizardStyles.input} />
          </View>
          <View style={halfOrFull}>
            <Text style={wizardStyles.label}>Institución</Text>
            <TextInput placeholder="Universidad Nacional..." placeholderTextColor="#9ca3af" style={wizardStyles.input} />
          </View>
          <View style={halfOrFull}>
            <Text style={wizardStyles.label}>Año de graduación</Text>
            <TextInput placeholder="2019" placeholderTextColor="#9ca3af" keyboardType="numeric" style={wizardStyles.input} />
          </View>
          <View style={halfOrFull}>
            <Text style={wizardStyles.label}>Carrera a inscribirse</Text>
            <TextInput placeholder="Seleccionar maestría/doctorado" placeholderTextColor="#9ca3af" style={wizardStyles.input} />
          </View>
        </View>
        
        <Text style={wizardStyles.label}>¿Posee otro título de posgrado?</Text>
        <View style={wizardStyles.radioRow}>
          <Pressable style={wizardStyles.radioItem} onPress={() => setOtroTitulo(true)}>
            <View style={[wizardStyles.radioCircle, otroTitulo && wizardStyles.radioCircleSelected]}>
              {otroTitulo && <View style={wizardStyles.radioInner} />}
            </View>
            <Text style={wizardStyles.checkboxLabel}>Sí</Text>
          </Pressable>
          <Pressable style={wizardStyles.radioItem} onPress={() => setOtroTitulo(false)}>
            <View style={[wizardStyles.radioCircle, !otroTitulo && wizardStyles.radioCircleSelected]}>
              {!otroTitulo && <View style={wizardStyles.radioInner} />}
            </View>
            <Text style={wizardStyles.checkboxLabel}>No</Text>
          </Pressable>
        </View>
      </View>

      <View style={wizardStyles.section}>
        <Text style={wizardStyles.sectionTitle}>Motivaciones y perfil</Text>
        <View style={wizardStyles.fullField}>
          <Text style={wizardStyles.label}>¿Por qué desea realizar esta carrera? (máx. 500 caracteres)</Text>
          <TextInput 
            placeholder="Describa sus motivaciones..." 
            placeholderTextColor="#9ca3af"
            multiline 
            numberOfLines={4} 
            maxLength={500} 
            style={[wizardStyles.input, wizardStyles.textArea]} 
          />
        </View>

        <View style={{ marginTop: 20 }}>
          <Text style={wizardStyles.label}>¿Actualmente trabaja en el área de la carrera?</Text>
          <View style={wizardStyles.radioRow}>
            <Pressable style={wizardStyles.radioItem} onPress={() => setTrabajaEnArea(true)}>
              <View style={[wizardStyles.radioCircle, trabajaEnArea && wizardStyles.radioCircleSelected]}>
                {trabajaEnArea && <View style={wizardStyles.radioInner} />}
              </View>
              <Text style={wizardStyles.checkboxLabel}>Sí</Text>
            </Pressable>
            <Pressable style={wizardStyles.radioItem} onPress={() => setTrabajaEnArea(false)}>
              <View style={[wizardStyles.radioCircle, !trabajaEnArea && wizardStyles.radioCircleSelected]}>
                {!trabajaEnArea && <View style={wizardStyles.radioInner} />}
              </View>
              <Text style={wizardStyles.checkboxLabel}>No</Text>
            </Pressable>
          </View>
        </View>

        <View style={[wizardStyles.fullField, { marginTop: 20 }]}>
          <Text style={wizardStyles.label}>¿Cómo conoció la oferta académica?</Text>
          <TextInput placeholder="Seleccione una opción..." placeholderTextColor="#9ca3af" style={wizardStyles.input} />
        </View>
      </View>
    </WizardShell>
  );
}