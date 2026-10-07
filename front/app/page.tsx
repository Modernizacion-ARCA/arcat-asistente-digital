import { Assistant } from "./assistant";

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#inicio" aria-label="Inicio ARCAT">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span><strong>ARCAT</strong><small>Catamarca</small></span>
        </a>
        <span className="service-label">Asistente digital</span>
      </header>

      <section className="hero" id="inicio">
        <div className="hero-copy">
          <p className="eyebrow">Orientación tributaria y catastral</p>
          <h1>Encontrá información pública de ARCAT con una pregunta.</h1>
          <p className="lead">
            El asistente busca en documentos registrados y muestra las fuentes utilizadas
            para que puedas verificar cada respuesta.
          </p>
          <div className="trust-list" aria-label="Características del servicio">
            <span><i aria-hidden="true">✓</i> Respuestas en español</span>
            <span><i aria-hidden="true">✓</i> Fuentes visibles</span>
            <span><i aria-hidden="true">✓</i> Sin datos sensibles</span>
          </div>
        </div>
        <Assistant />
      </section>

      <section className="info-grid" aria-label="Información importante">
        <article>
          <span className="number">01</span>
          <h2>Preguntá con claridad</h2>
          <p>Indicá el impuesto, trámite o documentación que necesitás consultar.</p>
        </article>
        <article>
          <span className="number">02</span>
          <h2>Revisá la evidencia</h2>
          <p>Cada respuesta incluye enlaces a los documentos que la respaldan.</p>
        </article>
        <article>
          <span className="number">03</span>
          <h2>Confirmá antes de actuar</h2>
          <p>Para decisiones formales, verificá siempre la vigencia en el sitio oficial.</p>
        </article>
      </section>

      <footer>
        <p>Agencia de Recaudación Catamarca</p>
        <p>Este asistente brinda orientación y no reemplaza una resolución administrativa.</p>
      </footer>
    </main>
  );
}
