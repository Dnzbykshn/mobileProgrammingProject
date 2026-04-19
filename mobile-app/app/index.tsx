import { Redirect } from 'expo-router';
import { ActivityIndicator, View } from 'react-native';

import { useAuth } from '@/contexts/AuthContext';
import { colors } from '@/theme';

export default function Index() {
  const { isLoading, isLoggedIn } = useAuth();

  if (isLoading) {
    return (
      <View
        style={{
          flex: 1,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: colors.paper,
        }}>
        <ActivityIndicator size="large" color={colors.gold} />
      </View>
    );
  }

  return <Redirect href={isLoggedIn ? '/(tabs)' : '/auth/login'} />;
}
