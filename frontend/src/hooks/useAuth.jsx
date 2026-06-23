import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getMe } from "../api/authApi";

const AuthContext = createContext(null);

const TOKEN_KEY = "tg_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);

  // Validate stored token on mount
  useEffect(() => {
    if (!token) return;
    getMe(token).then((u) => {
      if (u) {
        setUser(u);
      } else {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      }
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const signIn = useCallback((accessToken, userData) => {
    localStorage.setItem(TOKEN_KEY, accessToken);
    setToken(accessToken);
    setUser(userData);
  }, []);

  const signOut = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  // Return safe defaults when called outside AuthProvider (shouldn't happen, but guards HMR edge cases)
  if (!ctx) return { token: null, user: null, signIn: () => {}, signOut: () => {} };
  return ctx;
}
