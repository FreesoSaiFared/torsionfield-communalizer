#!/usr/bin/env python3
"""Independent Git-repo -> Torsionfield ABP community project."""
import argparse
import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent

def cmd(*args, cwd=None):
    p = subprocess.run([str(v) for v in args], cwd=cwd, text=True,
                       capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-1300:])
    return p.stdout.strip()

def create(source, name, owner, workspace, visibility):
    target = workspace / name
    if target.exists():
        raise ValueError("Destination exists: " + str(target))
    workspace.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tf-source-") as temp:
        root = Path(temp) / "source"
        cmd("git", "clone", "--depth", "1", source, root)
        sha = cmd("git", "rev-parse", "HEAD", cwd=root)
        branch = cmd("git", "branch", "--show-current", cwd=root)
        if visibility == "public" and not any((root / f).exists()
                for f in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")):
            raise ValueError("Cannot publish source without reviewing its license")
        shutil.copytree(root, target, ignore=shutil.ignore_patterns(".git"),
                        symlinks=True)
    overlay = target / ".torsionfield"
    if overlay.exists():
        raise ValueError("Upstream already has a .torsionfield directory")
    shutil.copytree(HERE / "template", overlay)
    workflows = target / ".github" / "workflows"
    if workflows.is_dir():
        shutil.move(str(workflows), str(overlay / "upstream-workflows-disabled"))
    detected = [kind for kind, names in {
        "node": ("package.json",), "python": ("pyproject.toml", "requirements.txt"),
        "rust": ("Cargo.toml",), "go": ("go.mod",),
        "mcp": ("mcp.json", ".mcp.json")}.items()
        if any((target / filename).exists() for filename in names)]
    data = {
        "schemaVersion": "torsionfield.community/v1",
        "project": {"id": name, "name": name, "origin": source,
                    "originCommit": sha, "originBranch": branch,
                    "convertedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "repository": "https://github.com/" + owner + "/" + name if owner else None},
        "agent": {"detectedStacks": detected, "adapter": None,
                  "mcpServer": "node .torsionfield/mcp.mjs"},
        "community": {"participation": "opt-in", "contributorPrivacy": "local-by-default",
                      "workerCode": "allowlisted-only",
                      "taskTypes": ["prime-range", "digest-text", "agent-request"],
                      "agentRequests": "proposal-only"}
    }
    (overlay / "project.json").write_text(json.dumps(data, indent=2) + "\n")
    (target / "TORSIONFIELD.md").write_text(
        "# " + name + ": Torsionfield Community Edition\n\n"
        "Source: " + source + "\n\nSource revision: " + sha + "\n\n"
        "Independent derivative; original license and notices retained.\n\n"
        "Start the community task hub: node .torsionfield/hub.mjs\n\n"
        "Open http://127.0.0.1:19876/ to propose work or explicitly donate "
        "ABP/browser compute. Browser work is allowlisted; other agent tasks "
        "are proposals pending review and a separately approved adapter.\n\n"
        "MCP stdio entry: node .torsionfield/mcp.mjs\n\n"
        "See .torsionfield/COMMUNITY.md for API and deployment limits.\n")
    with (target / ".gitignore").open("a") as f:
        f.write("\n# Community-local state\n.torsionfield/state/\n.torsionfield/*.token\n")
    cmd("git", "init", "-b", "main", target)
    cmd("git", "config", "user.name", "Torsionfield Communalizer", cwd=target)
    cmd("git", "config", "user.email", "automation@users.noreply.github.com", cwd=target)
    cmd("git", "add", "-A", cwd=target)
    cmd("git", "commit", "-m", "Torsionfield community conversion of " + source, cwd=target)
    url = None
    if visibility != "local":
        cmd("gh", "repo", "create", owner + "/" + name,
            "--" + visibility, "--source", target,
            "--remote", "origin", "--push",
            "--description", "Opt-in ABP community edition of " + source)
        url = "https://github.com/" + owner + "/" + name
    receipt = {"path": str(target), "source": source, "sourceSha": sha,
               "newSha": cmd("git", "rev-parse", "HEAD", cwd=target),
               "repo": url, "visibility": visibility}
    print(json.dumps(receipt, indent=2))
    return receipt

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", help="Any Git clone URL or local Git repository")
    p.add_argument("--name", help="Independent new GitHub repository name")
    p.add_argument("--owner", help="GitHub account, default authenticated account")
    p.add_argument("--workspace", type=Path, default=HERE / "projects")
    visibility = p.add_mutually_exclusive_group(required=True)
    visibility.add_argument("--public", action="store_true")
    visibility.add_argument("--private", action="store_true")
    visibility.add_argument("--local", action="store_true")
    a = p.parse_args()
    leaf = re.sub(r"\.git$", "", a.source.rstrip("/").split("/")[-1])
    name = a.name or ("torsionfield-" + leaf + "-communal")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{2,79}", name):
        p.error("Invalid new repository name")
    owner = a.owner or (cmd("gh", "api", "user", "-q", ".login")
                        if not a.local else "")
    mode = "public" if a.public else "private" if a.private else "local"
    create(a.source, name.lower(), owner, a.workspace.resolve(), mode)

if __name__ == "__main__":
    main()
