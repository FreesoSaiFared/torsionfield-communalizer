# Torsionfield Communalizer
Convert **any Git-based AI/agent repository** into an independent community edition.
This is not a GitHub fork: source, license, notices and upstream SHA are preserved;
the new repository receives its own Git history, ABP/browser task hub, verifiable
volunteer worker, MCP bridge, MCP Apps ui:// workbench and portable extension.

## Convert a repo
Prerequisites: Python 3.10+, Git, Node.js 22+; GitHub CLI if publishing.

    python3 communalize.py https://github.com/FreesoSaiFared/rea.git --name torsionfield-rea-communal --public
    python3 communalize.py https://github.com/owner/other-agent.git --name torsionfield-other-agent --private
    python3 communalize.py ./local-agent --name torsionfield-local-agent --local

Windows PowerShell: ./communalize.ps1 -Source https://github.com/owner/repo -Name torsionfield-example -Public
POSIX shell: ./communalize.sh SOURCE --name PROJECT --local

Every converted repository contains:
- Original code, documentation, notices and license unchanged.
- TORSIONFIELD.md and .torsionfield/project.json: identity and originating SHA.
- .torsionfield/hub.mjs: limited, persistent job/lease/receipt API on loopback.
- .torsionfield/web: ABP-compatible volunteer workbench; compute starts only on click.
- .torsionfield/mcp.mjs and mcp-ui.html: MCP tools and functional MCP Apps ui:// resource.
- .torsionfield/extension: portable Chrome MV3 extension for ABP/Brave.
- .torsionfield/COMMUNITY.md: contracts, contributor privacy and known limits.
- Disabled copies of inherited GitHub Actions workflows for review.

## Operate a community project
    cd projects/torsionfield-rea-communal
    node .torsionfield/hub.mjs
Browse http://127.0.0.1:19876/ from the machine running the hub. Open a second
tab and explicitly enable compute on both to share task shards. Each accepted
unit has SHA256 evidence and an independent verifier receipt.

## Test
    python3 tests/smoke.py

## Security and scope
This v0.1 prototype is a **local task network**. Public repo publication does
not publish or federate its live queue. Do not Internet-expose the hub: task
submissions have no authentication or anti-abuse gateway yet.
Volunteers execute allowlisted, bounded browser operations, never arbitrary code.
Agent-specific native or AI actions are proposals until deliberately connected
to an approved local adapter with participant consent.
Private source, credentials, sessions and device data must not enter public tasks.
Source license and third-party terms remain in force; project authorship stays intact.
The generated community code is independent and does not imply original author endorsement.
