"""Exercise rendered commit guidance and real Copier upgrades, without project dependencies.

Needs git, Copier and the v0.10.0 tag (CI fetches full history). Uses a disposable template
repository so the working tree, tags and generated projects of the caller are never changed.
"""

import io
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
GIT = ["git", "-c", "user.name=template-ci", "-c", "user.email=ci@example.invalid"]
GUIDANCE = ["AGENTS.md", ".agents/skills/ship-a-change/SKILL.md", "README.md"]


def run(*args, cwd):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(f"{args}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def commit(repo, message):
    run(*GIT, "add", "-A", cwd=repo)
    run(*GIT, "commit", "--allow-empty", "-qm", message, cwd=repo)


def copy(template, project, *data):
    run(
        "copier",
        "copy",
        "--defaults",
        "--quiet",
        *data,
        str(template),
        str(project),
        cwd=SOURCE,
    )
    run(*GIT, "init", "-q", "-b", "main", cwd=project)
    commit(project, "Generate project")


def update(project, *data):
    commit(project, "Save before update")
    run(
        "copier",
        "update",
        "--defaults",
        "--quiet",
        "--conflict",
        "inline",
        *data,
        cwd=project,
    )
    assert not list(project.rglob("*.rej")), "Copier left rejected patches"
    for path in project.rglob("*"):
        if path.is_file() and not path.is_symlink() and ".git" not in path.parts:
            text = path.read_text()
            assert not any(
                line.startswith(("<<<<<<<", ">>>>>>>")) for line in text.splitlines()
            ), path


def check(project, style):
    answers = (project / ".copier-answers.yml").read_text()
    assert f"commit_style: {style}\n" in answers, answers
    for relative in GUIDANCE:
        text = (project / relative).read_text()
        assert f"`commit_style={style}`" in text, relative
        assert "{{" not in text and "{%" not in text, relative
        if style == "gitmoji":
            assert "🐛 Reject expired sessions" in text, relative
        else:
            assert "Fix expired session handling" in text, relative
            assert not any(
                emoji in text
                for emoji in ("✨", "🐛", "📝", "♻", "✅", "👷", "⬆", "🔧")
            ), relative
    skill = (project / GUIDANCE[1]).read_text()
    assert skill.count('--subject "$pr_title"') == 3, (
        "All merge paths must set the subject"
    )
    assert "git show -s --format=%s <merge-sha>" in skill


with tempfile.TemporaryDirectory(prefix="fsb-commit-style-") as directory:
    work = Path(directory)
    template = work / "template"
    template.mkdir()
    # A genuine released template without this question, not just a deleted saved answer.
    archive = subprocess.check_output(["git", "archive", "v0.10.0"], cwd=SOURCE)
    with tarfile.open(fileobj=io.BytesIO(archive)) as files:
        files.extractall(template, filter="data")
    run(*GIT, "init", "-q", "-b", "main", cwd=template)
    commit(template, "Template before commit style")
    run(*GIT, "tag", "v0.0.1", cwd=template)

    legacy = [work / "legacy-default", work / "legacy-plain"]
    for project in legacy:
        copy(template, project)
        assert "commit_style:" not in (project / ".copier-answers.yml").read_text()
        readme = project / "README.md"
        readme.write_text(
            "Project-specific guidance to preserve.\n\n" + readme.read_text()
        )

    for path in template.iterdir():
        if path.name != ".git":
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
    shutil.copytree(
        SOURCE,
        template,
        dirs_exist_ok=True,
        symlinks=True,
        ignore=shutil.ignore_patterns(".git", ".venv", "node_modules", "__pycache__"),
    )
    commit(template, "Template with commit style")
    run(*GIT, "tag", "v0.0.2", cwd=template)

    projects = [
        (work / "default", "gitmoji"),
        (work / "gitmoji", "gitmoji"),
        (work / "plain", "plain"),
    ]
    for project, style in projects:
        flags = [] if project.name == "default" else ["--data", f"commit_style={style}"]
        copy(template, project, *flags)
        check(project, style)

    invalid = subprocess.run(
        [
            "copier",
            "copy",
            "--defaults",
            "--quiet",
            "--data",
            "commit_style=unknown",
            str(template),
            str(work / "invalid"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert invalid.returncode, "Invalid commit style was accepted"

    for project, style in zip(legacy, ["gitmoji", "plain"], strict=True):
        flags = [] if style == "gitmoji" else ["--data", "commit_style=plain"]
        update(project, *flags)
        check(project, style)
        assert (
            "Project-specific guidance to preserve."
            in (project / "README.md").read_text()
        )
        projects.append((project, style))

    # A later release must preserve both saved answers while applying a real template change.
    marker = "A later template release keeps the saved commit style."
    with (template / "template/AGENTS.md.jinja").open("a") as agents:
        agents.write(f"\n{marker}\n")
    commit(template, "Later template change")
    run(*GIT, "tag", "v0.0.3", cwd=template)
    for project, style in projects:
        update(project)
        check(project, style)
        assert marker in (project / "AGENTS.md").read_text()

    # Explicit overrides must replace all three instruction surfaces and survive another update.
    for style in ["plain", "gitmoji"]:
        project = projects[0][0]
        update(project, "--data", f"commit_style={style}")
        check(project, style)
        update(project)
        check(project, style)

print(
    "Commit styles: generation, validation, legacy upgrades, persistence and switching passed."
)
