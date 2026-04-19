/**
 * IslamicOrnaments — Dekoratif İslami görsel bileşenler
 * Mosqui Design System için özel SVG ve Arapça metin elementleri.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, {
  Circle,
  ClipPath,
  Defs,
  G,
  Line,
  Path,
  Polygon,
  Rect,
} from 'react-native-svg';

import { colors, fonts } from '@/theme';

// ─── Hilal + Yıldız ──────────────────────────────────────────────────────────

export function CrescentStar({
  size = 32,
  color = colors.gold,
  opacity = 0.85,
}: {
  size?: number;
  color?: string;
  opacity?: number;
}) {
  const s = size;
  return (
    <Svg width={s} height={s} viewBox="0 0 40 40" opacity={opacity}>
      <Defs>
        <ClipPath id="crescentClip">
          <Circle cx={18} cy={20} r={13} />
        </ClipPath>
      </Defs>
      {/* Hilal */}
      <Circle cx={18} cy={20} r={13} fill={color} />
      <Circle cx={23} cy={17} r={10.5} fill={colors.night} clipPath="url(#crescentClip)" />
      {/* 5 köşeli yıldız */}
      <Polygon
        points="33,14 34.5,19 39.5,19 35.5,22 37,27 33,24 29,27 30.5,22 26.5,19 31.5,19"
        fill={color}
      />
    </Svg>
  );
}

// ─── 8 Köşeli Geometrik Rozet ─────────────────────────────────────────────────

