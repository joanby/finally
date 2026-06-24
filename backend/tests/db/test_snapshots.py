def test_record_and_list_snapshots(db):
    db.record_snapshot(10000.0)
    db.record_snapshot(10250.5)

    snapshots = db.list_snapshots()
    assert [s["total_value"] for s in snapshots] == [10000.0, 10250.5]
    assert all(s["recorded_at"] for s in snapshots)
