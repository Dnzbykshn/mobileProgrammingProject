import React, { useRef, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Eye, EyeOff, LockKeyhole, Mail } from 'lucide-react-native';
import Svg, { Circle, Defs, G, Path, RadialGradient, Stop } from 'react-native-svg';

import { useAuth } from '@/contexts/AuthContext';
import { colors, fonts, radius, shadows, spacing } from '@/theme';

// ─── Emblem ───────────────────────────────────────────────────────────────────

function MosquiEmblem() {
  return (
    <Svg width={72} height={72} viewBox="0 0 72 72">
      <Defs>
        <RadialGradient id="lgEmb" cx="50%" cy="50%" r="50%">
          <Stop offset="0%" stopColor={colors.gold} stopOpacity={0.22} />
          <Stop offset="100%" stopColor={colors.gold} stopOpacity={0} />
        </RadialGradient>
      </Defs>
      <Circle cx={36} cy={36} r={36} fill="url(#lgEmb)" />
      <G stroke={colors.gold} strokeWidth={1.1} fill="none" strokeOpacity={0.9}>
        <Path d="M36 10 L40.24 27.76 L58 36 L40.24 44.24 L36 62 L31.76 44.24 L14 36 L31.76 27.76 Z" />
        <Path d="M36 20 L52 36 L36 52 L20 36 Z" strokeOpacity={0.45} />
        <Path d="M36 10 L36 20 M58 36 L52 36 M36 62 L36 52 M14 36 L20 36" strokeOpacity={0.35} />
        <Circle cx={36} cy={36} r={3.5} fill={colors.gold} fillOpacity={0.7} strokeWidth={0} />
      </G>
    </Svg>
  );
}

// ─── Field ────────────────────────────────────────────────────────────────────

type FieldProps = {
  label: string;
  icon: React.ElementType;
  value: string;
  onChangeText: (v: string) => void;
  error?: string;
  secure?: boolean;
  inputRef?: React.RefObject<TextInput | null>;
  nextRef?: React.RefObject<TextInput | null>;
  returnKeyType?: 'next' | 'done';
  onSubmit?: () => void;
  placeholder: string;
  keyboardType?: 'default' | 'email-address';
  autoCapitalize?: 'none' | 'words' | 'sentences';
  textContentType?: string;
  autoComplete?: string;
};

