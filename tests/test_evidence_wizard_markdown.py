from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from research_audit_kit.evidence import fs, run
from research_audit_kit.evidence.initialize import initialize
from research_audit_kit.evidence.wizard import wizard
from research_audit_kit.evidence.markdown import render_markdown


def answers(values):
    iterator = iter(values)
    def ask(prompt):
        try:
            return next(iterator)
        except StopIteration:
            raise EOFError
    return ask


def test_wizard_authors_only_confirmed_declarations_without_reads(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('wizard must not open asset contents')
    monkeypatch.setattr(fs.Root, 'read', forbidden)
    preview = []
    result = wizard(root=tmp_path, ask=answers([
        'result', 'results.csv', '', 'main', 'Explicit claim', 'result', '', '', 'yes']), show=preview.append)
    assert result['status'] == 'PASS' and result['output_created']
    manifest = json.loads((tmp_path/'assets.json').read_text())
    assert manifest['claims'][0]['supports'] == ['result']
    assert manifest['claims'][0]['contradicts'] == []
    assert 'Explicit claim' in '\n'.join(preview)
    assert manifest['assets'] == [{'name':'result','path':'results.csv'}]
    assert not (tmp_path/'results.csv').exists()


@pytest.mark.parametrize('values', [[], ['r','r.txt','','','no'],
    ['r','../outside','','','yes'], ['r','r.txt','','c','claim','unknown','','','yes']])
def test_cancel_and_invalid_input_publish_nothing(tmp_path, values):
    result = wizard(root=tmp_path, ask=answers(values), show=lambda x: None)
    assert result['status'] != 'PASS' and not result['output_created']
    assert list(tmp_path.iterdir()) == []


def test_wizard_protects_inputs_and_existing_outputs(tmp_path):
    for output in ['r.txt','assets.json']:
        if output == 'assets.json':
            (tmp_path/output).write_bytes(b'old')
        result = wizard(root=tmp_path, output=output, ask=answers(['r','r.txt','','','yes']), show=lambda x:None)
        assert result['status'] == 'INVALID'
    assert (tmp_path/'assets.json').read_bytes() == b'old'
    assert not (tmp_path/'r.txt').exists()


def test_wizard_no_publish_on_policy_restore_failure(tmp_path, monkeypatch):
    from contextlib import contextmanager
    @contextmanager
    def broken():
        yield
        raise fs.EvidenceError('POLICY_RESTORE_FAILED')
    monkeypatch.setattr('research_audit_kit.evidence.wizard.no_download', broken)
    result=wizard(root=tmp_path, ask=answers(['r','r.txt','','','yes']), show=lambda x:None)
    assert result['status']=='INVALID' and list(tmp_path.iterdir())==[]


def test_installed_style_cli_wizard_stdout_is_json(tmp_path):
    result=subprocess.run([sys.executable,'-m','research_audit_kit','evidence','wizard','--root',str(tmp_path),'--format','json'],
        input='r\nr.txt\n\n\nyes\n', text=True,capture_output=True,env=os.environ.copy(),timeout=30)
    assert result.returncode==0, result.stdout+result.stderr
    assert json.loads(result.stdout)['output_created']
    assert 'Preview' in result.stderr


def test_markdown_check_keeps_json_exit_and_escapes_user_text(tmp_path):
    name = '<img src=x onerror=alert(1)>[link](https:evil)|`\u202e'
    (tmp_path/'result.txt').write_bytes(b'first')
    manifest={'schema':'researchauditkit.asset-list/v1','assets':[{'name':'r','path':'result.txt'}],
              'claims':[{'name':'main','statement':name,'supports':['r']}]}
    (tmp_path/'assets.json').write_text(json.dumps(manifest))
    init=initialize(tmp_path/'assets.json',output='graph.json')
    (tmp_path/'result.txt').write_bytes(b'changed')
    report=run(tmp_path/'graph.json','check',expected_graph_sha256=init['graph_content_sha256'],
               allow_unresolved_claims=('urn:rak:project:claim:main@1',))
    report['evidence_result']['artifact_observations'][0]['path']=name
    md=render_markdown(report)
    assert 'Mechanical gate: **FAIL**' in md
    assert 'Declared path:' in md and 'urn:rak:project:claim:main@1' in md
    assert '<img' not in md and '[link]' not in md and '\u202e' not in md
    assert '&lt;img' in md and '&#124;' in md and '&#96;' in md
    assert len(md.splitlines())<=400


def test_markdown_cli_out_stays_canonical_json(tmp_path):
    (tmp_path/'assets.json').write_text(json.dumps({'schema':'researchauditkit.asset-list/v1',
       'assets':[{'name':'r','path':'r.txt'}]}))
    (tmp_path/'r.txt').write_bytes(b'data')
    init=initialize(tmp_path/'assets.json',output='graph.json')
    result=subprocess.run([sys.executable,'-m','research_audit_kit','evidence','check',str(tmp_path/'graph.json'),
        '--graph-sha256',init['graph_content_sha256'],'--format','markdown','--out','check.json'],
        text=True,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr
    assert 'Mechanical gate: **PASS**' in result.stdout
    assert json.loads((tmp_path/'check.json').read_text())['mechanical_gate']=='PASS'


def test_guided_release_demo_replays_complete_cli():
    script = Path(__file__).resolve().parents[1]/'examples/evidence_graph_demo/run_guided_demo.py'
    done = subprocess.run([sys.executable,str(script)],capture_output=True,text=True,timeout=60)
    assert done.returncode==0,done.stdout+done.stderr
    assert 'Mechanical gate: **PASS**' in done.stdout
    assert 'Mechanical gate: **FAIL**' in done.stdout
    assert 'Declared path:' in done.stdout
