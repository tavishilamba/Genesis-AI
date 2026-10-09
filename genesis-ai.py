import json
import os
import re
from pathlib import Path

from openai import OpenAI

OUT = Path("output")
PROJECT = OUT / "project"
MAX_FILES = 12
MAX_FILE_SIZE = 30_000

def main():
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

    response = client.responses.create(
        model=model,
        instructions="""
You are DailyForge, an autonomous software developer.

Create ONE useful, small, original Python project.
Use Python's standard library only.
Include README.md and at least one pytest test file.
The project must be runnable locally and must not need credentials,
network access, external services, or elevated permissions.
Do not create malware, surveillance tools, or destructive software.
Return only a JSON object with these fields:
slug, title, description, files.
files must map relative file paths to their text contents.
Keep the project small, understandable and well documented.
""",
        input=(
            "Create a useful beginner-friendly developer tool or "
            "everyday utility. Avoid generic hello-world examples. "
            "Return valid JSON only."
        ),
    )

    data = json.loads(response.output_text)
    slug = re.sub(
        r"[^a-z0-9-]", "-", data["slug"].lower()
    ).strip("-")[:50]

    if not slug or not isinstance(data["files"], dict):
        raise ValueError("Invalid project metadata")

    files = data["files"]
    if not 2 <= len(files) <= MAX_FILES:
        raise ValueError("Invalid number of project files")

    PROJECT.mkdir(parents=True, exist_ok=True)

    for name, content in files.items():
        path = Path(name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not path.parts
            or not isinstance(content, str)
            or len(content.encode("utf-8")) > MAX_FILE_SIZE
        ):
            raise ValueError(f"Rejected file: {name}")

        destination = PROJECT / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    (OUT / "metadata.json").write_text(
        json.dumps({
            "slug": slug,
            "title": str(data["title"])[:120],
            "description": str(data["description"])[:500],
        }, indent=2),
        encoding="utf-8",
    )

    print(f"Generated project: {slug}")

if __name__ == "__main__":
    main()
