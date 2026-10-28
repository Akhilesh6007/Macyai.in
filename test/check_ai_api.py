
import json
from urllib.request import urlopen
from urllib.error import URLError

BASE_URL = "http://127.0.0.1:8081"

def main():
    print("=== MACY AI API CHECK ===")

    try:
        with urlopen(BASE_URL + "/health", timeout=10) as response:
            print("Health:", response.read().decode())

        with urlopen(BASE_URL + "/openapi.json", timeout=10) as response:
            spec = json.load(response)

        paths = spec.get("paths", {})

        expected = [
            ("get", "/"),
            ("get", "/health"),
            ("post", "/api/v1/scripts/demo"),
            ("post", "/api/v1/scripts/generate"),
        ]

        for method, path in expected:
            exists = method in paths.get(path, {})
            print(
                "PASS" if exists else "MISSING",
                method.upper(),
                path
            )

        print("\nAI request details:")
        operation = paths.get(
            "/api/v1/scripts/generate", {}
        ).get("post", {})

        print(json.dumps(
            operation.get("requestBody", {}),
            indent=2
        ))

    except URLError as error:
        print("Connection error:", error)

if __name__ == "__main__":
    main()
