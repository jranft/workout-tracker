import pytest
from app import parse_duration

def test_minutes_and_seconds():
    assert abs(parse_duration("00:59:07") - (59 + 7/60)) < 0.0001

def test_hours_minutes_seconds():
    assert abs(parse_duration("01:23:43") - (83 + 43/60)) < 0.0001

def test_zero_duration():
    assert parse_duration("00:00:00") == 0.0

def test_whole_minutes():
    assert parse_duration("00:30:00") == 30.0

def test_exactly_one_hour():
    assert parse_duration("01:00:00") == 60.0

def test_invalid_returns_none():
    assert parse_duration("") is None
    assert parse_duration("abc") is None
    assert parse_duration(None) is None

def test_out_of_range_returns_none():
    assert parse_duration("00:99:00") is None
    assert parse_duration("00:00:61") is None

def test_malformed_three_part_returns_none():
    assert parse_duration("00:xx:00") is None
