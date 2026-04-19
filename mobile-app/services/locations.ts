/**
 * Location service — wraps /api/v1/locations/* endpoints.
 */

import { api } from './api';

export interface Country {
  id: string;
  name: string;
  name_en: string;
}

export interface State {
  id: string;
  name: string;
  name_en: string;
  country_id: string;
}

export interface District {
  id: string;
  name: string;
  name_en: string;
  state_id: string;
  country_id: string;
}

export async function fetchCountries(): Promise<Country[]> {
  return api.get<Country[]>('/locations/countries');
}

export async function fetchStates(countryId: string): Promise<State[]> {
  return api.get<State[]>(`/locations/states?country_id=${countryId}`);
}

export async function fetchDistricts(stateId: string): Promise<District[]> {
  return api.get<District[]>(`/locations/districts?state_id=${stateId}`);
}

export async function fetchDistrict(districtId: string): Promise<District> {
  return api.get<District>(`/locations/district/${districtId}`);
}
