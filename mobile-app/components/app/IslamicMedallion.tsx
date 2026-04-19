/**
 * IslamicMedallion — Tek büyük geometrik süs
 *
 * Tekrarlayan döşeme yerine ekranın üstünde duran,
 * yarı saydam tek bir madalyon. Ottoman/Safavi el yazması
 * rozet geleneğinden ilham alınmıştır.
 */

import React, { useMemo } from 'react';
import { StyleSheet, useWindowDimensions, View } from 'react-native';
import Svg, { Circle, G, Line, Path } from 'react-native-svg';

import { colors } from '@/theme';

function buildStarPath(cx: number, cy: number, rOuter: number, rInner: number, points: number) {
  const total = points * 2;
  const pts = Array.from({ length: total }, (_, i) => {
    const angle = (Math.PI / points) * i - Math.PI / 2;
    const r = i % 2 === 0 ? rOuter : rInner;
    return {
      x: cx + Math.cos(angle) * r,
      y: cy + Math.sin(angle) * r,
    };
  });
  return pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ') + ' Z';
}

function buildSpokes(cx: number, cy: number, r1: number, r2: number, count: number) {
  return Array.from({ length: count }, (_, i) => {
    const angle = (Math.PI * 2 * i) / count - Math.PI / 2;
    return {
      x1: cx + Math.cos(angle) * r1,
      y1: cy + Math.sin(angle) * r1,
      x2: cx + Math.cos(angle) * r2,
      y2: cy + Math.sin(angle) * r2,
    };
  });
}

type Props = {
  /** Madalyon çapı (px) */
  size?: number;
  /**
   * 'top' → ekranın tepesinde, ortada, yarı görünür (tab ekranlar için)
   * 'float' → tam ekranda, ortada, çok soluk (auth için arka plan)
   */
  variant?: 'top' | 'float';
  color?: string;
  opacity?: number;
};

export default function IslamicMedallion({
  size = 320,
  variant = 'top',
  color = colors.gold,
  opacity,
}: Props) {
  const { width } = useWindowDimensions();

  // Varsayılan opaklıklar
  const alpha = opacity ?? (variant === 'top' ? 0.055 : 0.07);

  const cx = size / 2;
  const cy = size / 2;

  // Katmanlar (dıştan içe)
  const R = size * 0.46;   // dış çember yarıçapı
  const r16o = R * 0.92;   // 16-köşeli yıldız dış
  const r16i = R * 0.70;   // 16-köşeli yıldız iç
  const r8o  = R * 0.52;   // 8-köşeli yıldız dış
  const r8i  = R * 0.30;   // 8-köşeli yıldız iç
  const rCore = R * 0.09;  // merkez halka

  const star16 = useMemo(() => buildStarPath(cx, cy, r16o, r16i, 16), [cx, cy, r16o, r16i]);
  const star8  = useMemo(() => buildStarPath(cx, cy, r8o, r8i, 8),  [cx, cy, r8o, r8i]);
  const spokes16 = useMemo(() => buildSpokes(cx, cy, r8i, r16o, 16), [cx, cy, r8i, r16o]);
  const spokes8  = useMemo(() => buildSpokes(cx, cy, rCore, r8i, 8),  [cx, cy, rCore, r8i]);

  const containerStyle =
    variant === 'top'
      ? {
          position: 'absolute' as const,
          top: -(size * 0.38),
          left: (width - size) / 2,
          width: size,
          height: size,
        }
      : {
          position: 'absolute' as const,
          top: (size * -0.1),
          left: (width - size) / 2,
          width: size,
          height: size,
        };

  return (
    <View pointerEvents="none" style={containerStyle}>
      <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} opacity={alpha}>
        <G stroke={color} fill="none">
          {/* Dış çift halka */}
          <Circle cx={cx} cy={cy} r={R} strokeWidth={1.2} strokeOpacity={0.9} />
          <Circle cx={cx} cy={cy} r={R * 0.97} strokeWidth={0.5} strokeOpacity={0.4} />

          {/* İnce ara halka */}
          <Circle cx={cx} cy={cy} r={R * 0.73} strokeWidth={0.6} strokeOpacity={0.3} />

          {/* 16-köşeli dış yıldız */}
          <Path d={star16} strokeWidth={1} strokeOpacity={0.9} />

          {/* 16 ışın (dış yıldız tepelerinden iç yıldıza) */}
          {spokes16.map((s, i) => (
            <Line
              key={`s16-${i}`}
              x1={s.x1.toFixed(2)} y1={s.y1.toFixed(2)}
              x2={s.x2.toFixed(2)} y2={s.y2.toFixed(2)}
              strokeWidth={0.5} strokeOpacity={0.25}
            />
          ))}

          {/* 8-köşeli iç yıldız */}
          <Path d={star8} strokeWidth={0.9} strokeOpacity={0.8} />

          {/* 8 ışın (iç yıldızdan merkeze) */}
          {spokes8.map((s, i) => (
            <Line
              key={`s8-${i}`}
              x1={s.x1.toFixed(2)} y1={s.y1.toFixed(2)}
              x2={s.x2.toFixed(2)} y2={s.y2.toFixed(2)}
              strokeWidth={0.5} strokeOpacity={0.2}
            />
          ))}

          {/* Merkez çift halka */}
          <Circle cx={cx} cy={cy} r={rCore} strokeWidth={0.8} strokeOpacity={0.7} />
          <Circle cx={cx} cy={cy} r={rCore * 0.45} strokeWidth={0.6} strokeOpacity={0.5} />

          {/* 16 küçük nokta dış halkada */}
          {Array.from({ length: 16 }, (_, i) => {
            const angle = (Math.PI * 2 * i) / 16 - Math.PI / 2;
            return (
              <Circle
                key={`dot-${i}`}
                cx={(cx + Math.cos(angle) * R).toFixed(2)}
                cy={(cy + Math.sin(angle) * R).toFixed(2)}
                r={2.2}
                strokeWidth={0}
                fill={color}
                fillOpacity={0.7}
              />
            );
          })}
        </G>

        {/* Merkez altın nokta */}
        <Circle cx={cx} cy={cy} r={rCore * 0.45} fill={color} fillOpacity={0.6} />
      </Svg>
    </View>
  );
}

export const medallionStyles = StyleSheet.create({
  absoluteFill: { ...StyleSheet.absoluteFillObject },
});
