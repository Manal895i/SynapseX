"""
Unit tests for the modular evidence parser package.
Tests use real in-memory or temporary files — no mocking of file I/O.
"""
import csv
import json
import os
import tempfile
import pytest

from app.processing.base import ParsedEvent
from app.processing.csv_parser import CSVParser, _try_parse_timestamp
from app.processing.json_parser import JSONParser
from app.processing.txt_parser import TXTParser
from app.processing.evtx_parser import EVTXParser
from app.processing.media_parser import MediaParser


# ─── CSV Parser ────────────────────────────────────────────────────────────

def test_csv_parser_returns_one_event_per_row():
    rows = [{"timestamp": "2026-01-01T10:00:00", "src_ip": "192.168.1.1", "action": "login"}] * 3
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "src_ip", "action"])
        writer.writeheader()
        writer.writerows(rows)
        path = f.name
    try:
        events = CSVParser().parse(path, "test.csv")
        assert len(events) == 3
        assert all(e.event_type == "structured_row" for e in events)
    finally:
        os.unlink(path)


def test_csv_parser_extracts_timestamp_column():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "value"])
        writer.writeheader()
        writer.writerow({"timestamp": "2026-06-15T09:30:00", "value": "42"})
        path = f.name
    try:
        events = CSVParser().parse(path, "events.csv")
        assert events[0].timestamp is not None
        assert events[0].timestamp.year == 2026
    finally:
        os.unlink(path)


def test_csv_parser_handles_missing_timestamp():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ip", "port"])
        writer.writeheader()
        writer.writerow({"ip": "10.0.0.1", "port": "443"})
        path = f.name
    try:
        events = CSVParser().parse(path, "conn.csv")
        assert events[0].timestamp is None
    finally:
        os.unlink(path)


def test_csv_timestamp_parser_handles_bad_value():
    result = _try_parse_timestamp("not-a-date")
    assert result is None


def test_csv_parser_handles_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        path = f.name
    try:
        events = CSVParser().parse(path, "empty.csv")
        assert events == []
    finally:
        os.unlink(path)


# ─── JSON Parser ───────────────────────────────────────────────────────────

def test_json_parser_array_of_objects():
    data = [{"id": 1, "event": "login"}, {"id": 2, "event": "logout"}]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        events = JSONParser().parse(path, "events.json")
        assert len(events) == 2
        assert all(e.event_type == "json_record" for e in events)
    finally:
        os.unlink(path)


def test_json_parser_single_object():
    data = {"user": "alice", "action": "view"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        events = JSONParser().parse(path, "single.json")
        assert len(events) == 1
    finally:
        os.unlink(path)


def test_json_parser_extracts_timestamp():
    data = [{"timestamp": "2026-03-10T14:00:00", "msg": "test"}]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        events = JSONParser().parse(path, "ts.json")
        assert events[0].timestamp is not None
        assert events[0].timestamp.month == 3
    finally:
        os.unlink(path)


def test_json_parser_handles_invalid_json():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{ this is not json }")
        path = f.name
    try:
        events = JSONParser().parse(path, "bad.json")
        assert events == []
    finally:
        os.unlink(path)


# ─── TXT Parser ────────────────────────────────────────────────────────────

def test_txt_parser_one_event_per_nonempty_line():
    content = "Line one\nLine two\n\nLine four\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        events = TXTParser().parse(path, "log.txt")
        assert len(events) == 3   # blank line skipped
        assert all(e.event_type == "log_entry" for e in events)
    finally:
        os.unlink(path)


# ─── EVTX Parser (Placeholder) ─────────────────────────────────────────────

def test_evtx_parser_produces_placeholder_event():
    # Create a fake file — not a real EVTX
    with tempfile.NamedTemporaryFile(suffix=".evtx", delete=False) as f:
        f.write(b"\x00" * 64)
        path = f.name
    try:
        events = EVTXParser().parse(path, "security.evtx")
        assert len(events) == 1
        assert events[0].event_type == "windows_event"
        assert events[0].entity_value == "placeholder"
    finally:
        os.unlink(path)


def test_evtx_magic_bytes_detection():
    # Create a file with correct EVTX magic
    with tempfile.NamedTemporaryFile(suffix=".evtx", delete=False) as f:
        f.write(b"ElfFile\x00" + b"\x00" * 56)
        path = f.name
    try:
        from app.processing.evtx_parser import _is_valid_evtx
        assert _is_valid_evtx(path) is True
    finally:
        os.unlink(path)


# ─── Media Parser ──────────────────────────────────────────────────────────

def test_media_parser_registers_image():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG" + b"\x00" * 60)
        path = f.name
    try:
        events = MediaParser().parse(path, "screenshot.png")
        assert len(events) == 1
        assert events[0].event_type == "media_registered"
        assert events[0].entity_value == "png"
    finally:
        os.unlink(path)


def test_media_parser_no_ai_analysis():
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"\x00" * 100)
        path = f.name
    try:
        events = MediaParser().parse(path, "footage.mp4")
        meta = events[0].metadata or {}
        assert meta.get("analysis_status") == "pending_future_processing"
    finally:
        os.unlink(path)
