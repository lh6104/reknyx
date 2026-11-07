/** Synthetic transport cases; actual browser acceptance is a separate suite. */
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {ApiClient, validate} from '../src/api/client';
test('runtime validation rejects fabricated success and missing fields', () => {
  assert.throws(() => validate('AsyncAccepted', {status:'success'}));
  assert.throws(() => validate('Session', {actor:{id:'local',display_name:'Fake'}}));
});
test('uncertain malformed success preserves exact replay key', async () => {
  const original = globalThis.fetch;
  const keys: string[] = [];
  globalThis.fetch = async (_path, options) => {keys.push((options!.headers as Record<string,string>)['Idempotency-Key']);return new Response('{', {status:202});};
  try {
    const client = new ApiClient();
    const request = () => client.request('/api/v1/assessments', 'AssessmentDetail', {method:'POST',body:{name:'same intent'}});
    await assert.rejects(request());
    await assert.rejects(request());
    assert.ok(keys[0]);
    assert.equal(keys[0], keys[1]);
    await assert.rejects(client.request('/api/v1/assessments','AssessmentDetail',{method:'POST',body:{name:'new intent'}}));
    assert.notEqual(keys[0],keys[2]);
  } finally {globalThis.fetch = original;}
});
test('a late response from a cleared session cannot restore credentials', async () => {
  const original = globalThis.fetch;
  let finish!: (response:Response) => void;
  globalThis.fetch = () => new Promise(resolve => {finish = resolve;});
  try {
    const client = new ApiClient();
    const pending = client.request('/api/v1/auth/me','Session');
    client.clear();
    finish(new Response(JSON.stringify({actor:{id:'00000000-0000-4000-8000-000000000003',display_name:'Old actor'},csrf_token:'x'.repeat(32),expires_at:'2026-11-07T12:00:00Z'})));
    await assert.rejects(pending, {name:'AbortError'});
    assert.equal(client.csrf,'');
  } finally {globalThis.fetch = original;}
});
test('clearing the session during file hashing prevents upload dispatch', async () => {
  const original = globalThis.fetch;
  let requests = 0;
  globalThis.fetch = async () => {requests++;return new Response('{}');};
  try {
    const client = new ApiClient();
    const form = new FormData();
    form.append('file',new Blob(['synthetic bytes']),'fixture.txt');
    const pending = client.request('/api/v1/assessments/00000000-0000-4000-8000-000000000001/imports','AsyncAccepted',{method:'POST',body:form});
    client.clear();
    await assert.rejects(pending,{name:'AbortError'});
    assert.equal(requests,0);
  } finally {globalThis.fetch = original;}
});
