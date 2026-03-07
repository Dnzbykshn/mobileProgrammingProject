/**
 * Location Picker — 3-step flow: Country → State → District
 * Navigates back and fires an onSelect callback via router params.
 * Saves selection to AsyncStorage.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
    View, Text, FlatList, TouchableOpacity,
    TextInput, ActivityIndicator, Pressable,
} from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronRight, ChevronLeft, MapPin, Search, Check } from 'lucide-react-native';

import { fetchCountries, fetchStates, fetchDistricts, Country, State, District } from '@/services/locations';
import { setDistrictId, getDistrictId } from '@/services/prayerTimes';

type Step = 'country' | 'state' | 'district';

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
    const [currentDistrictId, setCurrentDistrictId] = useState<string>('');

    // Load countries on mount + get current selection
    useEffect(() => {
        (async () => {
            setLoading(true);
            try {
                const [data, savedId] = await Promise.all([
                    fetchCountries(),
                    getDistrictId(),
                ]);
                // Sort: Türkiye first, then KKTC, then alphabetical
                const sorted = [...data].sort((a, b) => {
                    if (a.id === '2') return -1;
                    if (b.id === '2') return 1;
                    if (a.id === '1') return -1;
                    if (b.id === '1') return 1;
                    return a.name.localeCompare(b.name, 'tr');
                });
                setCountries(sorted);
                setCurrentDistrictId(savedId);
            } catch {
                // Keep empty — user sees empty list
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    const handleCountrySelect = useCallback(async (country: Country) => {
        setSelectedCountry(country);
        setQuery('');
        setLoading(true);
        try {
            const data = await fetchStates(country.id);
            setStates(data.sort((a, b) => a.name.localeCompare(b.name, 'tr')));
            setStep('state');
        } catch {
            setStates([]);
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
            const data = await fetchDistricts(state.id);
            setDistricts(data.sort((a, b) => a.name.localeCompare(b.name, 'tr')));
            setStep('district');
        } catch {
            setDistricts([]);
            setStep('district');
        } finally {
            setLoading(false);
        }
    }, []);

    const handleDistrictSelect = useCallback(async (district: District) => {
        await setDistrictId(district.id);
        router.back();
    }, [router]);

    const goBack = useCallback(() => {
        setQuery('');
        if (step === 'district') setStep('state');
        else if (step === 'state') setStep('country');
        else router.back();
    }, [step, router]);

    // --- Filtered lists ---
    const filteredCountries = query
        ? countries.filter(c => c.name.toLowerCase().includes(query.toLowerCase()))
        : countries;

    const filteredStates = query
        ? states.filter(s => s.name.toLowerCase().includes(query.toLowerCase()))
        : states;

    const filteredDistricts = query
        ? districts.filter(d => d.name.toLowerCase().includes(query.toLowerCase()))
        : districts;

    // --- Step title ---
    const titles: Record<Step, string> = {
        country: 'Ülke Seç',
        state: `${selectedCountry?.name ?? 'Şehir'} › Şehir Seç`,
        district: `${selectedState?.name ?? 'İlçe'} › İlçe Seç`,
    };

    const renderItem = useCallback(({ item }: { item: Country | State | District }) => {
        const isCurrentDistrict = step === 'district' && (item as District).id === currentDistrictId;
        return (
            <TouchableOpacity
                onPress={() => {
                    if (step === 'country') handleCountrySelect(item as Country);
                    else if (step === 'state') handleStateSelect(item as State);
                    else handleDistrictSelect(item as District);
                }}
                className="flex-row items-center justify-between px-5 py-4 border-b border-[#1A4642]"
                activeOpacity={0.7}
            >
                <View className="flex-row items-center flex-1">
                    {isCurrentDistrict && (
                        <Check size={16} color="#FFD700" style={{ marginRight: 10 }} />
                    )}
                    <Text
                        className={`text-base ${isCurrentDistrict ? 'text-[#FFD700] font-bold' : 'text-[#E5E9E9]'}`}
                        style={{ textTransform: 'capitalize' }}
                    >
                        {(item as any).name.charAt(0) + (item as any).name.slice(1).toLowerCase()}
                    </Text>
                </View>
                {step !== 'district' && <ChevronRight size={18} color="#436F65" />}
            </TouchableOpacity>
        );
    }, [step, currentDistrictId, handleCountrySelect, handleStateSelect, handleDistrictSelect]);

    return (
        <View className="flex-1 bg-[#0B3130]">
            {/* Header */}
            <View className="flex-row items-center px-4 pt-14 pb-4 border-b border-[#1A4642]">
                <Pressable onPress={goBack} className="p-2 mr-3">
                    <ChevronLeft size={24} color="#E5E9E9" />
                </Pressable>
                <MapPin size={18} color="#FFD700" style={{ marginRight: 8 }} />
                <Text className="text-[#E5E9E9] text-lg font-bold flex-1" numberOfLines={1}>
                    {titles[step]}
                </Text>
            </View>

            {/* Search */}
            <View className="mx-4 my-3 flex-row items-center bg-[#113835] rounded-xl px-4 border border-[#1A4642]">
                <Search size={16} color="#436F65" />
                <TextInput
                    value={query}
                    onChangeText={setQuery}
                    placeholder="Ara..."
                    placeholderTextColor="#436F65"
                    className="flex-1 py-3 px-3 text-[#E5E9E9]"
                    autoCorrect={false}
                    autoCapitalize="none"
                />
            </View>

            {/* List */}
            {loading ? (
                <View className="flex-1 items-center justify-center">
                    <ActivityIndicator color="#FFD700" size="large" />
                </View>
            ) : (
                <FlatList
                    data={
                        step === 'country' ? filteredCountries
                        : step === 'state' ? filteredStates
                        : filteredDistricts
                    }
                    keyExtractor={item => (item as any).id}
                    renderItem={renderItem}
                    contentContainerStyle={{ paddingBottom: 40 }}
                    keyboardShouldPersistTaps="handled"
                    ListEmptyComponent={
                        <View className="items-center justify-center mt-16">
                            <Text className="text-[#436F65] text-base">Sonuç bulunamadı</Text>
                        </View>
                    }
                />
            )}
        </View>
    );
}
