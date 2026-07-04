// Thin fetch wrapper around the backend API. All requests go to the same origin
// under /api (Vite proxy in dev, nginx in Docker), and attach the bearer token.

const TOKEN_KEY = 'token'
const USER_KEY = 'user'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY)
  return raw ? JSON.parse(raw) : null
}

export function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  const resp = await fetch(`/api${path}`, { ...options, headers })

  if (resp.status === 401) {
    // Session expired or invalid — drop it so the app bounces to /login.
    clearSession()
    throw new ApiError('Your session has expired. Please log in again.', 401)
  }

  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`
    try {
      const body = await resp.json()
      if (body && body.detail) detail = body.detail
    } catch {
      // response had no JSON body; keep the default message
    }
    throw new ApiError(detail, resp.status)
  }

  if (resp.status === 204) return null
  return resp.json()
}

export function login(username, password) {
  return request('/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export function listBookings() {
  return request('/bookings')
}

export function createBooking(timeSlot) {
  return request('/bookings', {
    method: 'POST',
    body: JSON.stringify({ time_slot: timeSlot }),
  })
}

export function updateBooking(id, timeSlot) {
  return request(`/bookings/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ time_slot: timeSlot }),
  })
}

export function deleteBooking(id) {
  return request(`/bookings/${id}`, { method: 'DELETE' })
}
