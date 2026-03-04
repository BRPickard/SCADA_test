from app.connectors.arcgis import ArcGISSurvey123Connector


def test_mock_survey123_fetches_records():
    c = ArcGISSurvey123Connector({"mock_mode": True})
    records = c.fetch_records()
    assert len(records) >= 1
    normalized = c.normalize_record(records[0])
    assert "source_record_id" in normalized
