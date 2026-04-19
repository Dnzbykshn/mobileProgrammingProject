import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, FlatList, Text, TouchableOpacity, View } from 'react-native';
import { Search } from 'lucide-react-native';
import { useRouter } from 'expo-router';

import AppInput from '@/components/app/AppInput';
import EmptyState from '@/components/app/EmptyState';
import PageHeader from '@/components/app/PageHeader';
import ScreenWrapper from '@/components/ScreenWrapper';
import { colors, fonts, radius, spacing, typography } from '@/theme';
import {
  Country,
  District,
  fetchCountries,
  fetchDistricts,
  fetchStates,
  State,
} from '@/services/locations';
import { getDistrictId, setDistrictId } from '@/services/prayerTimes';

type Step = 'country' | 'state' | 'district';

type StepItem = Country | State | District;

export default function LocationPickerScreen() {
  const router = useRouter();

  const [step, setStep] = useState<Step>('country');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [countries, setCountries] = useState<Country[]>([]);
  const [states, setStates] = useState<State[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<Country | null>(null);
  const [selectedState, setSelectedState] = useState<State | null>(null);
  const [currentDistrictId, setCurrentDistrictId] = useState('');

  useEffect(() => {
    const loadInitial = async () => {
      setLoading(true);
      try {
        const [countryList, districtId] = await Promise.all([fetchCountries(), getDistrictId()]);
        setCountries(countryList);
        setCurrentDistrictId(districtId);
      } finally {
        setLoading(false);
      }
    };

    void loadInitial();
  }, []);

  const handleCountrySelect = useCallback(async (country: Country) => {
    setSelectedCountry(country);
    setQuery('');
    setLoading(true);
    try {
      const nextStates = await fetchStates(country.id);
      setStates(nextStates);
      setStep('state');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleStateSelect = useCallback(async (state: State) => {
    setSelectedState(state);
    setQuery('');
    setLoading(true);
    try {
      const nextDistricts = await fetchDistricts(state.id);
      setDistricts(nextDistricts);
      setStep('district');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDistrictSelect = useCallback(
    async (district: District) => {
      await setDistrictId(district.id);
      router.back();
    },
    [router]
  );

  const items = useMemo<StepItem[]>(() => {
    if (step === 'country') return countries;
    if (step === 'state') return states;
    return districts;
  }, [countries, districts, states, step]);

  const filteredItems = useMemo(
    () => items.filter((item) => item.name.toLowerCase().includes(query.trim().toLowerCase())),
    [items, query]
  );

  const title =
    step === 'country'
      ? 'Konum'
      : step === 'state'
        ? selectedCountry?.name || 'Şehir'
        : selectedState?.name || 'İlçe';

  return (
    <ScreenWrapper>
      <View style={{ flex: 1, paddingHorizontal: spacing.lg, paddingTop: spacing.lg }}>
        <PageHeader
          title={title}
          subtitle={step === 'country' ? 'Ülke seç' : step === 'state' ? 'Şehir seç' : 'İlçe seç'}
          eyebrow="Konum"
          back
        />

        <View
          style={{
            borderRadius: radius.xl,
            borderWidth: 1,
            borderColor: colors.border.paper,
            backgroundColor: colors.surface.paperRaised,
            padding: spacing.md,
            marginBottom: spacing.md,
          }}>
          <AppInput icon={Search} value={query} onChangeText={setQuery} placeholder="Ara" />
        </View>

        {loading ? (
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
            <ActivityIndicator size="large" color={colors.gold} />
          </View>
        ) : (
          <FlatList
            data={filteredItems}
            keyExtractor={(item) => item.id}
            contentContainerStyle={{ paddingBottom: spacing.huge, gap: spacing.sm + 2 }}
            renderItem={({ item }) => {
              const selected = step === 'district' && item.id === currentDistrictId;

              return (
                <TouchableOpacity
                  activeOpacity={0.88}
                  onPress={() => {
                    if (step === 'country') {
                      void handleCountrySelect(item as Country);
                    } else if (step === 'state') {
                      void handleStateSelect(item as State);
                    } else {
                      void handleDistrictSelect(item as District);
                    }
                  }}>
                  <View
                    style={{
                      borderRadius: radius.xl,
                      paddingHorizontal: spacing.lg,
                      paddingVertical: spacing.md,
                      borderWidth: 1,
                      borderColor: selected ? colors.border.gold : colors.border.paper,
                      backgroundColor: selected
                        ? colors.surface.goldSoft
                        : colors.surface.paperRaised,
                    }}>
                    <View
                      style={{
                        flexDirection: 'row',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}>
                      <Text
                        style={{
                          ...typography.bodyMd,
                          fontFamily: selected ? fonts.bodyMd : fonts.body,
                          color: colors.ink,
                        }}>
                        {item.name}
                      </Text>

                      {selected ? (
                        <Text
                          style={{
                            ...typography.labelMd,
                            fontFamily: fonts.bodySm,
                            color: colors.goldDeep,
                          }}>
                          SEÇİLİ
                        </Text>
                      ) : null}
                    </View>
                  </View>
                </TouchableOpacity>
              );
            }}
            ListEmptyComponent={<EmptyState message="Sonuç bulunamadı." />}
          />
        )}
      </View>
    </ScreenWrapper>
  );
}
