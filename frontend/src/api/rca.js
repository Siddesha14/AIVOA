const API_BASE_URL = 'http://127.0.0.1:8000'

async function request(url, options = {}) {
  const response = await fetch(`${API_BASE_URL}${url}`, options)

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : `Request failed with status ${response.status}`

    throw new Error(message)
  }

  return response.json()
}

export function sendMessage(message, form) {
  return request('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, form }),
  })
}

export function uploadDoc(file, form, message = '') {
  const body = new FormData()
  body.append('file', file)
  body.append('message', message)
  body.append('form', JSON.stringify(form))

  return request('/api/chat/upload', {
    method: 'POST',
    body,
  })
}

export function saveInvestigation(form, noConfirmedRootCause, actor = 'user') {
  return request('/api/investigations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      form,
      no_confirmed_root_cause: noConfirmedRootCause,
      actor,
    }),
  })
}

export function loadInvestigation(id) {
  return request(`/api/investigations/${id}`)
}

export function reviewCause(investigationId, causeId, status, actor = 'user') {
  return request(
    `/api/investigations/${investigationId}/causes/${encodeURIComponent(causeId)}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status, actor }),
    },
  )
}