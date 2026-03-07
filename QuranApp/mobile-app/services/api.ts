/**
 * API Client — Central HTTP layer with JWT interceptor + network fallback.
 * All services import from here.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';

// Change this to your actual backend URL
// For physical devices, use your computer's local IP instead of localhost
const BASE_URL = __DEV__
    ? 'http://192.168.1.164:8000/api/v1'
    : 'https://your-production-api.com/api/v1';

const ACCESS_TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const DEVICE_ID_KEY = 'device_id';
const REQUEST_TIMEOUT_MS = 60_000; // 60 saniye (READY fazı birden fazla LLM çağrısı yapar)
let unauthorizedHandler: (() => void) | null = null;
let refreshPromise: Promise<string | null> | null = null;

async function hasSecureStore(): Promise<boolean> {
    try {
        return await SecureStore.isAvailableAsync();
    } catch {
        return false;
    }
}

/** Store JWT token */
export async function setToken(token: string): Promise<void> {
    await setAccessToken(token);
}

async function setAccessToken(token: string): Promise<void> {
    if (await hasSecureStore()) {
        await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, token);
        // Clean up any legacy plaintext token copy.
        await AsyncStorage.removeItem(ACCESS_TOKEN_KEY);
        return;
    }
    // Fallback (e.g. unsupported platform): keep current behavior.
    await AsyncStorage.setItem(ACCESS_TOKEN_KEY, token);
}

/** Get stored JWT token */
export async function getToken(): Promise<string | null> {
    return getAccessToken();
}

async function getAccessToken(): Promise<string | null> {
    if (await hasSecureStore()) {
        const secureToken = await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
        if (secureToken) {
            return secureToken;
        }

        // One-time migration from legacy AsyncStorage token.
        const legacyToken = await AsyncStorage.getItem(ACCESS_TOKEN_KEY);
        if (legacyToken) {
            await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, legacyToken);
            await AsyncStorage.removeItem(ACCESS_TOKEN_KEY);
        }
        return legacyToken;
    }

    return await AsyncStorage.getItem(ACCESS_TOKEN_KEY);
}

export async function getRefreshToken(): Promise<string | null> {
    if (await hasSecureStore()) {
        return await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
    }
    return await AsyncStorage.getItem(REFRESH_TOKEN_KEY);
}

function createDeviceId(): string {
    // Prefer cryptographically strong UUID when available.
    if (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function') {
        return globalThis.crypto.randomUUID();
    }
    const rand = `${Math.random().toString(36).slice(2)}${Math.random().toString(36).slice(2)}`;
    return `dev-${Date.now().toString(36)}-${rand.slice(0, 20)}`;
}

async function getOrCreateDeviceId(): Promise<string> {
    if (await hasSecureStore()) {
        const existing = await SecureStore.getItemAsync(DEVICE_ID_KEY);
        if (existing) return existing;

        // One-time migration from AsyncStorage fallback key.
        const legacy = await AsyncStorage.getItem(DEVICE_ID_KEY);
        const deviceId = legacy || createDeviceId();
        await SecureStore.setItemAsync(DEVICE_ID_KEY, deviceId);
        await AsyncStorage.removeItem(DEVICE_ID_KEY);
        return deviceId;
    }

    const existing = await AsyncStorage.getItem(DEVICE_ID_KEY);
    if (existing) return existing;
    const created = createDeviceId();
    await AsyncStorage.setItem(DEVICE_ID_KEY, created);
    return created;
}

export async function setAuthTokens(accessToken: string, refreshToken?: string | null): Promise<void> {
    await setAccessToken(accessToken);
    if (!refreshToken) return;

    if (await hasSecureStore()) {
        await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken);
        await AsyncStorage.removeItem(REFRESH_TOKEN_KEY);
        return;
    }
    await AsyncStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

/** Remove stored JWT token */
export async function removeToken(): Promise<void> {
    if (await hasSecureStore()) {
        await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
        await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    }
    await AsyncStorage.removeItem(ACCESS_TOKEN_KEY);
    await AsyncStorage.removeItem(REFRESH_TOKEN_KEY);
}

/** Register global callback for auth failures (401). */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
    unauthorizedHandler = handler;
}

/** Typed API error */
export class ApiError extends Error {
    status: number;
    isNetworkError: boolean;

