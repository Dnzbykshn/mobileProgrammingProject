import React from 'react';
import { StyleSheet, useWindowDimensions, View } from 'react-native';
import Svg, { Defs, Path, Pattern, Rect } from 'react-native-svg';

import { colors } from '@/theme';

const TILE_SIZE = 112;

function createStarPath(
  cx: number,
  cy: number,
  outerRadius: number,
  innerRadius: number,
  points: number
) {
  const totalPoints = points * 2;
  return Array.from({ length: totalPoints }, (_, index) => {
    const angle = (Math.PI / points) * index - Math.PI / 2;
    const radius = index % 2 === 0 ? outerRadius : innerRadius;
    const x = cx + Math.cos(angle) * radius;
    const y = cy + Math.sin(angle) * radius;
    return `${index === 0 ? 'M' : 'L'}${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(' ');
}

const centerStar = `${createStarPath(56, 56, 21, 11.5, 8)} Z`;
const cornerStar = `${createStarPath(0, 0, 16, 8.5, 8)} Z`;

export default function ArabesquePattern({ dark = false }: { dark?: boolean }) {
  const { width, height } = useWindowDimensions();
  const patternId = dark ? 'mqPatternDark' : 'mqPatternLight';
  const strokeColor = dark ? colors.gold : colors.goldDeep;
  const strokeOpacity = dark ? 0.12 : 0.08;

  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <Svg width={width} height={height} style={{ opacity: 1 }}>
        <Defs>
          <Pattern
            id={patternId}
            width={TILE_SIZE}
            height={TILE_SIZE}
            patternUnits="userSpaceOnUse">
            <Rect width={TILE_SIZE} height={TILE_SIZE} fill="transparent" />
            <Path
              d="M56 0 L112 56 L56 112 L0 56 Z M28 28 L84 28 L84 84 L28 84 Z"
              stroke={strokeColor}
              strokeOpacity={strokeOpacity * 2.5}
              strokeWidth={1.2}
              fill="none"
            />
            <Path
              d="M56 0 L56 28 M84 28 L112 56 M56 84 L56 112 M0 56 L28 56"
              stroke={strokeColor}
              strokeOpacity={strokeOpacity * 2}
              strokeWidth={1}
              fill="none"
            />
            <Path
              d={centerStar}
              stroke={strokeColor}
              strokeOpacity={strokeOpacity * 3}
              strokeWidth={1}
              fill="none"
            />
            <Path
              d={cornerStar}
              stroke={strokeColor}
              strokeOpacity={strokeOpacity * 2}
              strokeWidth={0.9}
              fill="none"
            />
            <Path
              d={`M112 0 ${cornerStar.slice(1)} M0 112 ${cornerStar.slice(1)} M112 112 ${cornerStar.slice(1)}`}
              stroke={strokeColor}
              strokeOpacity={strokeOpacity * 2}
              strokeWidth={0.9}
              fill="none"
            />
          </Pattern>
        </Defs>

        <Rect width="100%" height="100%" fill={`url(#${patternId})`} />
      </Svg>
    </View>
  );
}
