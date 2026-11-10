"""Eval-process-only physical HTTP custody and conservative budget admission.

# ruff: noqa: E501

Does not change prompts, models, retry counts, allowances, or rescue topology.
"""
# ruff: noqa: E501
from __future__ import annotations

import hashlib
import io
import json
import shutil
import threading
import time
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path

RATES = {
    'claude-fable-5-2': (8, 40),
    'claude-sonnet-4-6': (3, 15),
    'claude-haiku-4-5-20251001': (1, 5),
    'claude-opus-4-6': (5, 25),
    'gpt-4.1-mini': (.4, 1.6),
    'gpt-6.1-sol': (2, 10),
}


class AdmissionDenied(RuntimeError):
    pass


class StoredResponse(io.BytesIO):
    def __init__(self, raw, response):
        super().__init__(raw)
        self.status = getattr(response, 'status', 200)
        self.headers = getattr(response, 'headers', {})


class PhysicalMeter:
    def __init__(self, root: Path, cap='20'):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.cap = Decimal(cap)
        self.lock = threading.RLock()
        self.original = urllib.request.urlopen
        self.group = 'preflight'
        self.exhausted = False
        self.rows = []
        path = root / 'ledger.json'
        if path.exists():
            self.rows = json.loads(path.read_text())

    def save(self):
        (self.root / 'ledger.json').write_text(json.dumps(self.rows, indent=2) + '\n')

    def accounted(self):
        return sum(Decimal(str(x['accounted_usd'])) for x in self.rows)

    def __enter__(self):
        urllib.request.urlopen = self.urlopen
        return self

    def __exit__(self, *args):
        urllib.request.urlopen = self.original

    def count_native(self, body, request):
        count = {k: v for k, v in body.items() if k in {'model', 'messages', 'system', 'tools'}}
        if 'output_config' in body:
            count['system'] = str(count.get('system', '')) + '\n' + json.dumps(body['output_config'])
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages/count_tokens',
            data=json.dumps(count).encode(), method='POST',
            headers={'x-api-key': request.get_header('X-api-key'),
                     'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
        )
        with self.original(req, timeout=60) as response:
            return json.load(response)['input_tokens']

    def urlopen(self, request, *args, **kwargs):
        url = request.full_url if hasattr(request, 'full_url') else str(request)
        paid = url in {
            'https://api.anthropic.com/v1/messages',
            'https://api.openai.com/v1/chat/completions',
            'https://api.openai.com/v1/responses',
        }
        if not paid:
            if '/count_tokens' in url or '/models' in url:
                return self.original(request, *args, **kwargs)
            raise AdmissionDenied(f'Unplanned HTTP endpoint blocked: {url}')
        if self.exhausted:
            raise AdmissionDenied('Physical admission already halted; no later fallback call allowed')
        if (self.root.parent / 'CLOSED.json').exists():
            self.exhausted = True
            raise AdmissionDenied('Closed experiment: new inference needs a new authorized run identity')
        authorization = self.root.parent / 'FINAL_REPLAY_AUTHORIZED.json'
        if authorization.exists():
            allowed = json.loads(authorization.read_text())
            if len(self.rows) >= allowed['max_total_physical_calls'] or hashlib.sha256(request.data).hexdigest() != allowed['only_request_sha256']:
                self.exhausted = True
                raise AdmissionDenied('Final one-slot replay authorization does not admit this request')
        body = json.loads(request.data)
        if body.get('speed') not in (None, 'standard') or body.get('service_tier') not in (None, 'standard_only'):
            raise AdmissionDenied('Premium speed/tier request forbidden')
        if any(('fast-mode' in k.lower() or 'priority' in k.lower()) for k, _ in request.header_items()):
            raise AdmissionDenied('Premium speed header forbidden')
        model = body['model']
        if model not in RATES:
            raise AdmissionDenied(f'Unpriced model blocked: {model}')
        allowance = body.get('max_tokens', body.get('max_completion_tokens', body.get('max_output_tokens')))
        if not isinstance(allowance, int) or allowance < 1:
            raise AdmissionDenied('Unbounded output request blocked')
        if model.startswith('claude-'):
            input_bound = self.count_native(body, request) + 2048
        else:
            input_bound = len(request.data) + 2048
        ir, outr = map(Decimal, map(str, RATES[model]))
        # Reserve 1h cache writes at twice base input, even if not requested.
        input_multiplier = 2 if model.startswith('claude-') else 1
        reserve = (Decimal(input_bound) * ir * input_multiplier + Decimal(allowance) * outr) / 1000000
        with self.lock:
            if shutil.disk_usage(self.root).free < 512 * 1024**2:
                raise AdmissionDenied('Durable-write free-space guard')
            if self.accounted() + reserve > self.cap:
                self.exhausted = True
                raise AdmissionDenied('Hard USD20 physical-request reservation guard')
            name = f'{len(self.rows):04d}-{self.group}-{model}'
            folder = self.root / name
            folder.mkdir()
            encoded = request.data
            (folder / 'request.json').write_bytes(encoded)
            (folder / 'request-canonical.json').write_text(json.dumps(body, sort_keys=True, separators=(',', ':')))
            row = {'name': name, 'group': self.group, 'model': model,
                   'url': url, 'state': 'reserved', 'input_bound': input_bound,
                   'output_allowance': allowance, 'reservation_usd': str(reserve),
                   'accounted_usd': str(reserve),
                   'request_sha256': hashlib.sha256(encoded).hexdigest()}
            self.rows.append(row)
            self.save()
        start = time.perf_counter()
        try:
            response = self.original(request, *args, **kwargs)
            raw = response.read()
            # Original byte envelope persisted before any JSON/semantic parsing.
            (folder / 'response.json').write_bytes(raw)
            parsed = json.loads(raw)
            usage = parsed.get('usage', {})
            def count(value, name):
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise AdmissionDenied('Invalid usage count: ' + name)
                return value
            if url.endswith('/messages'):
                if parsed.get('model') != model:
                    raise AdmissionDenied('Served Anthropic model differs from priced requested model')
                if usage.get('service_tier') not in (None, 'standard') or usage.get('speed') not in (None, 'standard'):
                    raise AdmissionDenied('Reported premium speed/tier quarantined')
                i = count(usage.get('input_tokens'), 'input_tokens')
                o = count(usage.get('output_tokens'), 'output_tokens')
                read = count(usage.get('cache_read_input_tokens', 0), 'cache_read_input_tokens')
                write = count(usage.get('cache_creation_input_tokens', 0), 'cache_creation_input_tokens')
                if i + read + write > input_bound or o > allowance:
                    raise AdmissionDenied('Input/output usage exceeds admitted token bounds')
                creation = usage.get('cache_creation', {})
                w1 = count(creation.get('ephemeral_1h_input_tokens', 0), 'ephemeral_1h_input_tokens')
                w5 = count(creation.get('ephemeral_5m_input_tokens', 0), 'ephemeral_5m_input_tokens')
                if w1 + w5 > write:
                    raise AdmissionDenied('Cache creation components do not reconcile')
                unknown_write = max(0, write - w1 - w5)
                read_rate = Decimal('.2') if model == 'claude-fable-5-2' else ir * Decimal('.1')
                cost = (Decimal(i) * ir + Decimal(o) * outr + Decimal(read) * read_rate
                        + Decimal(w1 + unknown_write) * ir * 2
                        + Decimal(w5) * ir * Decimal('1.25')) / 1000000
            else:
                i = count(usage.get('prompt_tokens', usage.get('input_tokens')), 'input_tokens')
                o = count(usage.get('completion_tokens', usage.get('output_tokens')), 'output_tokens')
                if i > input_bound or o > allowance:
                    raise AdmissionDenied('Input/output usage exceeds admitted token bounds')
                cost = (Decimal(i) * ir + Decimal(o) * outr) / 1000000
            if cost < 0 or cost > reserve:
                raise AdmissionDenied('Usage exceeds conservative reservation; quarantine')
            with self.lock:
                row.update(state='settled-usage-estimate', accounted_usd=str(cost),
                           usage=usage, request_id=parsed.get('id'),
                           served_model=parsed.get('model'),
                           latency_ms=round((time.perf_counter() - start) * 1000),
                           response_sha256=hashlib.sha256(raw).hexdigest())
                self.save()
            return StoredResponse(raw, response)
        except Exception as exc:
            with self.lock:
                row.update(state='unknown-exposure-held', error_type=type(exc).__name__,
                           latency_ms=round((time.perf_counter() - start) * 1000))
                if isinstance(exc, urllib.error.HTTPError):
                    raw = exc.read()
                    (folder / 'error-body.txt').write_bytes(raw)
                    # Reconstitute readable error for existing helper recovery.
                    exc.fp = io.BytesIO(raw)
                    row['http_status'] = exc.code
                self.save()
            raise