export function GeometricRosette({
  size = 40,
  color = colors.gold,
  opacity = 0.7,
}: {
  size?: number;
  color?: string;
  opacity?: number;
}) {
  const cx = 36;
  const cy = 36;
  const r1 = 22;
  const r2 = 12;
  const pts = 8;

  const starPath = Array.from({ length: pts * 2 }, (_, i) => {
    const angle = (Math.PI / pts) * i - Math.PI / 2;
    const r = i % 2 === 0 ? r1 : r2;
    const x = cx + Math.cos(angle) * r;
    const y = cy + Math.sin(angle) * r;
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(' ') + ' Z';

  const innerPath = Array.from({ length: pts * 2 }, (_, i) => {
    const angle = (Math.PI / pts) * i - Math.PI / 2;
    const r = i % 2 === 0 ? r1 * 0.55 : r2 * 0.55;
    const x = cx + Math.cos(angle) * r;
    const y = cy + Math.sin(angle) * r;
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(' ') + ' Z';

  return (
    <Svg width={size} height={size} viewBox="0 0 72 72" opacity={opacity}>
      <G stroke={color} strokeWidth={1} fill="none">
        <Path d={starPath} strokeOpacity={0.9} />
        <Path d={innerPath} strokeOpacity={0.5} />
        <Circle cx={cx} cy={cy} r={r2 * 0.42} stroke={color} strokeOpacity={0.7} />
        {/* 8 ışın çizgisi */}
        {Array.from({ length: pts }, (_, i) => {
          const angle = (Math.PI * 2 * i) / pts - Math.PI / 2;
          const x1 = cx + Math.cos(angle) * (r2 * 0.42);
          const y1 = cy + Math.sin(angle) * (r2 * 0.42);
          const x2 = cx + Math.cos(angle) * r1;
          const y2 = cy + Math.sin(angle) * r1;
          return (
            <Line
              key={i}
              x1={x1.toFixed(2)}
              y1={y1.toFixed(2)}
              x2={x2.toFixed(2)}
              y2={y2.toFixed(2)}
              strokeOpacity={0.3}
            />
          );
        })}
      </G>
      <Circle cx={cx} cy={cy} r={3.5} fill={color} fillOpacity={0.8} />
    </Svg>
  );
}

// ─── Cami Silüeti ─────────────────────────────────────────────────────────────

export function MosqueSilhouette({
  width = 160,
  height = 60,
  color = colors.gold,
  opacity = 0.08,
}: {
  width?: number;
  height?: number;
  color?: string;
  opacity?: number;
}) {
  // Merkezi kubbe + iki minare
  const w = 200;
  const h = 80;
  return (
    <Svg width={width} height={height} viewBox={`0 0 ${w} ${h}`} opacity={opacity}>
      <G fill={color}>
        {/* Sol minare */}
        <Rect x={18} y={20} width={10} height={55} />
        <Path d="M18 20 Q23 8 28 20 Z" />
        <Rect x={20} y={4} width={6} height={8} />
        <Path d="M20 4 Q23 0 26 4 Z" />

        {/* Sağ minare */}
        <Rect x={172} y={20} width={10} height={55} />
        <Path d="M172 20 Q177 8 182 20 Z" />
        <Rect x={174} y={4} width={6} height={8} />
        <Path d="M174 4 Q177 0 180 4 Z" />

        {/* Ana bina */}
        <Rect x={38} y={38} width={124} height={37} />

        {/* Merkezi büyük kubbe */}
        <Path d="M68 38 Q100 4 132 38 Z" />

        {/* Yan küçük kubbeler */}
        <Path d="M38 52 Q55 38 72 52 Z" />
        <Path d="M128 52 Q145 38 162 52 Z" />

        {/* Kapı */}
        <Path d="M90 75 L90 55 Q100 48 110 55 L110 75 Z" fill={colors.night} />
      </G>
    </Svg>
  );
}

// ─── Ornamental Divider ────────────────────────────────────────────────────────

export function IslamicDivider({
  color = colors.gold,
  opacity = 0.3,
}: {
  color?: string;
  opacity?: number;
}) {
  return (
    <View style={[styles.dividerWrap, { opacity }]}>
      <View style={[styles.dividerLine, { backgroundColor: color }]} />
      <Svg width={18} height={18} viewBox="0 0 36 36" style={styles.dividerStar}>
        {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => {
          const angle = (Math.PI / 4) * i - Math.PI / 2;
          const x = 18 + Math.cos(angle) * 12;
          const y = 18 + Math.sin(angle) * 12;
          const ix = 18 + Math.cos(angle + Math.PI / 8) * 6;
          const iy = 18 + Math.sin(angle + Math.PI / 8) * 6;
          return null; // rendered via path below
        })}
        <Path
          d={(() => {
            const pts = 8;
            return (
              Array.from({ length: pts * 2 }, (_, i) => {
                const angle = (Math.PI / pts) * i - Math.PI / 2;
                const r = i % 2 === 0 ? 12 : 6;
                const x = 18 + Math.cos(angle) * r;
                const y = 18 + Math.sin(angle) * r;
                return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`;
              }).join(' ') + ' Z'
            );
          })()}
          fill={color}
        />
        <Circle cx={18} cy={18} r={3} fill={colors.night} />
      </Svg>
      <View style={[styles.dividerLine, { backgroundColor: color }]} />
    </View>
  );
}

// ─── Arapça İfade ─────────────────────────────────────────────────────────────

export function ArabicPhrase({
  text,
  size = 15,
  color = colors.gold,
  opacity = 0.55,
  centered = true,
}: {
  text: string;
  size?: number;
  color?: string;
  opacity?: number;
  centered?: boolean;
}) {
  return (
    <Text
      style={{
        fontFamily: fonts.arabic,
        fontSize: size,
        color,
        opacity,
        textAlign: centered ? 'center' : 'right',
        letterSpacing: 1.5,
        lineHeight: size * 1.7,
      }}>
      {text}
    </Text>
  );
}

// ─── Büyük arka plan süsü (absolute) ─────────────────────────────────────────

export function IslamicBackgroundAccent({
  position = 'top-right',
  size = 180,
  opacity = 0.04,
}: {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'center';
  size?: number;
  opacity?: number;
}) {
  const posStyle: Record<string, number> = {};
  if (position === 'top-right') { posStyle.top = -size * 0.3; posStyle.right = -size * 0.3; }
  else if (position === 'top-left') { posStyle.top = -size * 0.3; posStyle.left = -size * 0.3; }
  else if (position === 'bottom-right') { posStyle.bottom = -size * 0.3; posStyle.right = -size * 0.3; }
  else if (position === 'bottom-left') { posStyle.bottom = -size * 0.3; posStyle.left = -size * 0.3; }
  else { posStyle.top = '50%'; posStyle.left = '50%'; posStyle.marginTop = -size / 2; posStyle.marginLeft = -size / 2; }

  return (
    <View
      pointerEvents="none"
      style={[StyleSheet.absoluteFill.valueOf ? { position: 'absolute' } : {}, posStyle]}>
      <GeometricRosette size={size} opacity={opacity} />
    </View>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  dividerWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 12,
  },
  dividerLine: {
    flex: 1,
    height: 1,
  },
  dividerStar: {
    marginHorizontal: 10,
  },
});
