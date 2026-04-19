import React from 'react';
import { TextInputProps } from 'react-native';
import { LucideIcon } from 'lucide-react-native';

import AppInput from '@/components/app/AppInput';

type AuthFieldProps = TextInputProps & {
  icon: LucideIcon;
  label?: string;
  hint?: string;
  dark?: boolean;
};

export default function AuthField({ icon, label, hint, dark = true, ...props }: AuthFieldProps) {
  return <AppInput icon={icon} label={label} hint={hint} dark={dark} {...props} />;
}
