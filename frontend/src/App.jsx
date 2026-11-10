import { useEffect, useState } from 'react';

async function getJson(path, signal) {
  const response = await fetch(path, { signal });
  if (!response.ok) throw new Error('Service temporairement indisponible.');
  return response.json();
}

export function App() {
  const [state, setState] = useState({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const demo = await getJson('/api/foundation/demo', controller.signal);
        if (!demo.race_id) {
          setState({ status: 'empty' });
          return;
        }
        const race = await getJson(`/api/v1/races/${encodeURIComponent(demo.race_id)}`, controller.signal);
        setState({ status: 'ready', race });
      } catch (error) {
        if (error.name !== 'AbortError') setState({ status: 'error' });
      }
    }
    load();
    return () => controller.abort();
  }, [attempt]);
  const race = state.race;
  return <main>
    <header><a className="brand" href="/">Race<span>Atlas</span></a><span className="badge">Lot 1 · Socle technique</span></header>
    <section className="intro"><p className="eyebrow">Auvergne-Rhône-Alpes</p>
      <h1>Le début de votre prochaine course.</h1>
      <p>Le socle RaceAtlas est connecté. La carte et le calendrier arrivent dans les prochains lots.</p>
    </section>
    <section className="demo" aria-label="Démonstration du socle">
      <p className="eyebrow">Démonstration · Données synthétiques</p>
      {state.status === 'loading' && <p role="status">Chargement de la démonstration…</p>}
      {state.status === 'empty' && <><h2>Aucune épreuve de démonstration</h2><p>Le catalogue synthétique n’a pas encore été chargé.</p></>}
      {state.status === 'error' && <div role="alert"><h2>Service temporairement indisponible.</h2><p>Réessayez dans quelques instants.</p></div>}
      {race && <article>
        <p className="connection">● Épreuve lue depuis PostgreSQL</p>
        <h2>{race.name}</h2>
        <dl><div><dt>Discipline</dt><dd>{{ road: 'Route', gravel: 'Gravel', mtb: 'VTT', cyclocross: 'Cyclo-cross' }[race.discipline]}</dd></div>
          <div><dt>Date</dt><dd>{race.start_date}{race.end_date !== race.start_date ? ` → ${race.end_date}` : ''}</dd></div>
          <div><dt>Commune</dt><dd>{race.location?.commune_name ?? 'Commune inconnue'}</dd></div>
          <div><dt>Département</dt><dd>{race.department}</dd></div></dl>
        <p>{race.entry_scopes.length} liste(s) d’engagement distincte(s) · Admissibilité personnelle non évaluée</p>
      </article>}
      <button onClick={() => { setState({ status: 'loading' }); setAttempt(attempt + 1); }}>Actualiser la démonstration</button>
      <p className="note">Ces épreuves sont fictives. Aucune donnée FFC n’est collectée par cette démonstration.</p>
    </section>
    <footer>RaceAtlas · Fondation V1 · Aucune inscription proposée à ce stade.</footer>
  </main>;
}
