import { Text, TextProps } from 'react-native';
import { typography, colors } from '@/theme';

type HeadingSize = 'xl' | 'lg' | 'md' | 'sm';
type BodySize = 'lg' | 'md' | 'sm';
type CaptionSize = 'md' | 'sm';

interface HeadingProps extends TextProps {
  size?: HeadingSize;
  color?: string;
}

interface BodyProps extends TextProps {
  size?: BodySize;
  color?: string;
}

interface CaptionProps extends TextProps {
  size?: CaptionSize;
  color?: string;
}

export function Heading({
  size = 'md',
  color = colors.text.primary,
  style,
  ...props
}: HeadingProps) {
  return (
    <Text
      style={[
        typography.heading[size],
        { color },
        style
      ]}
      {...props}
    />
  );
}

export function Body({
  size = 'md',
  color = colors.text.primary,
  style,
  ...props
}: BodyProps) {
  return (
    <Text
      style={[
        typography.body[size],
        { color },
        style
      ]}
      {...props}
    />
  );
}

export function Caption({
  size = 'md',
  color = colors.text.secondary,
  style,
  ...props
}: CaptionProps) {
  return (
    <Text
      style={[
        typography.caption[size],
        { color },
        style
      ]}
      {...props}
    />
  );
}
