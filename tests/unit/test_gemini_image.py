"""Mocked transport regressions; these tests do not evaluate image quality."""

from __future__ import annotations

import base64
import io
import json
import urllib.error
from email.message import Message

import pytest
from PIL import Image

from cine_forge.ai import gemini_image as adapter
from cine_forge.ai.image import (
    DEFAULT_MODEL,
    ImageGenerationError,
    estimate_image_generation_cost_usd,
    generate_image,
    supports_direct_reference_images,
)

pytestmark = pytest.mark.unit


def image_data(fmt: str = "PNG") -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (3, 2), "blue").save(output, format=fmt)
    return output.getvalue()


def result(data: bytes | None = None) -> dict:
    return {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {
                    "parts": [
                        {"text": "Rendered."},
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": base64.b64encode(
                                    data if data is not None else image_data()
                                ).decode(),
                            }
                        },
                    ]
                },
            }
        ]
    }


def mock_response(monkeypatch: pytest.MonkeyPatch, payload: object) -> list:
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return json.dumps(payload).encode()

    def open_request(request, timeout):
        calls.append((request, timeout))
        return Response()

    monkeypatch.setenv("CINE_FORGE_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(adapter.urllib.request, "urlopen", open_request)
    return calls


def test_default_dispatch_native_request_and_jpeg(monkeypatch):
    calls = mock_response(monkeypatch, result())
    data, model = generate_image("test", entity_type="location")
    assert model == DEFAULT_MODEL == "gemini-nano-banana-2.1"
    assert supports_direct_reference_images(model)
    with Image.open(io.BytesIO(data)) as image:
        assert image.format == "JPEG"
        assert image.size == (3, 2)
    request, timeout = calls[0]
    assert request.full_url == f"{adapter.BASE_URL}/{model}:generateContent"
    assert request.get_header("X-goog-api-key") == "test-key"
    assert "test-key" not in request.full_url
    assert timeout == 120
    assert json.loads(request.data) == {
        "contents": [{"role": "user", "parts": [{"text": "test"}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "responseFormat": {"image": {"aspectRatio": "16:9", "imageSize": "1K"}},
            "thinkingConfig": {"thinkingLevel": "medium"},
        },
    }


@pytest.mark.parametrize(
    "quality,thinking",
    [
        ("auto", "medium"),
        ("low", "minimal"),
        ("medium", "medium"),
        ("high", "high"),
    ],
)
def test_resolution_aspect_and_quality_mapping(monkeypatch, quality, thinking):
    calls = mock_response(monkeypatch, result())
    generate_image("test", size="2K", aspect_ratio="21:9", quality=quality)
    config = json.loads(calls[0][0].data)["generationConfig"]
    assert config["responseFormat"]["image"] == {"aspectRatio": "21:9", "imageSize": "2K"}
    assert config["thinkingConfig"]["thinkingLevel"] == thinking


@pytest.mark.parametrize(
    "size,aspect",
    [
        ("1024x1024", "1:1"),
        ("1024x1536", "2:3"),
        ("1536x1024", "3:2"),
    ],
)
def test_existing_pixel_sizes_map_orientation(monkeypatch, size, aspect):
    calls = mock_response(monkeypatch, result())
    generate_image("test", entity_type="character", size=size)
    assert json.loads(calls[0][0].data)["generationConfig"]["responseFormat"]["image"] == {
        "aspectRatio": aspect,
        "imageSize": "1K",
    }


def test_references_detect_mime_from_bytes_and_preserve_all_14(monkeypatch, tmp_path):
    path = tmp_path / "misnamed.jpg"
    path.write_bytes(image_data("PNG"))
    calls = mock_response(monkeypatch, result())
    generate_image("test", reference_image_paths=[str(path)] * 14)
    parts = json.loads(calls[0][0].data)["contents"][0]["parts"]
    assert len(parts) == 15
    for part in parts[1:]:
        assert part["inlineData"]["mimeType"] == "image/png"
        assert base64.b64decode(part["inlineData"]["data"]) == path.read_bytes()


@pytest.mark.parametrize(
    "kwargs,message",
    [
        ({"reference_image_paths": ["unused"] * 15}, "at most 14"),
        ({"reference_image_paths": [""]}, "Invalid Gemini reference"),
        ({"reference_image_paths": ["/no/such/image.png"]}, "Cannot read Gemini reference"),
        ({"aspect_ratio": "banana"}, "aspect ratio"),
        ({"size": "512"}, "image size"),
        ({"quality": "best"}, "quality"),
    ],
)
def test_invalid_inputs_fail_before_http(monkeypatch, kwargs, message):
    calls = mock_response(monkeypatch, result())
    with pytest.raises(ImageGenerationError, match=message):
        generate_image("test", **kwargs)
    assert calls == []


def test_skips_thought_image(monkeypatch):
    payload = result()
    parts = payload["candidates"][0]["content"]["parts"]
    parts.insert(0, {"thought": True, "inlineData": {"mimeType": "image/png", "data": "invalid"}})
    mock_response(monkeypatch, payload)
    assert generate_image("test")[0].startswith(b"\xff\xd8")


@pytest.mark.parametrize(
    "payload,message",
    [
        ({"promptFeedback": {"blockReason": "SAFETY"}}, "prompt blocked: SAFETY"),
        ({"candidates": [{"finishReason": "IMAGE_SAFETY"}]}, "no image.*IMAGE_SAFETY"),
        (
            {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "No"}]}}]},
            "no image",
        ),
        ({}, "no image"),
        (result(b"not-an-image"), "invalid image data"),
        ([], "invalid response"),
    ],
)
def test_bad_provider_response(monkeypatch, payload, message):
    mock_response(monkeypatch, payload)
    with pytest.raises(ImageGenerationError, match=message) as info:
        generate_image("test")
    assert info.value.provider == "google"
    assert info.value.model == DEFAULT_MODEL


