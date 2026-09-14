from pathlib import Path

def test_service_metadata_names_repo():
    assert "name: merchant-service" in Path("SERVICE.yaml").read_text()
