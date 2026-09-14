from pathlib import Path

def test_service_metadata_names_repo():
    assert "name: identity-core" in Path("SERVICE.yaml").read_text()