def test_http_error_preserves_metadata(monkeypatch):
    mock_response(monkeypatch, result())
    headers = Message()
    headers["x-goog-request-id"] = "req_123"

    def fail(*_, **__):
        raise urllib.error.HTTPError(
            "https://example.invalid",
            503,
            "Unavailable",
            headers,
            io.BytesIO(b'{"error":{"message":"Try later","code":503}}'),
        )

    monkeypatch.setattr(adapter.urllib.request, "urlopen", fail)
    with pytest.raises(ImageGenerationError, match="HTTP 503: Try later") as info:
        generate_image("test")
    assert info.value.request_id == "req_123"
    assert info.value.status_code == 503
    assert info.value.is_transient


def test_missing_key_is_structured(monkeypatch):
    monkeypatch.delenv("CINE_FORGE_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ImageGenerationError, match="GEMINI_API_KEY") as info:
        generate_image("test")
    assert info.value.provider == "google"


@pytest.mark.parametrize(
    "size,cost", [(None, 0.0336), ("1K", 0.0336), ("2K", 0.0504), ("4K", 0.1134)]
)
def test_output_only_cost_estimate(size, cost):
    assert estimate_image_generation_cost_usd(DEFAULT_MODEL, size=size) == pytest.approx(cost)


def test_explicit_imagen_selection_preserved(monkeypatch):
    monkeypatch.setattr(
        "cine_forge.ai.image._generate_image_imagen", lambda *args: (b"imagen", args[2])
    )
    assert generate_image("test", model="imagen-4.0-generate-001") == (
        b"imagen",
        "imagen-4.0-generate-001",
    )


@pytest.mark.parametrize("error", [urllib.error.URLError("offline"), TimeoutError()])
def test_transport_error_is_structured(monkeypatch, error):
    mock_response(monkeypatch, result())

    def fail(*_, **__):
        raise error

    monkeypatch.setattr(adapter.urllib.request, "urlopen", fail)
    with pytest.raises(ImageGenerationError, match="request failed") as info:
        generate_image("test")
    assert info.value.is_transient
    assert info.value.provider == "google"


def test_invalid_json_is_structured(monkeypatch):
    mock_response(monkeypatch, result())

    class Response(io.BytesIO):
        pass

    monkeypatch.setattr(adapter.urllib.request, "urlopen", lambda *_, **__: Response(b"invalid"))
    with pytest.raises(ImageGenerationError, match="invalid JSON"):
        generate_image("test")


@pytest.mark.parametrize(
    "payload",
    [
        {"candidates": [None]},
        {"candidates": "bad"},
        {"promptFeedback": "bad"},
        {"candidates": [{"content": "bad"}]},
        {"candidates": [{"content": {"parts": "bad"}}]},
        {"candidates": [{"content": {"parts": [None]}}]},
        {"candidates": [{"content": {"parts": [{"inlineData": "bad"}]}}]},
    ],
)
def test_malformed_nested_response_is_structured(monkeypatch, payload):
    mock_response(monkeypatch, payload)
    with pytest.raises(ImageGenerationError, match="invalid response"):
        generate_image("test")


def test_invalid_base64_is_structured(monkeypatch):
    payload = result()
    payload["candidates"][0]["content"]["parts"][1]["inlineData"]["data"] = "!not-base64"
    mock_response(monkeypatch, payload)
    with pytest.raises(ImageGenerationError, match="invalid image data"):
        generate_image("test")


@pytest.mark.parametrize("reason", ["SAFETY", "IMAGE_SAFETY", "PROHIBITED_CONTENT", "MAX_TOKENS"])
def test_blocked_or_incomplete_candidate_cannot_publish_image(monkeypatch, reason):
    payload = result()
    payload["candidates"][0]["finishReason"] = reason
    mock_response(monkeypatch, payload)
    with pytest.raises(ImageGenerationError, match=f"no image.*{reason}") as info:
        generate_image("test")
    assert info.value.error_code == reason


def test_native_entity_aspect_defaults_without_pixel_override(monkeypatch):
    calls = mock_response(monkeypatch, result())
    for entity, aspect in [("character", "9:16"), ("location", "16:9"), ("prop", "4:3")]:
        generate_image("test", entity_type=entity, size=None)
        config = json.loads(calls[-1][0].data)["generationConfig"]
        assert config["responseFormat"]["image"]["aspectRatio"] == aspect


def test_tuple_retains_requested_model_without_claiming_serving_proof(monkeypatch):
    payload = result()
    payload["modelVersion"] = "provider-internal-build"
    mock_response(monkeypatch, payload)
    assert generate_image("test")[1] == DEFAULT_MODEL
