"""Mocked-transport tests for the read-only connector prototypes.

These prove pagination, retry, error handling, credential hygiene, and
canonical mapping against SANITIZED SYNTHETIC fixtures. They prove nothing
about live vendor behavior - the connectors are mock-tested only.
"""

import json

import pytest

from opencoworking.connectors import ConnectorError, HubSpotClient, OfficeRnDClient
from opencoworking.connectors.base import get_json
from opencoworking.connectors.officernd import fetch_token


class FakeTransport:
    """Scripted transport: pops queued (status, headers, body) responses and
    records every request for assertions."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def request(self, method, url, headers, body=None, timeout=30.0):
        self.requests.append({"method": method, "url": url,
                              "headers": headers, "body": body})
        status, resp_headers, payload = self.responses.pop(0)
        return status, resp_headers, json.dumps(payload).encode()


def ok(payload):
    return (200, {}, payload)


class TestBasePlumbing:
    def test_retry_on_429_respects_retry_after(self, monkeypatch):
        sleeps = []
        monkeypatch.setattr("time.sleep", sleeps.append)
        t = FakeTransport([(429, {"Retry-After": "2"}, {}), ok({"fine": True})])
        assert get_json(t, "https://x.example/a", {}) == {"fine": True}
        assert sleeps == [2.0]

    def test_gives_up_after_retries(self, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda s: None)
        t = FakeTransport([(500, {}, {})] * 4)
        with pytest.raises(ConnectorError) as e:
            get_json(t, "https://x.example/a", {}, max_retries=3)
        assert e.value.kind == "vendor"

    def test_auth_error_contains_no_token(self):
        t = FakeTransport([(401, {}, {})])
        with pytest.raises(ConnectorError) as e:
            get_json(t, "https://x.example/a", {"Authorization": "Bearer sekret-token"})
        assert "sekret" not in str(e.value)
        assert e.value.kind == "auth"

    def test_read_only_uses_get(self):
        t = FakeTransport([ok({"results": []})])
        HubSpotClient(token="tt", transport=t).companies()
        assert all(r["method"] == "GET" for r in t.requests)


class TestHubSpot:
    def test_missing_token_is_structured_error(self, monkeypatch):
        monkeypatch.delenv("HUBSPOT_ACCESS_TOKEN", raising=False)
        with pytest.raises(ConnectorError) as e:
            HubSpotClient()
        assert e.value.kind == "auth"

    def test_contacts_pagination_and_mapping(self):
        page1 = ok({
            "results": [{"id": "301", "properties": {
                "firstname": "Demo", "lastname": "Person",
                "email": "demo.person@example.test", "phone": "555-0100",
                "createdate": "2026-05-01T10:00:00Z",
                "associatedcompanyid": "901"}}],
            "paging": {"next": {"after": "CURSOR2"}}})
        page2 = ok({"results": [{"id": "302", "properties": {
            "firstname": "Second", "lastname": "Demo",
            "email": "second@example.test", "phone": "",
            "createdate": "2026-06-02T09:00:00Z"}}]})
        t = FakeTransport([page1, page2])
        rows = HubSpotClient(token="tt", transport=t).contacts()
        assert [r["contact_id"] for r in rows] == ["301", "302"]
        assert rows[0]["company_id"] == "901"
        assert rows[0]["created_at"] == "2026-05-01"
        assert "after=CURSOR2" in t.requests[1]["url"]
        assert "properties=" in t.requests[0]["url"]  # explicit properties only

    def test_deals_stage_kept_verbatim_without_map(self):
        t = FakeTransport([ok({"results": [{
            "id": "7", "properties": {"dealstage": "appointmentscheduled",
                                      "amount": "12000",
                                      "createdate": "2026-06-01T00:00:00Z"},
            "associations": {"companies": {"results": [{"id": "901"}]}}}]})])
        rows = HubSpotClient(token="tt", transport=t).deals()
        assert rows[0]["stage"] == "appointmentscheduled"  # never guessed
        assert rows[0]["company_id"] == "901"

    def test_deals_stage_map_applied(self):
        t = FakeTransport([ok({"results": [{
            "id": "7", "properties": {"dealstage": "stage-x"}}]})])
        rows = HubSpotClient(token="tt", transport=t).deals(
            stage_map={"stage-x": "proposal"})
        assert rows[0]["stage"] == "proposal"

    def test_bearer_header_set(self):
        t = FakeTransport([ok({"results": []})])
        HubSpotClient(token="private-app-token", transport=t).companies()
        assert t.requests[0]["headers"]["Authorization"] == "Bearer private-app-token"


class TestOfficeRnD:
    def test_token_fetch_requires_explicit_url_and_creds(self, monkeypatch):
        monkeypatch.delenv("OFFICERND_CLIENT_ID", raising=False)
        monkeypatch.delenv("OFFICERND_CLIENT_SECRET", raising=False)
        with pytest.raises(ConnectorError):
            fetch_token("https://auth.example/token")

    def test_token_fetch_error_hides_secret(self):
        t = FakeTransport([(401, {}, {})])
        with pytest.raises(ConnectorError) as e:
            fetch_token("https://auth.example/token", "cid", "very-secret", t)
        assert "very-secret" not in str(e.value)

    def test_members_cursor_pagination_and_mapping(self):
        page1 = ok({"results": [{"_id": "m1", "name": "Demo Member",
                                 "email": "m@example.test", "team": "team1",
                                 "createdAt": "2026-01-05T00:00:00Z"}],
                    "cursorNext": "abc"})
        page2 = ok({"results": [{"_id": "m2", "name": "Zoe Only",
                                 "email": "z@example.test"}]})
        t = FakeTransport([page1, page2])
        rows = OfficeRnDClient("demo-org", "tok", transport=t).members()
        assert [r["contact_id"] for r in rows] == ["m1", "m2"]
        assert rows[0]["company_id"] == "team1"
        assert "cursorNext=abc" in t.requests[1]["url"].replace("%24", "$")
        assert t.requests[0]["url"].startswith(
            "https://app.officernd.com/api/v2/organizations/demo-org/members")

    def test_memberships_price_kept_verbatim(self):
        t = FakeTransport([ok({"results": [{"_id": "ms1", "team": "team1",
                                            "plan": "Private Office",
                                            "price": 4200,
                                            "startDate": "2026-01-01T00:00:00Z"}]})])
        rows = OfficeRnDClient("demo-org", "tok", transport=t).memberships()
        # 4200 could be monthly or term total - emitted verbatim; the
        # data-dictionary flow decides, never the connector.
        assert rows[0]["contracted_rate"] == "4200"
        assert rows[0]["product"] == "Private Office"

    def test_invoices_mapping(self):
        t = FakeTransport([ok({"results": [{"_id": "i1", "team": "team1",
                                            "total": 500, "status": "Paid",
                                            "issueDate": "2026-06-01T00:00:00Z",
                                            "dueDate": "2026-06-15T00:00:00Z"}]})])
        rows = OfficeRnDClient("demo-org", "tok", transport=t).invoices()
        assert rows[0]["status"] == "paid"
        assert rows[0]["due_date"] == "2026-06-15"