    constructor(status: number, message: string, isNetworkError = false) {
        super(message);
        this.status = status;
        this.name = 'ApiError';
        this.isNetworkError = isNetworkError;
    }
}

/** Fetch with timeout */
function fetchWithTimeout(url: string, options: RequestInit, timeoutMs: number): Promise<Response> {
    return new Promise((resolve, reject) => {
        const controller = new AbortController();
        const timer = setTimeout(() => {
            controller.abort();
            reject(new ApiError(0, 'Request timeout', true));
        }, timeoutMs);

        fetch(url, { ...options, signal: controller.signal })
            .then(resolve)
            .catch((err) => {
                if (err.name === 'AbortError') {
                    reject(new ApiError(0, 'Request timeout', true));
                } else {
                    reject(new ApiError(0, err.message || 'Network error', true));
                }
            })
            .finally(() => clearTimeout(timer));
    });
}

function canAttemptRefresh(endpoint: string): boolean {
    if (endpoint.startsWith('/auth/login')) return false;
    if (endpoint.startsWith('/auth/register')) return false;
    if (endpoint.startsWith('/auth/refresh')) return false;
    return true;
}

async function refreshAccessToken(): Promise<string | null> {
    if (refreshPromise) {
        return refreshPromise;
    }

    refreshPromise = (async () => {
        const refreshToken = await getRefreshToken();
        if (!refreshToken) {
            return null;
        }
        const deviceId = await getOrCreateDeviceId();

        const response = await fetchWithTimeout(
            `${BASE_URL}/auth/refresh`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Device-ID': deviceId,
                },
                body: JSON.stringify({ refresh_token: refreshToken }),
            },
            REQUEST_TIMEOUT_MS,
        ).catch(async () => {
            await removeToken();
            return null as Response | null;
        });

        if (!response) {
            return null;
        }

        if (!response.ok) {
            await removeToken();
            return null;
        }

        const data = await response.json().catch(() => null as any);
        const nextAccessToken = data?.access_token as string | undefined;
        const nextRefreshToken = (data?.refresh_token as string | undefined) ?? refreshToken;
        if (!nextAccessToken) {
            await removeToken();
            return null;
        }

        await setAuthTokens(nextAccessToken, nextRefreshToken);
        return nextAccessToken;
    })().finally(() => {
        refreshPromise = null;
    });

    return refreshPromise;
}

/** Core fetch wrapper with auth headers, timeout, and error handling */
async function request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryOnAuthFailure = true,
): Promise<T> {
    const token = await getAccessToken();
    const deviceId = await getOrCreateDeviceId();

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
    };

    if (!headers['X-Device-ID']) {
        headers['X-Device-ID'] = deviceId;
    }

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetchWithTimeout(
        `${BASE_URL}${endpoint}`,
        { ...options, headers },
        REQUEST_TIMEOUT_MS,
    );

    if (!response.ok) {
        if (response.status === 401 && retryOnAuthFailure && canAttemptRefresh(endpoint)) {
            const refreshedAccessToken = await refreshAccessToken();
            if (refreshedAccessToken) {
                return request<T>(endpoint, options, false);
            }
        }

        if (response.status === 401) {
            await removeToken();
            unauthorizedHandler?.();
        }
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new ApiError(response.status, error.detail || 'Request failed');
    }

    return response.json();
}

/** Check if an error is a network/server unreachable error */
export function isNetworkError(error: unknown): boolean {
    // Check by property (instanceof can fail across Metro bundles)
    if (error && typeof error === 'object') {
        const e = error as any;
        if (e.isNetworkError === true || e.status === 0) return true;
        if (e.name === 'ApiError' && e.status === 0) return true;
        if (e.name === 'TypeError' && /network|fetch|abort/i.test(e.message || '')) return true;
    }
    return false;
}

// --- Export HTTP methods ---

export const api = {
    get: <T>(endpoint: string) => request<T>(endpoint, { method: 'GET' }),

    post: <T>(endpoint: string, body?: any) =>
        request<T>(endpoint, {
            method: 'POST',
            body: body ? JSON.stringify(body) : undefined,
        }),

    put: <T>(endpoint: string, body?: any) =>
        request<T>(endpoint, {
            method: 'PUT',
            body: body ? JSON.stringify(body) : undefined,
        }),

    delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' }),
};
