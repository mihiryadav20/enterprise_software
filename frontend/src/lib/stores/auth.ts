import { writable } from 'svelte/store';

export interface User {
  username: string;
  // Add other user fields as needed
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

const createAuthStore = () => {
  const { subscribe, set, update } = writable<AuthState>({
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
  });

  // Initialize from localStorage if available
  if (typeof window !== 'undefined') {
    const storedAuth = localStorage.getItem('auth');
    if (storedAuth) {
      try {
        const parsed = JSON.parse(storedAuth);
        set({
          user: parsed.user,
          accessToken: parsed.accessToken,
          refreshToken: parsed.refreshToken,
          isAuthenticated: true,
        });
      } catch (e) {
        console.error('Failed to parse auth from localStorage', e);
        localStorage.removeItem('auth');
      }
    }
  }

  const store = {
    subscribe,
    get accessToken() {
      let token: string | null = null;
      subscribe(state => { token = state.accessToken; })();
      return token;
    },
    get refreshToken() {
      let token: string | null = null;
      subscribe(state => { token = state.refreshToken; })();
      return token;
    },
    login: (username: string, accessToken: string, refreshToken: string) => {
      const user = { username };
      const authData = {
        user,
        accessToken,
        refreshToken,
        isAuthenticated: true,
      };
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth', JSON.stringify({
          user,
          accessToken,
          refreshToken,
        }));
      }
      set(authData);
    },
    logout: () => {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth');
      }
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
      });
    },
    updateAccessToken: (accessToken: string) => {
      update(state => {
        const newState = {
          ...state,
          accessToken,
        };
        if (typeof window !== 'undefined' && state.refreshToken) {
          localStorage.setItem('auth', JSON.stringify({
            user: state.user,
            accessToken,
            refreshToken: state.refreshToken,
          }));
        }
        return newState;
      });
    },
  };

  return store;
};

export const auth = createAuthStore();
