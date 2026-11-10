"""Pinned baseline meter: unchanged pricing/transport with safe URL rejection.

The frozen throughput runner resolves discovery to runtime Haiku, not recipe
Gemini. No query-auth provider is in this matrix. Reject undeclared routes with
sanitized metadata, never echo a potential query credential into a traceback.
"""
from urllib.parse import urlsplit, urlunsplit

from whole_story_workspace_meter import AdmissionDenied
from whole_story_workspace_meter import PhysicalMeter as NativePhysicalMeter


def safe_url(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.hostname or '', parts.path, '', ''))


class PhysicalMeter(NativePhysicalMeter):
    def urlopen(self, request, *args, **kwargs):
        url = request.full_url if hasattr(request, 'full_url') else str(request)
        clean = safe_url(url)
        parts = urlsplit(url)
        if parts.query or parts.fragment or parts.username or parts.password:
            self.exhausted = True
            raise AdmissionDenied('Undeclared query/auth endpoint blocked: ' + clean)
        try:
            return super().urlopen(request, *args, **kwargs)
        except AdmissionDenied as exc:
            raise AdmissionDenied(str(exc).replace(url, clean)) from None
