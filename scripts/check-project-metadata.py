"""Check how Copier answers reach the distribution, FastAPI, the visor, and the shell."""

import json
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from zipfile import ZipFile

TEMPLATE = Path(__file__).resolve().parents[1]
COPY = ["copier", "copy", "--quiet", "--defaults", "--vcs-ref", "HEAD"]
TITLE = """Calendar: "Anna's studio" & $5"""
DESCRIPTION = r"""Projects in "Málaga" & "Córdoba" 🗓, under C:\teams."""


class PageMetadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""
        self.description = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "meta" and attributes.get("name") == "description":
            self.description = attributes.get("content")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


with tempfile.TemporaryDirectory() as work:
    project = Path(work) / "project"
    keyword = subprocess.run(
        [*COPY, "--data", "project_name=Class", str(TEMPLATE), str(project)],
        capture_output=True,
        text=True,
    )
    assert keyword.returncode and "Python keyword" in keyword.stderr, keyword.stderr

    subprocess.run(
        [
            *COPY,
            "--data",
            f"project_name={TITLE}",
            "--data",
            f"description={DESCRIPTION}",
            "--data",
            "project_slug=calendar",
            "--data",
            "package_name=calendar_app",
            "--data",
            "with_database=false",
            str(TEMPLATE),
            str(project),
        ],
        check=True,
    )
    backend = project / "backend"
    subprocess.run(["uv", "build", "--wheel"], cwd=backend, check=True)
    with ZipFile(next((backend / "dist").glob("*.whl"))) as wheel:
        assert "calendar_app/__init__.py" in wheel.namelist()
    schema = subprocess.check_output(["uv", "run", "calendar", "openapi"], cwd=backend)
    info = json.loads(schema)["info"]
    assert info["title"] == TITLE + " API" and info["description"] == DESCRIPTION, info
    subprocess.run(
        ["uv", "run", "ruff", "format", "--check", "."], cwd=backend, check=True
    )

    page = PageMetadata()
    page.feed((project / "frontend/index.html").read_text(encoding="utf-8"))
    assert page.title == TITLE and page.description == DESCRIPTION, (
        page.title,
        page.description,
    )
    # This check only needs the banner, even on runners without the generated visor's npm.
    doctor = subprocess.run(
        ["bash", "scripts/doctor.sh"], cwd=project, capture_output=True, text=True
    )
    assert doctor.stdout.splitlines()[0] == f"Checking tools for {TITLE}", doctor.stdout
