// TabBarButton.tsx
import { View, Pressable, StyleSheet } from 'react-native';
import React, { useEffect } from 'react';
import { Home, Compass, User, Plus, Fingerprint } from 'lucide-react-native';
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from 'react-native-reanimated';

export default function TabBarButton({
    onPress,
    onLongPress,
    isFocused,
    routeName,
    color,
    label
}: {
    onPress: () => void;
    onLongPress: () => void;
    isFocused: boolean;
    routeName: string;
    color: string;
    label: any;
}) {
    const scale = useSharedValue(0);

    useEffect(() => {
        scale.value = withSpring(typeof isFocused === 'boolean' ? (isFocused ? 1 : 0) : isFocused, { duration: 350 });
    }, [scale, isFocused]);

    const animatedIconStyle = useAnimatedStyle(() => {
        return {
            transform: [{ scale: scale.value }],
        };
    });

    const icons: { [key: string]: (props: any) => React.ReactElement } = {
        index: (props: any) => <Home size={24} {...props} />,
        explore: (props: any) => <Compass size={24} {...props} />,
        chat: (props: any) => <Plus size={30} color="#000" {...props} />,
        dhikr: (props: any) => <Fingerprint size={24} {...props} />,
        profile: (props: any) => <User size={24} {...props} />,
    };

    const IconComponent = icons[routeName] || icons['index'];

    if (routeName === 'chat') {
        return (
            <Pressable
                onPress={onPress}
                onLongPress={onLongPress}
                style={styles.containerMiddle}
            >
                <View style={styles.circleButton}>
                    <IconComponent />
                </View>
            </Pressable>
        )
    }

    return (
        <Pressable
            onPress={onPress}
            onLongPress={onLongPress}
            style={styles.container}
        >
            <IconComponent color={color} />
        </Pressable>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingVertical: 10,
    },
    containerMiddle: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        height: 60,
        bottom: 30, // Move it up
        zIndex: 10,
    },
    circleButton: {
        width: 60,
        height: 60,
        borderRadius: 30,
        backgroundColor: '#66E0C6', // Cyan/Teal pop color
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: "#000",
        shadowOffset: {
            width: 0,
            height: 4,
        },
        shadowOpacity: 0.3,
        shadowRadius: 4.65,
        elevation: 8,
    }
});