function Field({
  label,
  icon: Icon,
  value,
  onChangeText,
  error,
  secure,
  inputRef,
  nextRef,
  returnKeyType = 'next',
  onSubmit,
  placeholder,
  keyboardType = 'default',
  autoCapitalize = 'none',
  textContentType,
  autoComplete,
}: FieldProps) {
  const [focused, setFocused] = useState(false);
  const [shown, setShown] = useState(false);

  const borderColor = error ? colors.status.error : focused ? colors.gold : colors.border.soft;

  return (
    <View style={styles.fieldWrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={[styles.fieldRow, { borderColor }]}>
        <Icon size={17} color={focused ? colors.gold : colors.text.muted} style={styles.fieldIcon} />
        <TextInput
          ref={inputRef}
          style={styles.fieldInput}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={colors.text.muted}
          selectionColor={colors.gold}
          cursorColor={colors.gold}
          secureTextEntry={secure && !shown}
          returnKeyType={returnKeyType}
          keyboardType={keyboardType}
          autoCapitalize={autoCapitalize}
          textContentType={textContentType as never}
          autoComplete={autoComplete as never}
          autoCorrect={false}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onSubmitEditing={() => {
            if (nextRef?.current) nextRef.current.focus();
            else onSubmit?.();
          }}
          blurOnSubmit={!nextRef}
        />
        {secure ? (
          <Pressable onPress={() => setShown((s) => !s)} hitSlop={12} style={styles.eyeBtn}>
            {shown ? (
              <EyeOff size={17} color={colors.text.muted} />
            ) : (
              <Eye size={17} color={colors.text.muted} />
            )}
          </Pressable>
        ) : null}
      </View>
      {error ? <Text style={styles.fieldError}>{error}</Text> : null}
    </View>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function LoginScreen() {
  const router = useRouter();
  const { login } = useAuth();
  const insets = useSafeAreaInsets();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [submitting, setSubmitting] = useState(false);
  const [globalError, setGlobalError] = useState('');

  const passwordRef = useRef<TextInput>(null);

  function validate() {
    const next: typeof errors = {};
    if (!email.trim()) next.email = 'E-posta gerekli.';
    else if (!/\S+@\S+\.\S+/.test(email)) next.email = 'Geçerli bir e-posta gir.';
    if (!password) next.password = 'Şifre gerekli.';
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleLogin() {
    setGlobalError('');
    if (!validate()) return;
    try {
      setSubmitting(true);
      await login(email.trim().toLowerCase(), password);
      router.replace('/(tabs)');
    } catch (err) {
      const msg =
        err && typeof err === 'object' && 'message' in err
          ? String((err as { message: string }).message)
          : 'E-posta veya şifre hatalı.';
      setGlobalError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <View style={styles.root}>
      <StatusBar style="light" />

      <LinearGradient
        colors={['#2A1F0A', '#1A1512', '#1A1512']}
        locations={[0, 0.45, 1]}
        style={StyleSheet.absoluteFill}
      />
      <View style={styles.topGlow} />

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={[
            styles.scroll,
            { paddingTop: insets.top + spacing.xxl, paddingBottom: insets.bottom + spacing.xxl },
          ]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="always">
          <View style={styles.brand}>
            <MosquiEmblem />
            <Text style={styles.brandName}>Kuran</Text>
            <Text style={styles.brandSub}>بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ</Text>
          </View>

          <View style={styles.heading}>
            <Text style={styles.headingTitle}>Hoş geldin</Text>
            <Text style={styles.headingSubtitle}>Hesabına sakin bir adımla geri dön.</Text>
          </View>

          <View style={styles.card}>
            <Field
              label="E-posta"
              icon={Mail}
              value={email}
              onChangeText={(v) => {
                setEmail(v);
                if (errors.email) setErrors((e) => ({ ...e, email: undefined }));
                setGlobalError('');
              }}
              error={errors.email}
              placeholder="ornek@mail.com"
              keyboardType="email-address"
              textContentType="emailAddress"
              autoComplete="email"
              nextRef={passwordRef}
              returnKeyType="next"
            />

            <Field
              label="Şifre"
              icon={LockKeyhole}
              value={password}
              onChangeText={(v) => {
                setPassword(v);
                if (errors.password) setErrors((e) => ({ ...e, password: undefined }));
                setGlobalError('');
              }}
              error={errors.password}
              placeholder="••••••••"
              secure
              inputRef={passwordRef}
              textContentType="password"
              autoComplete="password"
              returnKeyType="done"
              onSubmit={() => void handleLogin()}
            />

            {globalError ? <Text style={styles.globalError}>{globalError}</Text> : null}

            <Pressable
              onPress={() => void handleLogin()}
              disabled={submitting}
              style={({ pressed }) => [styles.btn, { opacity: submitting || pressed ? 0.82 : 1 }]}>
              {submitting ? (
                <ActivityIndicator color={colors.text.onGold} />
              ) : (
                <Text style={styles.btnLabel}>Giriş yap</Text>
              )}
            </Pressable>
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>Hesabın yok mu?</Text>
            <Pressable onPress={() => router.replace('/auth/register')} hitSlop={8}>
              <Text style={styles.footerLink}>Kayıt ol</Text>
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.night },
  topGlow: {
    position: 'absolute',
    top: -80,
    alignSelf: 'center',
    width: 340,
    height: 340,
    borderRadius: 170,
    backgroundColor: colors.goldDeep,
    opacity: 0.09,
  },
  scroll: { flexGrow: 1, paddingHorizontal: spacing.xl },

  brand: { alignItems: 'center', marginBottom: spacing.xxl },
  brandName: {
    fontFamily: fonts.heading,
    fontSize: 36,
    color: colors.text.primary,
    letterSpacing: 0.5,
    marginTop: spacing.md,
  },
  brandSub: {
    fontFamily: fonts.arabic,
    fontSize: 14,
    color: colors.text.gold,
    opacity: 0.7,
    marginTop: spacing.xs,
    letterSpacing: 1,
  },

  heading: { marginBottom: spacing.xl },
  headingTitle: {
    fontFamily: fonts.heading,
    fontSize: 28,
    color: colors.text.primary,
    marginBottom: spacing.xs,
  },
  headingSubtitle: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.text.secondary,
    lineHeight: 22,
  },

  card: {
    backgroundColor: colors.surface.raised,
    borderRadius: radius.xxl,
    borderWidth: 1,
    borderColor: colors.border.soft,
    padding: spacing.xl,
    gap: spacing.lg,
    ...shadows.lg,
  },

  fieldWrap: { gap: spacing.sm },
  fieldLabel: {
    fontFamily: fonts.bodyMd,
    fontSize: 11,
    color: colors.text.secondary,
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
  fieldRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface.nightSoft,
    borderRadius: radius.lg,
    borderWidth: 1,
    minHeight: 52,
    paddingHorizontal: spacing.lg,
  },
  fieldIcon: { marginRight: spacing.md },
  fieldInput: {
    flex: 1,
    fontFamily: fonts.body,
    fontSize: 15,
    color: colors.text.primary,
    paddingVertical: spacing.md,
  },
  eyeBtn: { padding: spacing.xs },
  fieldError: { fontFamily: fonts.body, fontSize: 12, color: colors.status.error },

  globalError: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.status.error,
    textAlign: 'center',
    backgroundColor: 'rgba(192,57,43,0.10)',
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },

  btn: {
    backgroundColor: colors.gold,
    borderRadius: radius.xl,
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.xs,
    ...shadows.gold,
  },
  btnLabel: {
    fontFamily: fonts.bodyMd,
    fontSize: 15,
    color: colors.text.onGold,
    letterSpacing: 0.2,
  },

  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.xl,
  },
  footerText: { fontFamily: fonts.body, fontSize: 14, color: colors.text.secondary },
  footerLink: { fontFamily: fonts.bodyMd, fontSize: 14, color: colors.gold },
});
