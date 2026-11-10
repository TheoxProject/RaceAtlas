// Oracle de conception local ; jamais un module applicatif ou importeur.
import assert from 'node:assert/strict';
const aura=new Set(['01','03','07','15','26','38','42','43','63','69','73','74']);
const compatible={road:['road_race','time_trial'],gravel:['gravel_race'],mtb:['xco','enduro','downhill'],cyclocross:['cyclocross']};
const normalize=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
const coordinates=r=>Array.isArray(r.location?.coordinates);
const day=d=>Date.parse(d)/86400000;
export function assertCatalog(c) {
  const ids=new Set(),sources=new Set(),cats=new Set(c.categories.map(v=>v.code));
  const add=id=>{assert(!ids.has(id),`Identifiant dupliqué: ${id}`);ids.add(id);};
  assert.equal(cats.size,c.categories.length,'Catégorie dupliquée');
  for(const r of c.races) {
    add(r.id);assert(r.start_date<=r.end_date,'Intervalle inversé');assert(aura.has(r.department),'Hors région');
    assert(r.types.every(t=>compatible[r.discipline]?.includes(t)),'Type incompatible');
    if(r.location) assert.equal(r.department,r.location.department);
    const key=[r.source.provider,r.source.source_season,r.source.race_number].join('/');assert(!sources.has(key),'Clé source dupliquée');sources.add(key);
    if(c.synthetic) {assert.equal(r.source.provider,'synthetic');assert.equal(new URL(r.source.source_url).hostname,'example.invalid');if(r.location)assert.equal(r.location.provenance,'synthetic');}
    for(const s of r.entry_scopes) {
      add(s.id);
      if(s.identity_status==='verified'&&s.kind==='entry_list')assert(s.source_list_id,'Liste vérifiée sans ID source');
      if(s.eligibility_status!=='confirmed')assert.equal(s.rules.length,0,'Catégories non confirmées');else assert(s.rules.length>0,'Confirmation vide');
      for(const rule of s.rules) {add(rule.id);assert(rule.category_codes.every(v=>cats.has(v)),'Catégorie sans référence');const x=rule.restrictions;
        if(x.min_age!==null&&x.max_age!==null)assert(x.min_age<=x.max_age,'Âge inversé');
        if(x.age_reference==='season_end')assert.notEqual(x.age_season,null,'Saison âge absente');
        if(x.age_reference==='event_date')assert.equal(x.age_season,null,'Saison superflue');
      }
    }
  }
  const cov=c.coverage;
  for(const w of cov.windows) {
    const dates=[w.requested_from,w.requested_to,w.effective_from,w.effective_to].map(day);
    const invalidInterval=dates.some(d=>!Number.isFinite(d))||dates[1]<dates[0]||dates[3]<dates[2]||dates[1]-dates[0]>=14||dates[3]-dates[2]>=14;
    const divergence=invalidInterval||w.requested_from!==w.effective_from||w.requested_to!==w.effective_to||w.requested_department!==w.effective_department||w.displayed_count!==w.distinct_keys;
    if(divergence) assert.equal(w.status,'incomplete','Divergence de fenêtre sans statut incomplete');
    if(w.status==='incomplete') assert.equal(cov.status,'incomplete','Fenêtre incomplète sans couverture globale incomplete');
  }
  if(cov.status==='consistent_sample') assert(cov.windows.length>0&&cov.windows.every(w=>w.status==='consistent_sample'),'Échantillon cohérent non établi');
  if(cov.status==='complete') {
    assert(cov.requested_from&&cov.requested_to&&cov.requested_from<=cov.requested_to&&cov.departments.length,'Périmètre absent');
    for(const dep of cov.departments) {
      const covered=new Set();
      for(const w of cov.windows.filter(w=>w.requested_department===dep)) {
        assert.equal(w.status,'consistent_sample');
        for(let d=day(w.requested_from);d<=day(w.requested_to);d++)covered.add(d);
      }
      for(let d=day(cov.requested_from);d<=day(cov.requested_to);d++)assert(covered.has(d),'Trou de couverture');
    }
  }
}
export function matchingScopes(r,f) {
  if(!f.categories.length)return r.entry_scopes.map(s=>s.id);
  return r.entry_scopes.filter(s=>{if(s.eligibility_status!=='confirmed')return false;const accepted=new Set(s.rules.flatMap(v=>v.category_codes));return f.category_operator==='and'?f.categories.every(v=>accepted.has(v)):f.categories.some(v=>accepted.has(v));}).map(s=>s.id);
}
function distance(a,b) {const rad=x=>x*Math.PI/180;const h=Math.sin(rad(b[1]-a[1])/2)**2+Math.cos(rad(a[1]))*Math.cos(rad(b[1]))*Math.sin(rad(b[0]-a[0])/2)**2;return 6371.0088*2*Math.asin(Math.sqrt(Math.min(1,Math.max(0,h))));}
export function select(c,f) {
  assert(f.from<=f.to,'Filtre dates inversé');
  const candidates=c.races.filter(r=>aura.has(r.department)&&r.start_date<=f.to&&r.end_date>=f.from&&(!f.disciplines.length||f.disciplines.includes(r.discipline))&&(!f.types.length||r.types.some(t=>f.types.includes(t)))&&matchingScopes(r,f).length&&normalize([r.name,r.location?.commune_name??'',r.organizer].join(' ')).includes(normalize(f.query)));
  const g=f.geography,pre=g.mode==='departments'?candidates.filter(r=>g.departments.includes(r.department)):candidates;
  const unlocated=pre.filter(r=>!coordinates(r));
  const matched=g.mode==='radius'?pre.filter(r=>coordinates(r)&&distance(g.center,r.location.coordinates)<=g.radius_km):pre;
  return {matched:matched.toSorted((a,b)=>a.start_date.localeCompare(b.start_date)||a.id.localeCompare(b.id)),unlocated};
}
export function project(c,f) {
  const {matched,unlocated}=select(c,f), common={contract_version:'1.0.0',catalog_version:c.catalog_version,total:matched.length,next_cursor:null,coverage:c.coverage};
  const page={...common,items:matched.map(race=>({race,matching_scope_ids:matchingScopes(race,f)})),unlocated_count:unlocated.length};
  const map={...common,type:'FeatureCollection',features:matched.filter(coordinates).map(r=>({type:'Feature',id:r.id,geometry:{type:'Point',coordinates:r.location.coordinates},properties:{race_id:r.id,commune_id:r.location.commune_id,discipline:r.discipline,matching_scope_ids:matchingScopes(r,f)}})),unlocated_ids:unlocated.map(r=>r.id)};
  return {page,map};
}
