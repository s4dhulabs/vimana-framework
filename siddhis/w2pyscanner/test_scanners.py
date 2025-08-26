import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import asyncio
from siddhis.w2pyscanner.scanners.admin_scanner import AdminScanner
from siddhis.w2pyscanner.scanners.session_scanner import SessionScanner
from siddhis.w2pyscanner.scanners.upload_scanner import UploadScanner
from siddhis.w2pyscanner.scanners.database_scanner import DatabaseScanner
from siddhis.w2pyscanner.scanners.csrf_scanner import CSRFScanner
from siddhis.w2pyscanner.scanners.info_disclosure import InfoDisclosureScanner

# Minimal config for scanners
MIN_CONFIG = {}

class MockHTTPClient:
    async def get(self, url, *args, **kwargs):
        # Return a minimal valid response for all GETs
        return {
            "status": 200,
            "content": "<html><body>admin interface</body></html>",
            "headers": {},
            "set_cookie": "session_id=abc123; HttpOnly; Path=/"
        }
    async def post(self, url, *args, **kwargs):
        # Return a minimal valid response for all POSTs
        return {
            "status": 200,
            "content": "OK",
            "headers": {},
            "set_cookie": "session_id=abc123; HttpOnly; Path=/"
        }

@pytest.mark.asyncio
async def test_admin_scanner_basic():
    scanner = AdminScanner(config=MIN_CONFIG, http_client=MockHTTPClient())
    result = await scanner.scan("http://localhost:8086")
    assert isinstance(result, dict)
    assert "vulnerabilities" in result
    assert any("admin" in v["title"].lower() for v in result["vulnerabilities"])

@pytest.mark.asyncio
async def test_session_scanner_cookie_flags():
    scanner = SessionScanner(config=MIN_CONFIG, http_client=MockHTTPClient())
    set_cookie = "session_id=abc123; HttpOnly; Path=/"
    flags = scanner._analyze_cookie_flags(set_cookie)
    assert flags["HttpOnly"] is True
    assert flags["Secure"] is False
    assert flags["SameSite"] is False

@pytest.mark.asyncio
async def test_session_scanner_entropy():
    scanner = SessionScanner(config=MIN_CONFIG, http_client=MockHTTPClient())
    entropy = scanner._shannon_entropy("abc123abc123abc123")
    assert isinstance(entropy, float)
    assert entropy > 0

@pytest.mark.asyncio
async def test_upload_scanner_structure():
    scanner = UploadScanner(config=MIN_CONFIG, http_client=MockHTTPClient())
    result = await scanner.scan("http://localhost:8086")
    assert isinstance(result, dict)
    assert "vulnerabilities" in result

@pytest.mark.asyncio
async def test_database_scanner_structure():
    scanner = DatabaseScanner(config=MIN_CONFIG, http_client=MockHTTPClient())
    result = await scanner.scan("http://localhost:8086")
    assert isinstance(result, dict)
    assert "vulnerabilities" in result

@pytest.mark.asyncio
async def test_csrf_scanner_structure():
    scanner = CSRFScanner(config=MIN_CONFIG, http_client=MockHTTPClient())
    result = await scanner.scan("http://localhost:8086")
    assert isinstance(result, dict)
    assert "vulnerabilities" in result

@pytest.mark.asyncio
async def test_info_disclosure_scanner_structure():
    scanner = InfoDisclosureScanner(config=MIN_CONFIG, http_client=MockHTTPClient())
    result = await scanner.scan("http://localhost:8086")
    assert isinstance(result, dict)
    assert "vulnerabilities" in result 