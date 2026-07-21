#!/usr/bin/env python3
"""POC to use REST API exposed from external API"""


import httpx # Simple HTTP request handler library
# Actually useless because HTTPX has its own built-in JSON parser method.
# import json  # Required to parse and exploit response body


# Base URL when interrogating "from the same host"
BASE_URL = "http://localhost:5000/api/v1"
# WARNING: IF code run "from another container in the same set of Docker compose"
# THEN MUST use the container name of the targeted service, example http://hb_inv__products_api:5000


def test_api_case(title: str, endpoint: str):
    print(f"\n=== {title} ===")    # Test case label
    url = f"{BASE_URL}{endpoint}"
    print(f"GET {url}")            # Matching url targeted

    try:
        response = httpx.get(url, timeout=3.0)
        print(f"Status Code : {response.status_code}")

        try:
            print(f"Response    : {response.json()}")
        # Covers the various cases where response was not JSON, typically
        # Some 40* or 50* error spawning an HTML body instead of JSON in the response.
        except Exception:
            print(f"Response    : {response.text}")

    except httpx.RequestError as exc:
        print(f"❌ Failure: couldn't communicate with API ({exc})")


if __name__ == "__main__":
    # -------------------------------------------------------------
    # Case 1: Valid request (product exists)
    # -------------------------------------------------------------
    test_api_case(
        title="CASE 1: Valid request (product exists)",
        endpoint="/products/1"  # Remplace par un ID valide du catalogue
    )
    # Should get a 200 HTTP code

    # -------------------------------------------------------------
    # Case 2: Request with invalid format
    # -------------------------------------------------------------
    test_api_case(
        title="CASE 2: Request with invalid format",
        endpoint="/products/abc_invalid_id"
    )
    # Should get a 40* something code (some kind of error)

    # -------------------------------------------------------------
    # Case 3: Valid request but inexisting product
    # -------------------------------------------------------------
    test_api_case(
        title="CASE 3: Valid request but inexisting product",
        endpoint="/products/777"
    )
    # Should get a 404 with something like "product not found"
