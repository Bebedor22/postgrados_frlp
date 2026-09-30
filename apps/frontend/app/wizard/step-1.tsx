import { useState } from "react";
import { Link } from "expo-router";
import { Pressable, StyleSheet, Text, TextInput, View, useWindowDimensions } from "react-native";
import { WizardShell, wizardStyles } from "../../src/components/wizard/WizardShell";

export default function Step1Screen() {
  const { width } = useWindowDimensions();
  const isCompact = width < 860;
  const halfOrFull = isCompact ? wizardStyles.fullField : wizardStyles.halfField;

  // Estado para controlar si el checkbox está marcado o no
  const [poseeDiscapacidad, setPoseeDiscapacidad] = useState(false);

  return (
    <WizardShell
      currentStep={1}
      title="Datos Personales"
      subtitle="Completá la información básica del aspirante."
      footer={
        <Link href="/wizard/step-2" asChild>
          <Pressable style={wizardStyles.primaryButton}>
            <Text style={wizardStyles.primaryButtonText}>Siguiente ›</Text>
          </Pressable>
        </Link>
      }
    >
      <View style={wizardStyles.twoColumns}>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Nombre(s)</Text>
          <TextInput placeholder="Juan" placeholderTextColor="#9ca3af" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Apellido(s)</Text>
          <TextInput placeholder="Pérez" placeholderTextColor="#9ca3af" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>DNI</Text>
          <TextInput placeholder="12.345.678" placeholderTextColor="#9ca3af" keyboardType="numeric" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Nacionalidad</Text>
          <TextInput placeholder="Argentina" placeholderTextColor="#9ca3af" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Fecha de Nacimiento</Text>
          <TextInput placeholder="DD/MM/AAAA" placeholderTextColor="#9ca3af" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Género</Text>
          <TextInput placeholder="Seleccionar" placeholderTextColor="#9ca3af" style={wizardStyles.input} />
        </View>
      </View>
      
      {/* Checkbox interactivo */}
      <Pressable 
        style={wizardStyles.radioItem} 
        onPress={() => setPoseeDiscapacidad(!poseeDiscapacidad)}
      >
        <View style={[
          wizardStyles.checkbox,
          // Si está marcado, le aplicamos el color de fondo y centramos el contenido
          poseeDiscapacidad && { 
            backgroundColor: '#0d2035', 
            borderColor: '#0d2035',
            justifyContent: 'center',
            alignItems: 'center'
          }
        ]}>
          {poseeDiscapacidad && <Text style={{ color: 'white', fontSize: 12, fontWeight: 'bold' }}>✓</Text>}
        </View>
        <Text style={wizardStyles.checkboxLabel}>¿Posee discapacidad?</Text>
      </Pressable>
      
    </WizardShell>
  );
}

const styles = StyleSheet.create({});
