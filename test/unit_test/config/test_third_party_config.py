from unittest.mock import patch

from core.config import AppConfig


def test_third_party_defaults(monkeypatch):
    """Test that third_party configs exist with defaults."""
    with patch("core.config.app.load_yaml", return_value={}):
        cfg = AppConfig()

    oauth_cfg = cfg.third_party.oauth
    assert oauth_cfg.oauth2.client_id is None
    assert oauth_cfg.oauth2.client_secret is None

    assert oauth_cfg.oidc.client_id is None
    assert oauth_cfg.oidc.client_secret is None

    assert oauth_cfg.github.client_id is None
    assert oauth_cfg.github.client_secret is None


def test_third_party_overrides(monkeypatch):
    monkeypatch.delenv("GITHUB_CLIENT_ID", raising=False)
    monkeypatch.delenv("GITHUB_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("OIDC_CLIENT_ID", raising=False)
    monkeypatch.delenv("OIDC_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("OAUTH2_CLIENT_ID", raising=False)
    monkeypatch.delenv("OAUTH2_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("TCADP_SECRET_ID", raising=False)
    monkeypatch.delenv("TCADP_SECRET_KEY", raising=False)
    monkeypatch.delenv("TCADP_REGION", raising=False)
    cfg = AppConfig()

    return_value = {
        "third_party": {
            "oauth": {
                "oauth2": {"client_id": "oauth2-client-id", "client_secret": "oauth2-client-secret"},
                "oidc": {"client_id": "oidc-client-id", "client_secret": "oidc-client-secret"},
                "github": {"client_id": "github-client-id", "client_secret": "github-client-secret"},
            },
            "tcadp": {
                "region": "us-east-1",
            },
        }
    }

    with patch("core.config.app.load_yaml", return_value=return_value):
        cfg = AppConfig()

    assert hasattr(cfg.third_party, "oauth")
    oauth_cfg = cfg.third_party.oauth

    assert oauth_cfg.oauth2.client_id == "oauth2-client-id"
    assert oauth_cfg.oauth2.client_secret == "oauth2-client-secret"

    assert oauth_cfg.oidc.client_id == "oidc-client-id"
    assert oauth_cfg.oidc.client_secret == "oidc-client-secret"

    assert oauth_cfg.github.client_id == "github-client-id"
    assert oauth_cfg.github.client_secret == "github-client-secret"

    assert hasattr(cfg.third_party, "tcadp")
    tc_cfg = cfg.third_party.tcadp
    assert tc_cfg.region == "us-east-1"
