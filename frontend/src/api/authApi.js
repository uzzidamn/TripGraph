const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

async function call(path, opts = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...opts.headers },
    ...opts,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export const register = ({ email, password, displayName }) =>
  call("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, display_name: displayName }),
  });

export const login = ({ email, password }) =>
  call("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

export const getMe = (token) =>
  call("/api/auth/me", { headers: { Authorization: `Bearer ${token}` } }).catch(() => null);
