import {test} from 'node:test';
import assert from 'node:assert/strict';
import {parsePreferences,DEFAULT_API_PREFERENCES} from '../src/components/api-settings';

test('browser preferences normalize ports and exclude unknown stored fields',()=>{
 assert.deepEqual(parsePreferences({...DEFAULT_API_PREFERENCES,ports:'0443, 80',actor:'untrusted'}),{includeSuspected:true,ports:'443, 80',theme:'system'});
});
test('invalid persisted settings cannot become form defaults',()=>{
 for(const change of [{ports:'0'},{ports:'65536'},{ports:'80,080'},{ports:'1e2'},{theme:['dark']},{theme:'other'},{includeSuspected:'false'}])assert.throws(()=>parsePreferences({...DEFAULT_API_PREFERENCES,...change}));
});
