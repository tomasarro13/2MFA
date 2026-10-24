from app.domain import totp

# RFC 6238, Apéndice B (SHA1). Secreto ASCII "12345678901234567890".
RFC_SECRET_B32 = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
RFC_VECTORS = {
    59: "94287082",
    1111111109: "07081804",
    1111111111: "14050471",
    1234567890: "89005924",
    2000000000: "69279037",
    20000000000: "65353130",
}


def test_rfc6238_vectors_8_digits():
    key = totp.b32_decode(RFC_SECRET_B32)
    for t, expected in RFC_VECTORS.items():
        assert totp.hotp(key, totp.counter_at(t), digits=8) == expected


def test_six_digits_are_last_six_of_rfc_vector():
    assert totp.totp(RFC_SECRET_B32, 59) == "287082"


def test_b32_decode_accepts_lowercase_spaces_and_missing_padding():
    assert totp.b32_decode("gezd gnbv") == totp.b32_decode("GEZDGNBV")


def test_provisioning_uri_contains_secret():
    uri = totp.provisioning_uri("ABC", "ana", "Lab2FA")
    assert uri.startswith("otpauth://totp/Lab2FA%3Aana?secret=ABC")
