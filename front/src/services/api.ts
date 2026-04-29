const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const SESSION_KEY = 'titasbot_session_id';

export interface ChatResponse {
  text: string;
  sources?: string[];
}

function getSessionId(): string | null {
  try {
    return localStorage.getItem(SESSION_KEY);
  } catch {
    return null;
  }
}

function setSessionId(sessionId: string): void {
  try {
    localStorage.setItem(SESSION_KEY, sessionId);
  } catch {
    // ignore localStorage issues
  }
}

export function resetBackendSession(): void {
  try {
    localStorage.removeItem(SESSION_KEY);
  } catch {
    // ignore localStorage issues
  }
}

export async function sendMessageToBackend(message: string): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: message,
        session_id: getSessionId(),
      }),
    });

    if (!response.ok) {
      throw new Error(`Erro na API: ${response.status}`);
    }

    const data = await response.json();

    if (data?.session_id) {
      setSessionId(String(data.session_id));
    }

    return {
      text:
        data.answer ||
        data.reply ||
        data.response ||
        data.text ||
        data.resposta ||
        'Resposta recebida, mas o formato nao foi reconhecido pelo frontend.',
    };
  } catch (error) {
    console.error('Erro ao comunicar com o backend Python:', error);
    throw new Error('Nao foi possivel conectar ao servidor. Verifique se o backend Python esta rodando.');
  }
}
