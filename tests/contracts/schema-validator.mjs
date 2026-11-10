// Validateur du seul sous-ensemble employé ; pas une certification JSON Schema.
import assert from 'node:assert/strict';
const supported = new Set(['$schema','$id','$ref','$defs','title','description','type','properties','required','additionalProperties','items','prefixItems','minItems','maxItems','uniqueItems','minLength','maxLength','pattern','format','minimum','maximum','enum','const','anyOf','oneOf']);
const equal = (a,b) => JSON.stringify(a) === JSON.stringify(b);
export function resolve(root, pointer) {
  assert(pointer.startsWith('#/'), 'Référence non locale interdite');
  return pointer.slice(2).split('/').reduce((v,key) => { const result=v?.[key.replaceAll('~1','/').replaceAll('~0','~')]; assert.notEqual(result,undefined,`Référence absente: ${pointer}`); return result; },root);
}
export function checkSchema(schema, root=schema) {
  if (typeof schema === 'boolean') return;
  assert(schema && typeof schema==='object' && !Array.isArray(schema));
  for (const key of Object.keys(schema)) assert(supported.has(key),`Mot-clé non pris en charge: ${key}`);
  if(schema.$ref) resolve(root,schema.$ref);
  if(schema.type) assert(['object','array','string','number','integer','boolean','null'].includes(schema.type));
  if(schema.format) assert(['date','date-time','uri'].includes(schema.format));
  if(schema.pattern) new RegExp(schema.pattern);
  for(const group of [schema.$defs,schema.properties]) for(const child of Object.values(group??{})) checkSchema(child,root);
  for(const group of [schema.anyOf,schema.oneOf,schema.prefixItems]) for(const child of group??[]) checkSchema(child,root);
  if(schema.items!==undefined) checkSchema(schema.items,root);
  if(schema.additionalProperties!==undefined) checkSchema(schema.additionalProperties,root);
}
export function valid(schema,value,root=schema) {
  if(typeof schema==='boolean') return schema;
  if(schema.$ref && !valid(resolve(root,schema.$ref),value,root)) return false;
  if(schema.anyOf && !schema.anyOf.some(s=>valid(s,value,root))) return false;
  if(schema.oneOf && schema.oneOf.filter(s=>valid(s,value,root)).length!==1) return false;
  if('const' in schema && !equal(value,schema.const)) return false;
  if(schema.enum && !schema.enum.some(v=>equal(v,value))) return false;
  if(schema.type) {
    const t=schema.type;
    if(t==='null'?value!==null:t==='array'?!Array.isArray(value):t==='object'?value===null||typeof value!=='object'||Array.isArray(value):t==='integer'?!Number.isInteger(value):typeof value!==t) return false;
  }
  if(typeof value==='number' && (!Number.isFinite(value)||value<(schema.minimum??-Infinity)||value>(schema.maximum??Infinity))) return false;
  if(typeof value==='string') {
    if([...value].length<(schema.minLength??0)||[...value].length>(schema.maxLength??Infinity)||(schema.pattern&&!new RegExp(schema.pattern).test(value))) return false;
    if(schema.format==='date' && (!/^\d{4}-\d{2}-\d{2}$/.test(value)||Number.isNaN(Date.parse(value))||new Date(value).toISOString().slice(0,10)!==value)) return false;
    if(schema.format==='date-time') {
      const parts=/^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|([+-])(\d{2}):(\d{2}))$/.exec(value);
      if(!parts||!valid({type:'string',format:'date'},parts[1])||Number(parts[2])>23||Number(parts[3])>59||Number(parts[4])>59||Number(parts[7]??0)>23||Number(parts[8]??0)>59||Number.isNaN(Date.parse(value))) return false;
    }
    if(schema.format==='uri') { try { new URL(value); } catch { return false; } }
  }
  if(Array.isArray(value)) {
    if(value.length<(schema.minItems??0)||value.length>(schema.maxItems??Infinity)) return false;
    if(schema.uniqueItems && new Set(value.map(v=>JSON.stringify(v))).size!==value.length) return false;
    const prefix=schema.prefixItems??[];
    for(let i=0;i<value.length;i++) if(!valid(i<prefix.length?prefix[i]:(schema.items??true),value[i],root)) return false;
  } else if(value && typeof value==='object') {
    if((schema.required??[]).some(k=>!Object.hasOwn(value,k))) return false;
    for(const [key,child] of Object.entries(value)) if(!valid(schema.properties?.[key]??schema.additionalProperties??true,child,root)) return false;
  }
  return true;
}
