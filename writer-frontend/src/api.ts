const API_BASE = '/api'

export async function fetchSessions(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/sessions`)
  const data = await res.json()
  return data.sessions || []
}

export async function fetchHistory(sessionId: string): Promise<{role: string, content: string}[]> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`)
  const data = await res.json()
  return data.history || []
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' })
}

export async function sendMessage(message: string, sessionId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  })
  const data = await res.json()
  return data.reply
}

export function streamChat(
  message: string,
  sessionId: string,
  onChunk: (chunk: string, node: string) => void,
  onDone: () => void,
  onError: (err: string) => void,
) {
  fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  }).then(async res => {
    const reader = res.body?.getReader()
    if (!reader) return onError('No reader')
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value)
      for (const line of text.split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.done) onDone()
          else if (data.error) onError(data.error)
          else if (data.chunk) onChunk(data.chunk, data.node)
        } catch {}
      }
    }
  }).catch(e => onError(e.message))
}

export interface FileItem {
  name: string
  path: string
  type: 'file' | 'directory'
  size?: number
  children?: FileItem[]
}

export async function fetchFiles(directory: string = ''): Promise<FileItem[]> {
  const res = await fetch(`${API_BASE}/files?directory=${encodeURIComponent(directory)}`)
  const data = await res.json()
  return data.items || []
}

export async function readFile(path: string): Promise<string> {
  const res = await fetch(`${API_BASE}/files/read?path=${encodeURIComponent(path)}`)
  const data = await res.json()
  return data.content || ''
}
