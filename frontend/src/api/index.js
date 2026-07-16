import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  login: (data) => api.post('/auth/login/', data),
  register: (data) => api.post('/auth/register/', data),
  logout: () => api.post('/auth/logout/'),
  me: () => api.get('/auth/me/'),
  users: () => api.get('/auth/users/'),
  changeRole: (id, role) => api.patch(`/auth/users/${id}/role/`, { role }),
}

export const ticketsApi = {
  list: (params) => api.get('/tickets/', { params }),
  get: (id) => api.get(`/tickets/${id}/`),
  create: (data) => api.post('/tickets/', data),
  update: (id, data) => api.patch(`/tickets/${id}/`, data),
  delete: (id) => api.delete(`/tickets/${id}/`),
  assign: (id, assignee_id) => api.patch(`/tickets/${id}/assign/`, { assignee_id }),
  changeStatus: (id, status) => api.patch(`/tickets/${id}/status/`, { status }),
  reanalyse: (id) => api.post(`/tickets/${id}/reanalyse/`),
  comments: {
    list: (ticketId) => api.get(`/tickets/${ticketId}/comments/`),
    create: (ticketId, body) => api.post(`/tickets/${ticketId}/comments/`, { body }),
    delete: (ticketId, commentId) => api.delete(`/tickets/${ticketId}/comments/${commentId}/`),
  },
}

export const projectsApi = {
  list: () => api.get('/projects/'),
  create: (data) => api.post('/projects/', data),
  delete: (id) => api.delete(`/projects/${id}/`),
  addMember: (id, userId) => api.post(`/projects/${id}/members/${userId}/`),
  removeMember: (id, userId) => api.delete(`/projects/${id}/members/${userId}/`),
}

export const statsApi = {
  get: () => api.get('/stats/'),
}

export const ingestApi = {
  logs: (params) => api.get('/ingest/logs/', { params }),
  send: (data, token) =>
    axios.post('/api/v1/ingest/log/', data, {
      headers: { 'X-Ingest-Token': token, 'Content-Type': 'application/json' },
    }),
}

export default api
