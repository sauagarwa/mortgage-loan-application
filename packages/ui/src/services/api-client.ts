import keycloak from '../auth/keycloak';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

export async function apiFetch(
  path: string,
  options: FetchOptions = {},
): Promise<Response> {
  const { skipAuth = false, headers: customHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    ...(customHeaders as Record<string, string>),
  };

  // Inject auth token if available
  if (!skipAuth && keycloak.authenticated) {
    // Refresh token if needed
    try {
      await keycloak.updateToken(30);
    } catch {
      // Token refresh failed, continue without token
    }
    if (keycloak.token) {
      headers['Authorization'] = `Bearer ${keycloak.token}`;
    }
  }

  // Set Content-Type for JSON requests (unless it's FormData)
  if (rest.body && !(rest.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      keycloak.login();
      throw new Error('Authentication required');
    }
    const errorBody = await response.json().catch(() => null);
    throw new Error(
      errorBody?.detail || `API error: ${response.status} ${response.statusText}`,
    );
  }

  return response;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await apiFetch(path);
  return response.json();
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const response = await apiFetch(path, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  });
  return response.json();
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const response = await apiFetch(path, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
  return response.json();
}

export async function apiDelete(path: string): Promise<void> {
  await apiFetch(path, { method: 'DELETE' });
}

export async function apiUpload<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  const response = await apiFetch(path, {
    method: 'POST',
    body: formData,
  });
  return response.json();
}
