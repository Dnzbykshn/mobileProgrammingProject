import React, { useRef, useState } from 'react';
import {
  Pressable,
  StyleProp,
  Text,
  TextInput,
  TextInputProps,
  TouchableOpacity,
  View,
  ViewStyle,
} from 'react-native';
import { Eye, EyeOff, LucideIcon } from 'lucide-react-native';

import { colors, fonts, radius, shadows, spacing, typography } from '@/theme';

type AppInputProps = TextInputProps & {
  icon?: LucideIcon;
  label?: string;
  hint?: string;
  dark?: boolean;
  containerStyle?: StyleProp<ViewStyle>;
};

export default function AppInput({
  icon: Icon,
  label,
  hint,
  secureTextEntry,
  dark = true,
  containerStyle,
  editable,
  multiline,
  ...props
}: AppInputProps) {
  const inputRef = useRef<TextInput>(null);
  const [isFocused, setIsFocused] = useState(false);
  const [visible, setVisible] = useState(false);

  const isSecure = Boolean(secureTextEntry) && !visible;
  const isEditable = editable !== false;
  const isMultiline = Boolean(multiline);

  const labelColor = dark ? colors.text.secondary : colors.text.inkMuted;
  const inputBackground = dark ? colors.surface.nightSoft : colors.surface.paperRaised;
  const inputBorderColor = isFocused
    ? colors.border.gold
    : dark
      ? colors.border.soft
      : colors.border.paper;
  const textColor = dark ? colors.text.primary : colors.ink;
  const placeholderColor = dark ? colors.text.muted : colors.text.inkSoft;
  const iconColor = isFocused ? colors.gold : dark ? colors.text.secondary : colors.text.inkMuted;

  return (
    <View style={containerStyle}>
      {label ? (
        <Text
          style={{
            ...typography.labelLg,
            fontFamily: fonts.bodyMd,
            color: labelColor,
            marginBottom: spacing.sm,
          }}>
          {label}
        </Text>
      ) : null}

      <Pressable
        onPress={() => {
          if (isEditable) {
            inputRef.current?.focus();
          }
        }}
        style={{
          minHeight: 56,
          borderRadius: radius.lg,
          borderWidth: 1,
          borderColor: inputBorderColor,
          backgroundColor: inputBackground,
          paddingHorizontal: spacing.lg,
          flexDirection: 'row',
          alignItems: isMultiline ? 'flex-start' : 'center',
          ...(isFocused ? shadows.sm : null),
        }}>
        {Icon ? (
          <View
            style={{
              height: isMultiline ? 56 : undefined,
              alignItems: 'center',
              justifyContent: 'center',
            }}>
            <Icon size={18} color={iconColor} />
          </View>
        ) : null}

        <TextInput
          ref={inputRef}
          {...props}
          editable={isEditable}
          multiline={isMultiline}
          secureTextEntry={isSecure}
          placeholderTextColor={placeholderColor}
          selectionColor={colors.gold}
          cursorColor={colors.gold}
          keyboardAppearance={dark ? 'dark' : 'light'}
          underlineColorAndroid="transparent"
          textAlignVertical={isMultiline ? 'top' : 'center'}
          onFocus={(event) => {
            setIsFocused(true);
            props.onFocus?.(event);
          }}
          onBlur={(event) => {
            setIsFocused(false);
            props.onBlur?.(event);
          }}
          style={{
            flex: 1,
            minHeight: isMultiline ? 88 : undefined,
            ...typography.bodyLg,
            fontFamily: fonts.body,
            color: textColor,
            paddingVertical: isMultiline ? spacing.md : spacing.lg,
            marginLeft: Icon ? spacing.md : 0,
          }}
        />

        {Boolean(secureTextEntry) ? (
          <TouchableOpacity
            onPress={() => setVisible((current) => !current)}
            hitSlop={10}
            style={{
              height: isMultiline ? 56 : undefined,
              alignItems: 'center',
              justifyContent: 'center',
            }}>
            {visible ? <EyeOff size={18} color={iconColor} /> : <Eye size={18} color={iconColor} />}
          </TouchableOpacity>
        ) : null}
      </Pressable>

      {hint ? (
        <Text
          style={{
            ...typography.bodySm,
            color: labelColor,
            marginTop: spacing.sm,
          }}>
          {hint}
        </Text>
      ) : null}
    </View>
  );
}
