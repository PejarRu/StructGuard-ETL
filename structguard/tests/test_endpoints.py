import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure project root is on sys.path for imports when running from repo root.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app  # noqa: E402


def test_extract_endpoint_accepts_file():
    client = TestClient(app)
    files = {"file": ("sample.xml", b"<root></root>", "application/xml")}
    response = client.post("/v1/extract", files=files)
    assert response.status_code == 200


def test_inject_endpoint_accepts_files():
    client = TestClient(app)
    files = {
        "skeleton_file": ("skeleton.xml", b"<root></root>", "application/xml"),
        "modifications_file": (
            "mods.json",
            b"[{\"id\": \"1\", \"original_text\": \"a\"}]",
            "application/json",
        ),
    }
    response = client.post("/v1/inject", files=files)
    assert response.status_code == 200
