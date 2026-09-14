from pathlib import Path

def test_service_metadata_names_repo():
    assert "name: repayment-service" in Path("SERVICE.yaml").read_text()
