import { Link } from "expo-router";
import { Pressable, Text, TextInput, View, useWindowDimensions } from "react-native";
import { WizardShell, wizardStyles } from "../../src/components/wizard/WizardShell";

export default function Step2Screen() {
  const { width } = useWindowDimensions();
  const isCompact = width < 860;
  const halfOrFull = isCompact ? wizardStyles.fullField : wizardStyles.halfField;

  return (
    <WizardShell
      currentStep={2}
      title="Contacto y Residencia"
      subtitle="Completá los datos de contacto y domicilio."
      footer={
        <>
          <Link href="/wizard/step-1" asChild>
            <Pressable style={wizardStyles.secondaryButton}>
              <Text style={wizardStyles.secondaryButtonText}>‹ Anterior</Text>
            </Pressable>
          </Link>
          <Link href="/wizard/step-3" asChild>
            <Pressable style={wizardStyles.primaryButton}>
              <Text style={wizardStyles.primaryButtonText}>Siguiente ›</Text>
            </Pressable>
          </Link>
        </>
      }
    >
      <View style={wizardStyles.twoColumns}>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Teléfono celular</Text>
          <TextInput placeholder="+54 9 11 1234-5678" placeholderTextColor="#9ca3af" keyboardType="phone-pad" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Correo electrónico</Text>
          <TextInput placeholder="ejemplo@email.com" placeholderTextColor="#9ca3af" keyboardType="email-address" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Provincia</Text>
          <TextInput placeholder="Buenos Aires" placeholderTextColor="#9ca3af" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Localidad</Text>
          <TextInput placeholder="La Plata" placeholderTextColor="#9ca3af" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Calle</Text>
          <TextInput placeholder="Av. 7" placeholderTextColor="#9ca3af" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Número</Text>
          <TextInput placeholder="1234" placeholderTextColor="#9ca3af" keyboardType="numeric" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Piso / Depto (opcional)</Text>
          <TextInput placeholder="2° B" placeholderTextColor="#9ca3af" style={wizardStyles.input} />
        </View>
        <View style={halfOrFull}>
          <Text style={wizardStyles.label}>Código Postal</Text>
          <TextInput placeholder="1900" placeholderTextColor="#9ca3af" keyboardType="numeric" style={wizardStyles.input} />
        </View>
      </View>
    </WizardShell>
  );
}
