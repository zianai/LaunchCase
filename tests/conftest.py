from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from launchcase.api import create_app
from launchcase.domain.contracts import ProductBrief, SourceImport
from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.db import Base

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures/scenarios/pet-furniture-us'


@pytest.fixture
def setup(tmp_path):
    settings = Settings(tmp_path, f'sqlite:///{tmp_path}/test.db')
    app = create_app(settings)
    svc = app.state.service
    Base.metadata.create_all(svc.engine)
    token, actor = svc.provision('tenant-a', 'fixture reviewer', 'owner', True)
    _, other = svc.provision('tenant-b', 'other', 'owner', True)
    client = TestClient(app, headers={'Authorization': f'Bearer {token}'})
    return svc, actor, other, client


@pytest.fixture
def brief():
    return ProductBrief.model_validate_json((FIXTURE / 'synthetic-brief.json').read_text())


@pytest.fixture
def case(setup, brief):
    svc, actor, _, _ = setup
    return svc.create_case(actor, brief, 'case-create')


@pytest.fixture
def imported(setup, case):
    svc, actor, _, _ = setup
    request = SourceImport(filename='synthetic-voc.csv', content=(FIXTURE / 'synthetic-voc.csv').read_text(),
        source_type='review', rights_status='synthetic_fixture', is_synthetic=True)
    result = svc.import_source(actor, case['id'], request, 'source-import')
    return request, result


def decide(svc, actor, case_id, gate, subject_id, decision):
    from launchcase.application.products import ProductService
    from launchcase.domain.common import uid
    from launchcase.domain.contracts import GateRequest
    product = ProductService(svc)
    subject = product.gate_subject(actor, case_id, gate, subject_id)
    return product.decide(actor, case_id, gate, GateRequest(decision=decision,
        subject_type={'G1':'opportunity','G2':'concept','G3':'feasibility','G4':'sample','G5':'launch_pack'}[gate],
        subject_id=subject_id, expected_subject_hash=subject['subject_hash'],
        reason='Synthetic test actor decision; no real product approval'), uid())


@pytest.fixture
def concepts(setup, case, imported):
    from launchcase.infrastructure.models import Artifact
    from launchcase.workflow.graph import enqueue_run, execute_task
    svc, actor, _, _ = setup
    research = enqueue_run(svc, actor, case['id'], 'research', 'research-run')
    execute_task(svc, actor, research['id'])
    opps = svc.list_scoped(actor, case['id'], Artifact, kind='Opportunity')
    opp = next(x for x in opps if 'assembly' in x['data']['title'])
    decide(svc, actor, case['id'], 'G1', opp['id'], 'accept')
    task = enqueue_run(svc, actor, case['id'], 'concepts', 'concept-run')
    execute_task(svc, actor, task['id'])
    return svc.list_scoped(actor, case['id'], Artifact, kind='Concept')
