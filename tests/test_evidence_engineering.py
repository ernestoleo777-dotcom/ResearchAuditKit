# SPDX-License-Identifier: Apache-2.0
import json,hashlib,os
from pathlib import Path
from dataclasses import replace
from contextlib import contextmanager
from test_evidence_graph_b1 import fixture,node,edge,save,codes
from research_audit_kit.evidence import run,Limits
from research_audit_kit.evidence import fs,core

def test_current_typed_reference_to_superseded_artifact_is_reported(tmp_path):
    path,g,n=fixture(tmp_path)
    newer=dict(n['artifact'],version='2',id=n['artifact']['logical_id']+'@2')
    g['nodes'].append(newer)
    g['edges']=[e for e in g['edges'] if e['target']!=n['artifact']['id']]
    g['edges'].append(edge('SUPERSEDES',newer,n['artifact'],'replace-artifact'))
    save(path,g)
    assert 'STALE_CURRENT_REFERENCE' in codes(run(path,'doctor'))

def test_failed_read_consumes_actual_aggregate_budget(tmp_path,monkeypatch):
    for name in ['a.bin','b.bin']:(tmp_path/name).write_bytes(b'a'*80)
    nodes=[node('Artifact',name,path=name,media_type='application/octet-stream',sha256=hashlib.sha256(b'a'*80).hexdigest()) for name in ['a.bin','b.bin']]
    path=tmp_path/'graph.json';save(path,{'schema':core.SCHEMA,'nodes':nodes,'edges':[]})
    ino=(tmp_path/'a.bin').stat().st_ino;artifact_inodes={ino,(tmp_path/'b.bin').stat().st_ino};original=fs.os.read;spent=0;mutated=False
    def racing(fd,count):
        nonlocal spent,mutated
        identity=os.fstat(fd).st_ino;value=original(fd,count)
        if identity in artifact_inodes:spent+=len(value)
        if identity==ino and value and not mutated:
            with (tmp_path/'a.bin').open('ab') as f:f.write(b'!')
            mutated=True
        return value
    monkeypatch.setattr(fs.os,'read',racing)
    result=run(path,'doctor',limits=replace(Limits(),artifact_bytes=80,total_artifact_bytes=80))
    assert spent<=80
    assert 'TOTAL_ARTIFACT_BUDGET_EXCEEDED' in codes(result)
    assert all(x['path']!='b.bin' or x['status']!='MECHANICALLY_VERIFIED' for x in result['artifact_observations'])

def test_leaf_mount_escape_rejected_before_open(tmp_path,monkeypatch):
    path,g,n=fixture(tmp_path);ino=(tmp_path/'artifact.txt').stat().st_ino
    stat_fn,fstat_fn,open_fn=fs.os.stat,fs.os.fstat,fs.os.open;opened=[]
    class Proxy:
        def __init__(self,s):self.s=s;self.st_dev=s.st_dev+1
        def __getattr__(self,k):return getattr(self.s,k)
    def st(name,*a,**kw):
        s=stat_fn(name,*a,**kw);return Proxy(s) if s.st_ino==ino else s
    def fst(fd):
        s=fstat_fn(fd);return Proxy(s) if s.st_ino==ino else s
    def op(name,*a,**kw):opened.append(str(name));return open_fn(name,*a,**kw)
    monkeypatch.setattr(fs.os,'stat',st);monkeypatch.setattr(fs.os,'fstat',fst);monkeypatch.setattr(fs.os,'open',op)
    assert 'MOUNT_ESCAPE' in codes(run(path,'doctor'))
    assert 'artifact.txt' not in opened

def test_no_download_guard_precedes_root_resolution(tmp_path,monkeypatch):
    path,g,n=fixture(tmp_path);active=False;original=fs._open_absolute
    @contextmanager
    def guard():
        nonlocal active
        active=True
        try:yield
        finally:active=False
    def root(p):assert active;return original(p)
    monkeypatch.setattr(core,'no_download',guard);monkeypatch.setattr(fs,'_open_absolute',root)
    assert run(path)['status']=='PASS'

def test_guard_restore_failure_is_explicit_and_does_not_publish(tmp_path,monkeypatch):
    path,g,n=fixture(tmp_path)
    class Function:
        def __init__(self,f):self.f=f
        def __call__(self,*a):return self.f(*a)
    class Policy:
        def __init__(self):self.value=0;self.getiopolicy_np=Function(lambda *a:self.value);self.setiopolicy_np=Function(self.set)
        def set(self,kind,scope,value):
            if value==0:return -1
            self.value=value;return 0
    policy=Policy();monkeypatch.setattr(fs.sys,'platform','darwin');monkeypatch.setattr(fs.ctypes,'CDLL',lambda *a,**kw:policy)
    result=run(path,output='new_report.json')
    assert 'NO_DOWNLOAD_RESTORE_FAILED' in codes(result)
    assert result['status']=='UNRESOLVED'
    assert not (tmp_path/'new_report.json').exists()
