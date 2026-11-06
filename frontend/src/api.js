
const API = "http://127.0.0.1:8000";

// Convert backend errors into readable messages
function getErrorMessage(data, status) {
  const detail = data?.detail;

  if (Array.isArray(detail)) {
    return detail.map(item => {
      if (typeof item === "string") return item;

      if (item && typeof item === "object") {
        const field = Array.isArray(item.loc)
          ? item.loc.filter(x => x !== "body").join(" → ")
          : "";

        return field
          ? `${field}: ${item.msg || "Invalid value"}`
          : item.msg || JSON.stringify(item);
      }

      return String(item);
    }).join("; ");
  }

  if (typeof detail === "string") return detail;

  if (detail && typeof detail === "object") {
    return detail.msg || JSON.stringify(detail);
  }

  return data?.message || `Request failed (${status})`;
}

// Common API request function
export async function api(path, method = "GET", body = null) {
  const token = localStorage.getItem("fittrack_token");

  const headers = {
    "Content-Type": "application/json"
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const options = {
    method,
    headers
  };

  if (body !== null) {
    options.body = JSON.stringify(body);
  }

  let response;

  try {
    response = await fetch(`${API}${path}`, options);
  } catch {
    throw new Error(
      "Cannot connect to backend. Please make sure FastAPI is running."
    );
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(getErrorMessage(data, response.status));
  }

  return data;
}

// Register
export async function apiRegister(username, email, password) {
  return api("/auth/register", "POST", {
    username,
    email,
    password
  });
}

// Login
export async function apiLogin(username_or_email, password) {
  const data = await api("/auth/login", "POST", {
    username_or_email,
    password
  });

  localStorage.setItem("fittrack_token", data.access_token);
  localStorage.setItem("fittrack_user", JSON.stringify(data.user));

  return data;
}

// Logout
export function logout() {
  localStorage.removeItem("fittrack_token");
  localStorage.removeItem("fittrack_user");
}

// Get stored user
export function getStoredUser() {
  try {
    const user = localStorage.getItem("fittrack_user");
    return user ? JSON.parse(user) : null;
  } catch {
    return null;
  }
}
