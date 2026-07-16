from privacy_shield import PrivacyShield


def test_protects_common_credentials_and_restores_local_result():
    shield = PrivacyShield()
    source = (
        "Authorization: Bearer top-secret-token\n"
        "api_key=sk-abcdefghijklmnopqrstuvwxyz123456\n"
        "contact dev@example.com"
    )

    result = shield.protect(source)

    assert "top-secret-token" not in result.protected_text
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in result.protected_text
    assert "dev@example.com" not in result.protected_text
    assert result.total == 3
    assert result.counts == {"authorization": 1, "api_key": 1, "email": 1}
    assert result.restore(result.protected_text) == source


def test_reuses_placeholder_for_repeated_value():
    result = PrivacyShield().protect("a@example.com then a@example.com")

    assert result.total == 1
    assert result.protected_text.count("__ATO_EMAIL_1__") == 2
    assert result.restore(result.protected_text) == "a@example.com then a@example.com"


def test_overlapping_generic_secret_does_not_double_redact_known_key():
    token = "sk-abcdefghijklmnopqrstuvwxyz123456"
    result = PrivacyShield().protect(f"api_key={token}")

    assert result.total == 1
    assert result.counts == {"api_key": 1}
    assert result.restore(result.protected_text) == f"api_key={token}"


def test_protects_private_key_as_one_item():
    key = "-----BEGIN PRIVATE KEY-----\nabc123\n-----END PRIVATE KEY-----"
    result = PrivacyShield().protect(key)

    assert result.counts == {"private_key": 1}
    assert "abc123" not in result.protected_text
    assert result.restore(result.protected_text) == key


def test_protects_windows_username_but_keeps_path_shape():
    source = r"Failed at C:\Users\alice\project\main.py:12"
    result = PrivacyShield().protect(source)

    assert "alice" not in result.protected_text
    assert r"C:\Users\__ATO_USER_PATH_1__\project" in result.protected_text
    assert result.restore(result.protected_text) == source


def test_plain_technical_text_is_unchanged():
    source = "TypeError: value is None at line 42"
    result = PrivacyShield().protect(source)

    assert result.protected_text == source
    assert result.total == 0
    assert result.replacements == {}


def test_existing_placeholder_like_text_cannot_be_overwritten_on_restore():
    source = "literal __ATO_EMAIL_1__ and dev@example.com"
    result = PrivacyShield().protect(source)

    assert "__ATO_EMAIL_2__" in result.protected_text
    assert result.restore(result.protected_text) == source
