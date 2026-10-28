import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

const SUGGESTIONS = [
  "¿En qué categoría gasté más en los últimos 30 días?",
  "¿Cuánto ingresé y cuánto gasté este mes?",
  "¿Cuáles fueron mis cinco gastos más grandes?",
  "Quiero ahorrar 300 al mes, ¿qué ajustes podría considerar?",
];

export default function Assistant({ aiConfigured }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [sending, setSending] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(text) {
    const message = (text ?? input).trim();
    if (!message || sending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: message }]);
    setSending(true);
    try {
      const res = await api.chat(message, conversationId);
      setConversationId(res.conversation_id);
      setMessages((m) => [...m, { role: "assistant", content: res.reply, tools: res.tools_used, model: res.model }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: `Error: ${e.message}`, error: true }]);
    } finally {
      setSending(false);
    }
  }

  async function reset() {
    if (conversationId) {
      try {
        await api.resetChat(conversationId);
      } catch {
        /* la conversación ya no existe en el servidor */
      }
    }
    setConversationId(null);
    setMessages([]);
  }

  return (
    <div className="stack">
      {aiConfigured === false && (
        <div className="notice warn">
          El asistente de IA no está configurado: añade <code>ANTHROPIC_API_KEY</code> al archivo <code>.env</code> y
          reinicia el backend. Puedes seguir usando el panel y el historial.
        </div>
      )}
      <div className="card chat">
        <div className="chat-header">
          <div>
            <h2>Asistente FinanzIA</h2>
            <p className="small">
              Responde con cifras calculadas por el sistema (no por el modelo). Cada respuesta muestra qué datos consultó.
            </p>
          </div>
          <button className="btn ghost small" onClick={reset} disabled={messages.length === 0}>
            Nueva conversación
          </button>
        </div>

        <div className="chat-log" aria-live="polite">
          {messages.length === 0 && (
            <div className="suggestions">
              <p className="small">Prueba con una de estas preguntas:</p>
              {SUGGESTIONS.map((s) => (
                <button key={s} className="chip" onClick={() => send(s)} disabled={sending}>
                  {s}
                </button>
              ))}
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`bubble ${m.role} ${m.error ? "error" : ""}`}>
              <div className="bubble-text">{m.content}</div>
              {m.tools?.length > 0 && (
                <div className="tools small">
                  Datos consultados:{" "}
                  {m.tools.map((t, j) => (
                    <span key={j} className="pill tool" title={JSON.stringify(t.input)}>
                      {t.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {sending && <div className="bubble assistant small">Consultando datos…</div>}
          <div ref={endRef} />
        </div>

        <form
          className="chat-input"
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Pregunta sobre tus ingresos, gastos o hábitos de consumo…"
            aria-label="Mensaje"
            disabled={sending}
          />
          <button className="btn primary" type="submit" disabled={sending || !input.trim()}>
            Enviar
          </button>
        </form>
      </div>
    </div>
  );
}
