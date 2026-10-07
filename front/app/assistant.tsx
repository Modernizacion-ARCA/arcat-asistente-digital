"use client";

import { FormEvent, useState } from "react";

type Evidence = {
  fragmento_id: number;
  documento: string;
  fuente: string;
  url: string;
};

type Answer = {
  respuesta: string;
  evidencias: Evidence[];
  modelo: string | null;
};

const suggestions = [
  "¿Qué documentación necesito para un trámite catastral?",
  "¿Dónde consulto información del Impuesto Inmobiliario?",
];

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function Assistant() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanQuestion = question.trim();
    if (!cleanQuestion || loading) return;
    setLoading(true);
    setError("");
    setAnswer(null);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/asistente/consultar/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pregunta: cleanQuestion }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "No fue posible realizar la consulta.");
      }
      setAnswer(data);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "El asistente no está disponible temporalmente.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="assistant-card" aria-labelledby="assistant-title">
      <div className="assistant-heading">
        <span className="status-dot" aria-hidden="true" />
        <div><p>Consulta pública</p><h2 id="assistant-title">¿En qué podemos ayudarte?</h2></div>
      </div>

      <form onSubmit={submit}>
        <label htmlFor="question">Escribí tu pregunta</label>
        <textarea
          id="question"
          maxLength={1000}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Por ejemplo: ¿cómo inicio un trámite de Catastro?"
          rows={4}
          value={question}
        />
        <div className="form-meta">
          <span>{question.length}/1000</span>
          <button disabled={!question.trim() || loading} type="submit">
            {loading ? "Buscando fuentes…" : "Consultar"}
            {!loading && <span aria-hidden="true">→</span>}
          </button>
        </div>
      </form>

      {!answer && !error && (
        <div className="suggestions">
          <p>También podés preguntar:</p>
          {suggestions.map((suggestion) => (
            <button key={suggestion} onClick={() => setQuestion(suggestion)} type="button">
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {error && <div className="message error" role="alert">{error}</div>}

      {answer && (
        <div className="answer" aria-live="polite">
          <p className="answer-label">Respuesta</p>
          <p>{answer.respuesta}</p>
          {answer.evidencias.length > 0 && (
            <div className="evidence">
              <h3>Fuentes consultadas</h3>
              <ol>
                {answer.evidencias.map((item) => (
                  <li key={item.fragmento_id}>
                    <a href={item.url} rel="noreferrer" target="_blank">{item.documento}</a>
                    <span>{item.fuente}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}

      <p className="privacy-note">No incluyas CUIT, claves ni información personal.</p>
    </section>
  );
}
