const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, { method = 'GET', body, token } = {}) {
  let res
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    throw new ApiError(
      'Could not reach the CareConfide server. Check that the backend is running and try again.',
      0
    )
  }

  let data = null
  try {
    data = await res.json()
  } catch {
    // empty body is fine
  }

  if (!res.ok) {
    throw new ApiError(data?.detail || 'Something went wrong. Please try again.', res.status)
  }
  return data
}

export const api = {
  health: () => request('/api/health'),

  register: (payload) => request('/api/auth/register', { method: 'POST', body: payload }),
  login: (payload) => request('/api/auth/login', { method: 'POST', body: payload }),
  demoAccounts: () => request('/api/auth/demo-accounts'),

  getPatientProfile: (token) => request('/api/patient/profile', { token }),
  getPatientConsultations: (token) => request('/api/patient/consultations', { token }),
  getClinicalProfiles: (token) => request('/api/patient/clinical-profiles', { token }),
  confirmIntake: (token, payload) => request('/api/patient/intake/confirm', { method: 'POST', body: payload, token }),

  startIntake: (token, description) => request('/api/ai/intake', { method: 'POST', body: { description }, token }),
  replyIntake: (token, session_id, message) =>
    request('/api/ai/intake/reply', { method: 'POST', body: { session_id, message }, token }),
  getIntakeMessages: (token, sessionId) => request(`/api/ai/intake/${sessionId}/messages`, { token }),

  listProfessionals: (token, params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString()
    return request(`/api/professionals${qs ? `?${qs}` : ''}`, { token })
  },

  createConsultation: (token, payload) => request('/api/consultations', { method: 'POST', body: payload, token }),
  getConsultationMessages: (token, id) => request(`/api/consultations/${id}/messages`, { token }),
  postConsultationMessage: (token, id, content) =>
    request(`/api/consultations/${id}/messages`, { method: 'POST', body: { content }, token }),
  updateConsent: (token, payload) => request('/api/consultations/consent', { method: 'POST', body: payload, token }),

  getDoctorConsultations: (token) => request('/api/doctor/consultations', { token }),
  getDoctorCase: (token, id) => request(`/api/doctor/consultations/${id}`, { token }),
}

export { ApiError }
