from __future__ import annotations

import base64
import io
import json
import urllib.error

import pytest

from cine_forge.ai import image as image_module
from cine_forge.ai.image import (
    ImageGenerationError,
    estimate_image_generation_cost_usd,
    generate_image,
    supports_direct_reference_images,
)


@pytest.mark.unit
def test_generate_image_routes_gpt_image_2_to_openai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, str]] = []

    def fake_openai(
        prompt: str,
        entity_type: str = "character",
        model: str = "gpt-image-1",
        quality: str = "auto",
        reference_image_paths: list[str] | None = None,
        size: str | None = None,
    ) -> tuple[bytes, str]:
        calls.append(("openai", model, str(size)))
        return b"openai-image", model

    def fake_imagen(
        prompt: str,
        entity_type: str = "character",
        model: str = "imagen-4.0-generate-001",
        aspect_ratio: str | None = None,
    ) -> tuple[bytes, str]:
        calls.append(("imagen", model, "None"))
        return b"imagen-image", model

    monkeypatch.setattr("cine_forge.ai.image._generate_image_openai", fake_openai)
    monkeypatch.setattr("cine_forge.ai.image._generate_image_imagen", fake_imagen)

    image_bytes, model_used = generate_image(
        prompt="storyboard test",
        entity_type="location",
        model="gpt-image-2",
        quality="low",
    )

    assert image_bytes == b"openai-image"
    assert model_used == "gpt-image-2"
    assert calls == [("openai", "gpt-image-2", "None")]


@pytest.mark.unit
def test_generate_image_rejects_unknown_model() -> None:
    with pytest.raises(ImageGenerationError, match="Unsupported image model"):
        generate_image(prompt="storyboard test", model="not-a-real-image-model")


@pytest.mark.unit
def test_supports_direct_reference_images_for_new_openai_image_models() -> None:
    assert supports_direct_reference_images("gpt-image-1")
    assert supports_direct_reference_images("gpt-image-1.5")
    assert supports_direct_reference_images("gpt-image-2")
    assert supports_direct_reference_images("chatgpt-image-latest")
    assert not supports_direct_reference_images("imagen-4.0-generate-001")


@pytest.mark.unit
def test_estimate_image_generation_cost_usd_supports_new_openai_image_models() -> None:
    assert estimate_image_generation_cost_usd(
        "gpt-image-1.5",
        entity_type="location",
        quality="low",
    ) == pytest.approx(0.013)
    assert estimate_image_generation_cost_usd(
        "chatgpt-image-latest",
        entity_type="location",
        quality="medium",
    ) == pytest.approx(0.05)
    assert estimate_image_generation_cost_usd(
        "gpt-image-2",
        entity_type="location",
        quality="high",
    ) == pytest.approx(0.18624)


@pytest.mark.unit
def test_generate_image_forwards_openai_size_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_openai(
        prompt: str,
        entity_type: str = "character",
        model: str = "gpt-image-1",
        quality: str = "auto",
        reference_image_paths: list[str] | None = None,
        size: str | None = None,
    ) -> tuple[bytes, str]:
        calls.append({"model": model, "size": size, "entity_type": entity_type})
        return b"openai-image", model

    monkeypatch.setattr("cine_forge.ai.image._generate_image_openai", fake_openai)

    generate_image(
        prompt="storyboard test",
        entity_type="location",
        model="gpt-image-2",
        size="1024x1024",
    )

    assert calls == [
        {"model": "gpt-image-2", "size": "1024x1024", "entity_type": "location"}
    ]
    assert estimate_image_generation_cost_usd(
        "gpt-image-2",
        entity_type="location",
        quality="low",
        size="1024x1024",
    ) == pytest.approx(0.00816)


@pytest.mark.unit
def test_openai_edit_retries_without_quality_when_provider_rejects_param(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    reference_path = tmp_path / "reference.jpg"
    reference_path.write_bytes(b"fake-reference")
    request_bodies: list[bytes] = []

    class FakeResponse:
        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {"data": [{"b64_json": base64.b64encode(b"image-bytes").decode("utf-8")}]}
            ).encode("utf-8")

    def fake_urlopen(req: object, timeout: int) -> FakeResponse:
        request_bodies.append(req.data)
        if len(request_bodies) == 1:
            raise urllib.error.HTTPError(
                url="https://api.openai.com/v1/images/edits",
                code=400,
                msg="Bad Request",
                hdrs={},
                fp=io.BytesIO(b'{"error":{"message":"Unknown parameter: \'quality\'."}}'),
            )
        if len(request_bodies) == 2:
            raise urllib.error.HTTPError(
                url="https://api.openai.com/v1/images/edits",
                code=400,
                msg="Bad Request",
                hdrs={},
                fp=io.BytesIO(b'{"error":{"message":"Unknown parameter: \'output_format\'."}}'),
            )
        return FakeResponse()

    monkeypatch.setattr(image_module.urllib.request, "urlopen", fake_urlopen)

    image_bytes, model_used = image_module._generate_image_openai(
        prompt="grid",
        entity_type="location",
        model="gpt-image-2",
        quality="low",
        reference_image_paths=[str(reference_path)],
        size="1024x1536",
    )

    assert image_bytes == b"image-bytes"
    assert model_used == "gpt-image-2"
    assert len(request_bodies) == 3
    assert b'name="quality"' in request_bodies[0]
    assert b'name="quality"' not in request_bodies[1]
    assert b'name="output_format"' in request_bodies[1]
    assert b'name="quality"' not in request_bodies[2]
    assert b'name="output_format"' not in request_bodies[2]
