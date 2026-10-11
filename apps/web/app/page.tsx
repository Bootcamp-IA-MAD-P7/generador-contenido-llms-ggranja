import Link from "next/link";
import styles from "./landing.module.css";

const steps = [
  { n: "1", title: "Cuéntanos tu idea", text: "Responde unas preguntas sencillas: qué quieres conseguir, a quién le hablas y dónde se publicará." },
  { n: "2", title: "Revisas y decides", text: "El borrador llega a tu revisión con el enfoque propuesto. Tú lo editas, lo apruebas o pides cambios." },
  { n: "3", title: "Planificas el mes", text: "Reparte las publicaciones por día y comprueba el balance entre contenido educativo, comunidad y marca." },
];

export default function Home() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <p className={styles.wordmark}>estudio.</p>
        <Link href="/login" className={styles.ghost}>Iniciar sesión</Link>
      </header>

      <main id="main-content">
        <section className={styles.hero} aria-labelledby="hero-title">
          <p className={styles.kicker}>Contenido para redes, con revisión humana</p>
          <h1 id="hero-title" className={styles.title}>¿Qué historia contamos hoy?</h1>
          <p className={styles.lede}>
            Prepara publicaciones para Instagram y Facebook, revísalas con calma y planifica tu mes. Nada se publica sin tu aprobación.
          </p>
          <div className={styles.actions}>
            <Link href="/login" className={styles.primary}>Iniciar sesión</Link>
          </div>
        </section>

        <section className={styles.steps} aria-labelledby="steps-title">
          <h2 id="steps-title" className={styles.stepsTitle}>Así se trabaja</h2>
          <ol className={styles.stepList}>
            {steps.map((step) => (
              <li key={step.n} className={styles.step}>
                <span className={styles.stepNum} aria-hidden="true">{step.n}</span>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className={styles.footer}>Prototipo local · datos de ejemplo · no se publica nada</footer>
    </div>
  );
}
