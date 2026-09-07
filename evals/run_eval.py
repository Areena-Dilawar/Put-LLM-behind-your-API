import json

import requests


API_URL = "http://127.0.0.1:8000/triage"


def main():
    with open("evals/cases.json", "r", encoding="utf-8") as file:
        cases = json.load(file)

    matched = 0
    failed_cases = []

    for case in cases:
        try:
            response = requests.post(
                API_URL,
                json={"text": case["text"]},
                timeout=60,
            )

            if response.status_code != 200:
                failed_cases.append(
                    f"- {case['id']}: API returned HTTP {response.status_code}"
                )
                continue

            result = response.json()
            expected_category = case["expected"]["category"]
            actual_category = result.get("category")

            if actual_category == expected_category:
                matched += 1
            else:
                failed_cases.append(
                    f"- {case['id']}: expected={expected_category}, "
                    f"actual={actual_category}"
                )

        except requests.RequestException as error:
            failed_cases.append(
                f"- {case['id']}: request failed: {error}"
            )

    total = len(cases)
    percentage = (matched / total * 100) if total else 0

    print(f"Matched: {matched}/{total}")
    print(f"Category accuracy: {percentage:.1f}%")
    print("Failed cases:")

    if failed_cases:
        for failure in failed_cases:
            print(failure)
    else:
        print("None")


if __name__ == "__main__":
    main()