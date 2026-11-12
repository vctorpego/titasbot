const API_BASE_URL = import.meta.env.VITE_API_URL || '';
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
      let message = `Erro na API: ${response.status}`;

      try {
        const errorData = await response.json();
        message = errorData?.error || errorData?.message || message;
      } catch {
        // Keep the HTTP status message when the response is not JSON.
      }

      throw new Error(message);
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
        'Resposta recebida, mas o formato não foi reconhecido pelo frontend.',
    };
  } catch (error) {
    console.error('Erro ao comunicar com o backend Python:', error);

    if (error instanceof TypeError) {
      throw new Error('Não foi possível conectar ao servidor. Verifique se o backend Python está rodando.');
    }

    if (error instanceof Error) {
      throw error;
    }

    throw new Error('Ocorreu um erro desconhecido ao comunicar com o servidor.');
  }
}
