import argparse
import importlib.metadata
import json
import os
from pathlib import Path

from launchcase.application.services import CaseService
from launchcase.domain.common import DomainError, uid
from launchcase.domain.contracts import ProductBrief, SourceImport
from launchcase.infrastructure.config import Settings
from launchcase.infrastructure.store import read_import_file


def main():
    parser = argparse.ArgumentParser(prog='launchcase')
    parser.add_argument('--json', action='store_true', help='All commands emit JSON')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor')
    auth = sub.add_parser('auth').add_subparsers(dest='operation', required=True).add_parser('create')
    auth.add_argument('--tenant', required=True)
    auth.add_argument('--name', required=True)
    auth.add_argument('--role', choices=['owner', 'reviewer', 'analyst', 'agent', 'viewer'], default='owner')
    auth.add_argument('--synthetic', action='store_true')
    case = sub.add_parser('case').add_subparsers(dest='operation', required=True)
    create = case.add_parser('create')
    create.add_argument('--brief', type=Path, required=True)
    status = case.add_parser('status')
    status.add_argument('case_id')
    case.add_parser('list')
    source = sub.add_parser('source').add_subparsers(dest='operation', required=True).add_parser('import')
    source.add_argument('--case', dest='case_id', required=True)
    source.add_argument('--file', type=Path, required=True)
    source.add_argument('--type', required=True, choices=['review', 'competitor', 'quote', 'spec', 'sample', 'rule'])
    source.add_argument('--rights', required=True, choices=['synthetic_fixture', 'authorized', 'unknown'])
    source.add_argument('--synthetic', action='store_true')
    args = parser.parse_args()
    service = CaseService(Settings.from_env())
    try:
        if args.command == 'doctor':
            result = {'status': 'ok', 'paid_enabled': False, 'external_actions': False,
                      'versions': {p: importlib.metadata.version(p) for p in
                                   ['launchcase', 'fastapi', 'pydantic', 'sqlalchemy', 'langgraph', 'openai-agents']}}
        elif args.command == 'auth':
            token, actor = service.provision(args.tenant, args.name, args.role, args.synthetic)
            result = {'token': token, 'tenant_id': actor.tenant_id, 'role': actor.role}
        else:
            actor = service.authenticate(os.getenv('LAUNCHCASE_TOKEN', ''))
            if args.command == 'case' and args.operation == 'create':
                result = service.create_case(actor, ProductBrief.model_validate_json(read_import_file(args.brief)), uid())
            elif args.command == 'case' and args.operation == 'status':
                result = service.get_case(actor, args.case_id)
            elif args.command == 'case':
                result = {'items': service.list_cases(actor)}
            else:
                request = SourceImport(filename=args.file.name, content=read_import_file(args.file),
                    source_type=args.type, rights_status=args.rights, is_synthetic=args.synthetic)
                result = service.import_source(actor, args.case_id, request, uid())
        print(json.dumps(result, ensure_ascii=False))
    except DomainError as exc:
        print(json.dumps({'error': {'code': exc.code, 'message': exc.message}}))
        raise SystemExit(1) from exc
