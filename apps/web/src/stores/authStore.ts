import { create } from 'zustand';
import { auth, setAccessToken, User } from '@ecommerce/sdk';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  error: string | null;
  login: (credentials: { email:string; password: string }) => Promise<void>;
  register: (userData: any) => Promise<void>;
  logout: () => void;
  fetchProfile: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  isLoading: false,
  error: null,

  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const { access_token } = await auth.login(credentials);
      setAccessToken(access_token);
      set({ accessToken: access_token, isLoading: false });
      await useAuthStore.getState().fetchProfile();
    } catch (err) {
      set({ error: 'Failed to login', isLoading: false });
    }
  },

  register: async (userData) => {
    set({ isLoading: true, error: null });
    try {
      const { access_token } = await auth.register(userData);
      setAccessToken(access_token);
      set({ accessToken: access_token, isLoading: false });
      await useAuthStore.getState().fetchProfile();
    } catch (err) {
      set({ error: 'Failed to register', isLoading: false });
    }
  },

  logout: () => {
    setAccessToken(null);
    set({ user: null, accessToken: null });
  },

  fetchProfile: async () => {
    set({ isLoading: true, error: null });
    try {
      const user = await auth.getProfile();
      set({ user, isLoading: false });
    } catch (err) {
      set({ error: 'Failed to fetch profile', isLoading: false });
      useAuthStore.getState().logout();
    }
  },
}));
