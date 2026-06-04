import base64
import json
import re
import requests
from pathlib import Path


def main():
    readme_path = Path("README.md")
    output_path = Path("architecture.png")

    if not readme_path.exists():
        print("Error: README.md not found.")
        return

    print("Reading README.md...")
    content = readme_path.read_text(encoding="utf-8")

    # Extract the first mermaid block
    match = re.search(r"```mermaid\n(.*?)\n```", content, re.DOTALL)
    if not match:
        print("Error: No mermaid block found in README.md.")
        return

    mermaid_code = match.group(1).strip()
    # Normalize unicode arrows to standard Mermaid arrows for the online parser
    mermaid_code = mermaid_code.replace("➔", "-->")
    # Wrap subgraph labels in double quotes to prevent syntax errors
    mermaid_code = re.sub(
        r"subgraph\s+(\w+)\s+\[(.*?)\]", r'subgraph \1 ["\2"]', mermaid_code
    )
    print("Found and cleaned mermaid diagram!")

    # Prepare the payload for mermaid.ink
    payload = {"code": mermaid_code, "mermaid": {"theme": "default"}}

    # Base64 encode the JSON payload
    json_bytes = json.dumps(payload).encode("utf-8")
    encoded_str = base64.b64encode(json_bytes).decode("utf-8")

    url = f"https://mermaid.ink/img/{encoded_str}"
    print("Downloading image from mermaid.ink API...")

    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            output_path.write_bytes(response.content)
            print(f"Success! Diagram saved to {output_path.resolve()}")
        else:
            print(f"Error: Failed to fetch image. HTTP Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Exception occurred: {e}")


if __name__ == "__main__":
    main()
