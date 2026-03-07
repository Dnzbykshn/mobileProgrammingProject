import { View, StyleSheet, LayoutChangeEvent, Pressable } from 'react-native';
import { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import TabBarButton from './TabBarButton';
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from 'react-native-reanimated';
import { useState } from 'react';
import Svg, { Path } from 'react-native-svg';

export function TabBar({ state, descriptors, navigation }: BottomTabBarProps) {
    const [dimensions, setDimensions] = useState({ height: 20, width: 100 });

    const buttonWidth = dimensions.width / state.routes.length;

    const onTabbarLayout = (e: LayoutChangeEvent) => {
        setDimensions({
            height: e.nativeEvent.layout.height,
            width: e.nativeEvent.layout.width,
        });
    };

    const tabPositionX = useSharedValue(0);

    const animatedStyle = useAnimatedStyle(() => {
        return {
            transform: [{ translateX: tabPositionX.value }],
        };
    });

    return (
        <View onLayout={onTabbarLayout} style={styles.tabBar}>
            <Svg
                width={dimensions.width}
                height={dimensions.height + 50} // Add extra height for the curve
                viewBox={`0 0 ${dimensions.width} ${dimensions.height + 50}`}
                style={styles.svgBackground}
            >
                <Path
                    d={`
            M0,0
            L${(dimensions.width / 2) - 45},0
            C${(dimensions.width / 2) - 30},0 ${(dimensions.width / 2) - 30},40 ${(dimensions.width / 2)},40
            C${(dimensions.width / 2) + 30},40 ${(dimensions.width / 2) + 30},0 ${(dimensions.width / 2) + 45},0
            L${dimensions.width},0
            L${dimensions.width},${dimensions.height + 50}
            L0,${dimensions.height + 50}
            Z
          `}
                    fill="#06181C"
                />
            </Svg>

            {state.routes.map((route, index) => {
                const { options } = descriptors[route.key];
                const label =
                    options.tabBarLabel !== undefined
                        ? options.tabBarLabel
                        : options.title !== undefined
                            ? options.title
                            : route.name;

                const isFocused = state.index === index;

                const onPress = () => {
                    tabPositionX.value = withSpring(buttonWidth * index, { duration: 1500 });
                    const event = navigation.emit({
                        type: 'tabPress',
                        target: route.key,
                        canPreventDefault: true,
                    });

                    if (!isFocused && !event.defaultPrevented) {
                        navigation.navigate(route.name, route.params);
                    }
                };

                const onLongPress = () => {
                    navigation.emit({
                        type: 'tabLongPress',
                        target: route.key,
                    });
                };

                return (
                    <TabBarButton
                        key={route.name}
                        onPress={onPress}
                        onLongPress={onLongPress}
                        isFocused={isFocused}
                        routeName={route.name}
                        color={isFocused ? '#ffffff' : '#436F65'}
                        label={label}
                    />
                );
            })}
        </View>
    );
}

const styles = StyleSheet.create({
    tabBar: {
        position: 'absolute',
        bottom: 0,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: 'transparent', // Transparent because we use SVG
        width: '100%',
        height: 70, // Adjust height as needed
        elevation: 0,
        borderTopWidth: 0,
    },
    svgBackground: {
        position: 'absolute',
        top: -15, // Move up to cover the space
        left: 0,
        right: 0,
        bottom: 0,
        // iOS shadow
        shadowColor: "#000",
        shadowOffset: {
            width: 0,
            height: -2,
        },
        shadowOpacity: 0.1,
        shadowRadius: 3,
        // Android shadow
        elevation: 5,
    },
});
