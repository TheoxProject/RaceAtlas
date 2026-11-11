import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve as pathResolve,dirname} from 'node:path';
import {checkSchema,valid,resolve} from './schema-validator.mjs';
import {assertCatalog,matchingScopes,select,project} from './reference-model.mjs';
const root=pathResolve(dirname(fileURLToPath(import.meta.url)),'../..');
const read=name=>JSON.parse(readFileSync(pathResolve(root,name),'utf8'));
const schema=read('contracts/catalog.schema.json'),catalog=read('fixtures/catalog.v1.json');
const scenarios=read('fixtures/scenarios.v1.json').scenarios;
const api=read('contracts/openapi.json'),revisions=read('fixtures/identity-revisions.v1.json');
const clone=v=>JSON.parse(JSON.stringify(v));
const sorted=v=>[...v].sort();
const check=(name,value)=>valid(schema.$defs[name],value,schema);
const mutate=change=>{const c=clone(catalog);change(c);return c;};

test('Schéma strict : références locales et mots-clés effectivement supportés',()=>{
  checkSchema(schema);
  assert.throws(()=>checkSchema({type:'object',unevaluatedProperties:false}),/non pris en charge/);
  assert.throws(()=>checkSchema({$ref:'#/$defs/missing',$defs:{}}),/Référence absente/);
  assert.throws(()=>checkSchema({format:'email'}));
});
test('Catalogue synthétique conforme au schéma et aux invariants',()=>{
  assert(valid(schema,catalog));assertCatalog(catalog);assert.equal(catalog.synthetic,true);
  assert.equal(catalog.coverage.status,'unknown');
});
test('Schéma rejette champs manquants/superflus, coordonnées invalides, fausse date et enum',()=>{
  for(const change of [c=>delete c.races[0].id,c=>c.races[0].unexpected=true,c=>c.races[0].location.coordinates=[181,45],c=>c.races[0].location.coordinates=[4,91],c=>c.races[0].location.coordinates=[4,45,12],c=>c.races[0].start_date='2026-02-30',c=>c.races[0].source.checked_at='2026-02-30T09:00:00Z',c=>c.races[0].discipline='time_trial',c=>c.races[0].entry_scopes[0].rules[0].category_codes=['open_1','open_1']]) assert.equal(valid(schema,mutate(change)),false);
});
test('IDs UUID, catégories extensibles et valeurs sources inconnues admis sans invention',()=>{
  const c=mutate(c=>{c.races[0].id='12345678-1234-4123-8123-123456789abc';c.races[0].organizer=null;c.races[0].types=[];c.categories.push({code:'u15',label:'U15'});c.races[0].entry_scopes[0].rules[0].category_codes=['u15'];});
  assert(valid(schema,c));assertCatalog(c);
});
test('Invariants rejettent identités/clefs dupliquées, référence absente et CLM hors Route',()=>{
  for(const change of [c=>c.races[1].id=c.races[0].id,c=>c.races[1].entry_scopes[0].id=c.races[0].entry_scopes[0].id,c=>c.races[1].source=c.races[0].source,c=>c.races[0].entry_scopes[0].rules[0].category_codes=['u15'],c=>c.races[0].discipline='mtb',c=>c.races[0].end_date='2026-01-01',c=>c.races[0].department='75',c=>c.races[0].entry_scopes[0].eligibility_status='ambiguous',c=>c.races[0].entry_scopes[0].identity_status='verified']) assert.throws(()=>assertCatalog(mutate(change)));
});
for(const scenario of scenarios) test(`Scénario figé : ${scenario.id}`,()=>{
  assert(check('Filter',scenario.filter));
  const {matched,unlocated}=select(catalog,scenario.filter);
  assert.deepEqual(sorted(matched.map(r=>r.id)),sorted(scenario.expected_ids));
  assert.deepEqual(sorted(unlocated.map(r=>r.id)),sorted(scenario.expected_unlocated_ids));
});
test('ET ne combine ni listes indépendantes ni courses de la même manifestation',()=>{
  const f=scenarios.find(s=>s.id==='and-same-scope').filter;
  for(const id of ['race-road-split','race-other-one','race-other-two']) assert.deepEqual(matchingScopes(catalog.races.find(r=>r.id===id),f),[]);
  assert.deepEqual(matchingScopes(catalog.races[0],f),['scope-road-combined']);
});
test('Restrictions corrélées non aplaties et aucune éligibilité personnelle inventée',()=>{
  const f=scenarios.find(s=>s.id==='and-same-scope').filter;
  const item=project(catalog,f).page.items.find(v=>v.race.id==='race-correlated');
  assert.deepEqual(item.matching_scope_ids,['scope-correlated']);
  const rules=item.race.entry_scopes[0].rules;
  assert.deepEqual(rules.map(r=>[r.category_codes,r.restrictions.sex]),[[['open_1'],'men'],[['open_2'],'women']]);
  assert.equal(item.race.personal_eligibility,'not_evaluated');
  const cx=catalog.races.find(r=>r.id==='race-cross-restricted');
  assert.equal(cx.source.source_season,2027);assert(cx.start_date.startsWith('2026'));
  assert.equal(cx.entry_scopes[0].rules[0].restrictions.age_season,2027);
  assert.throws(()=>assertCatalog(mutate(c=>c.races[4].entry_scopes[0].rules[0].restrictions.age_season=null)));
});
test('Projections carte/catalogue cohérentes, marqueurs uniquement au centre sourcé',()=>{
  for(const s of scenarios){const {page,map}=project(catalog,s.filter);assert(check('RacePage',page));assert(check('MapPage',map));assert.equal(page.total,map.total);
    const located=page.items.filter(v=>v.race.location?.coordinates).map(v=>v.race.id);
    assert.deepEqual(sorted(map.features.map(v=>v.id)),sorted(located));
    assert.equal(page.unlocated_count,map.unlocated_ids.length);
    for(const feature of map.features){const r=catalog.races.find(r=>r.id===feature.id);assert.deepEqual(feature.geometry.coordinates,r.location.coordinates);assert.equal(r.location.precision,'commune_center');}
  }
});
test('Rayon exclut la candidate non localisée du total confirmé sans la perdre',()=>{
  const s=scenarios.find(s=>s.id==='radius-unlocated'),{page,map}=project(catalog,s.filter);
  assert(!page.items.some(v=>v.race.id==='race-unlocated'));assert(map.unlocated_ids.includes('race-unlocated'));
  const far={...s.filter,geography:{mode:'radius',center:[5.9,46.5],radius_km:1}};
  assert.equal(select(catalog,far).matched.length,0);
});
test('Exemple GeoJSON figé utilisable directement par la première carte',()=>{
  const example=read('fixtures/map.v1.json');assert(check('MapPage',example));
  assert.deepEqual(example,project(catalog,scenarios[0].filter).map);
  assert.equal(example.features.length,11);assert.equal(example.total,12);
  assert.deepEqual(example.unlocated_ids,['race-unlocated']);
});
test('Renommage/report/regroupement préservent ID épreuve, liste et favori',()=>{
  assert(check('Race',revisions.before));assert(check('Race',revisions.after));
  assert.equal(revisions.before.id,revisions.after.id);
  assert.notEqual(revisions.before.name,revisions.after.name);assert.notEqual(revisions.before.start_date,revisions.after.start_date);assert.notEqual(revisions.before.competition_id,revisions.after.competition_id);
  assert.equal(revisions.saved_scope_id,revisions.after.entry_scopes[0].id);
  assert.equal(revisions.before.source.race_number,revisions.after.source.race_number);
});
test('Disparition et annulation restent indépendantes',()=>{
  const missing=catalog.races.find(r=>r.id==='race-missing');assert.equal(missing.status,'scheduled');assert.equal(missing.source_presence,'to_verify');
  const cancelled=mutate(c=>c.races.find(r=>r.id==='race-cancelled').source_presence='missing');assertCatalog(cancelled);assert.equal(cancelled.races.find(r=>r.id==='race-cancelled').status,'cancelled');
});
test('Couverture : une fenêtre mal appliquée ou un trou interdit complete',()=>{
  assert.throws(()=>assertCatalog(mutate(c=>c.coverage.status='complete')));
  const c=mutate(c=>Object.assign(c.coverage,{status:'complete',requested_from:'2026-11-10',requested_to:'2026-11-11',departments:['26'],windows:[{requested_from:'2026-11-10',requested_to:'2026-11-11',effective_from:'2026-11-10',effective_to:'2026-11-11',requested_department:'26',effective_department:'26',displayed_count:9,distinct_keys:9,status:'consistent_sample',reason:null}]}));
  assert(valid(schema,c));assertCatalog(c);
  for(const change of [c=>c.coverage.windows[0].effective_to='2026-11-10',c=>c.coverage.windows[0].distinct_keys=8,c=>c.coverage.requested_to='2026-11-12',c=>c.coverage.windows[0].effective_department='69']){const bad=clone(c);change(bad);assert.throws(()=>assertCatalog(bad));}
});
test('Filtres invalides rejetés : modes géographiques simultanés, rayon et dates',()=>{
  const f=clone(scenarios[0].filter);f.geography={mode:'departments',departments:['26'],radius_km:10};assert(!check('Filter',f));
  f.geography={mode:'departments',departments:['75']};assert(!check('Filter',f));
  f.geography={mode:'radius',center:[4,45],radius_km:0};assert(!check('Filter',f));
  f.geography={mode:'all'};f.from='2027-01-01';assert.throws(()=>select(catalog,f));
});
test('Régression : divergences de fenêtre rejetées même hors couverture complete',()=>{
  const window={requested_from:'2026-11-10',requested_to:'2026-11-23',effective_from:'2026-11-10',effective_to:'2026-11-23',requested_department:'26',effective_department:'26',displayed_count:9,distinct_keys:9,status:'consistent_sample',reason:null};
  const make=(status='consistent_sample')=>mutate(c=>Object.assign(c.coverage,{status,windows:[clone(window)]}));
  assertCatalog(make());
  for(const change of [w=>w.effective_to='2026-11-10',w=>w.effective_from='2026-11-11',w=>w.effective_department='69',w=>w.effective_department=null,w=>w.distinct_keys=8,w=>w.requested_to='2026-11-09',w=>w.effective_to='2026-11-09',w=>{w.requested_to='2026-11-24';w.effective_to='2026-11-24';}]) {
    for(const global of ['unknown','consistent_sample','incomplete','complete']) {
      const bad=make(global);change(bad.coverage.windows[0]);assert(valid(schema,bad));
      assert.throws(()=>assertCatalog(bad),/Divergence de fenêtre/);
      bad.coverage.windows[0].status='incomplete';bad.coverage.windows[0].reason='Divergence observée';
      if(global==='incomplete') assertCatalog(bad);else assert.throws(()=>assertCatalog(bad),/couverture globale incomplete/);
    }
  }
  assert.throws(()=>assertCatalog(mutate(c=>c.coverage.status='consistent_sample')),/non établi/);
  const unknown=make('unknown');unknown.coverage.windows[0].status='unknown';assertCatalog(unknown);
  unknown.coverage.status='consistent_sample';assert.throws(()=>assertCatalog(unknown),/non établi/);
});
test('Régression : date-time borne heures, minutes, secondes et décalage',()=>{
  const format={type:'string',format:'date-time'};
  for(const invalid of ['2026-11-10T24:00:00Z','2026-11-10T23:60:00Z','2026-11-10T23:59:60Z','2026-11-10T00:00:00+24:00','2026-11-10T00:00:00-24:00','2026-11-10T00:00:00+02:60','2026-02-30T00:00:00Z','2026-11-10t00:00:00z']) assert.equal(valid(format,invalid),false,invalid);
  for(const accepted of ['2026-11-10T00:00:00Z','2026-11-10T23:59:59Z','2026-11-10T00:00:00+02:00','2026-11-10T00:00:00-05:30','2026-11-10T00:00:00.123+00:00']) assert.equal(valid(format,accepted),true,accepted);
  const bad=mutate(c=>c.races[0].source.checked_at='2026-11-10T24:00:00Z');assert.equal(valid(schema,bad),false);
});
test('OpenAPI 3.1 : toutes références résolues localement et filtre commun',()=>{
  assert.equal(api.openapi,'3.1.0');
  const walk=v=>{if(!v||typeof v!=='object')return;if(v.$ref){if(v.$ref.startsWith('#/'))resolve(api,v.$ref);else{if(v.$ref === './catalog-options.schema.json'){checkSchema(read('contracts/catalog-options.schema.json'));}else{assert(v.$ref.startsWith('./catalog.schema.json#/'));resolve(schema,v.$ref.slice('./catalog.schema.json'.length));}}}for(const child of Object.values(v))walk(child);};walk(api);
  assert.deepEqual(api.paths['/api/v1/map'].get.parameters,api.paths['/api/v1/races'].get.parameters);
  assert.equal(api.paths['/api/v1/races/{race_id}'].get.parameters[0].name,'race_id');
});
