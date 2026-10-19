// Exercise the page handlers with a DOM fixture; this is not browser layout QA.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const buttons = {filter: [], add: [], remove: []};
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {
    textContent: '', classList: {add(){}, remove(){}, toggle(){}},
    set innerHTML(value) {
      this.html = value;
      const kind = {'#filters':'filter','#place-results':'add','#selected-list':'remove'}[id];
      if (kind) buttons[kind] = [...value.matchAll(new RegExp(`data-${kind}="([^"]+)"`, 'g'))].map(m => ({
        dataset: {[kind]:m[1]}, classList:{toggle(){}}, setAttribute(key,value){this[key]=value;}
      }));
    }, get innerHTML(){return this.html || '';}
  });
  return elements.get(id);
}
const storage = new Map();
const context = vm.createContext({window:{}, console, setTimeout, clearTimeout,
  document:{body:{dataset:{page:'fixture'}}, querySelector:element, getElementById:()=>null,
    querySelectorAll:s=>buttons[/\[data-(.+)\]/.exec(s)?.[1]] || []},
  sessionStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},
  location:{replace:url=>{context.redirect=url;}}
});
const put=(key,value)=>storage.set(key,JSON.stringify(value));
put('rw_trip',{city:'Cambridge',days:2,pace:'balanced',interests:['History','Museums','Food','Nature']});
const data={results:[
  {place_id:'museum',name:'Museum fixture',city:'Cambridge',category:'culture',score:.8,matched_interests:['History','Museums']},
  {place_id:'cafe',name:'Cafe fixture',city:'Cambridge',category:'food',score:.7,matched_interests:['Food']}
],model:{model:'fixture'},trace:[],prompt_version:'rag-planner-v2'};
put('rw_recommendations',data);
put('rw_selected',['cafe']);
vm.runInContext(fs.readFileSync('frontend/planner-app.js','utf8'),context);
vm.runInContext('recommendations()',context);
assert.deepEqual(buttons.filter.map(b=>b.dataset.filter),['all','History','Museums','Food','Nature']);
assert.match(element('#filters').innerHTML,/Museums \(1\)/);
assert.match(element('#filters').innerHTML,/Nature \(0\)/);
buttons.filter.find(b=>b.dataset.filter==='Museums').onclick();
assert.match(element('#place-results').innerHTML,/Museum fixture/);
assert.doesNotMatch(element('#place-results').innerHTML,/Cafe fixture/);
assert.match(element('#place-results').innerHTML,/Matches: History · Museums/);
assert.deepEqual(JSON.parse(storage.get('rw_selected')),['cafe']);
buttons.filter.find(b=>b.dataset.filter==='Nature').onclick();
assert.match(element('#place-results').innerHTML,/No places matched this interest/);
assert.equal(buttons.filter.find(b=>b.dataset.filter==='Nature')['aria-pressed'],'true');
data.results.forEach(p=>delete p.matched_interests);
put('rw_recommendations',data);
vm.runInContext('recommendations()',context);
assert.equal(context.redirect,'generating.html?stage=recommend');
console.log('Passed: matching labels/counts, overlapping interests, selection retention, empty results, old-cache refresh.');
