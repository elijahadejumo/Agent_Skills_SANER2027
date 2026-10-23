"""Command taxonomy: types, effect levels, review labels, and the list of outside actions.

Every command (program plus subcommand) gets one of four labels (label()):
  program        - a known program, with a type and an effect level (classify())
  shell grammar  - shell keywords and builtins (if, for, echo, cd, ...)
  not a command  - text inside a code block that is not a command (code in other
                   languages, variable names, ordinary words)
  unreviewed     - rare names that were not reviewed
Every name used by at least 0.02% of skills was reviewed by hand (50 skills in Claude Code
folders, 333 across all folders); the review is recorded in HEADS, SHELL_GRAMMAR and
NOT_COMMANDS below.

REMOTE_WRITE is the list of outside actions (140 commands from 37 tools; see
outside_actions_docs.py for the documentation link of each):
  1. for every tool among the most common commands, all subcommands that its documentation
     describes as changing a remote service (git, gh, glab, kubectl, vercel, npm, pnpm, yarn,
     bun, cargo, uv, docker, gradle);
  2. the standard commands of other widely used tools for the actions Claude Code's
     documentation names as side effects (deploying, committing and pushing, sending
     messages), plus publishing packages and migrating databases.
Commands whose effect depends on their arguments (curl, ssh, scp, rsync, database clients,
general cloud CLIs) are never counted as outside actions, so counts built on this list are
lower bounds.
"""
import re


def _expand(spec):
    return {f"{head} {sub}".strip() for head, subs in spec.items() for sub in subs.split(",")}


REMOTE_WRITE = {
    "remote_vcs": {"git push"} | _expand({
        "gh pr": "create,merge,edit,comment,review,close,ready,reopen",
        "gh issue": "create,edit,comment,close,reopen,delete,transfer,pin,lock",
        "gh release": "create,edit,upload,delete",
        "gh label": "create,edit,delete,clone",
        "gh workflow": "run,enable,disable",
        "gh run": "rerun,cancel,delete",
        "gh repo": "create,fork,delete,edit,rename,archive,sync",
        "gh api": "post,patch,put,delete",
        "gh secret": "set,delete", "gh variable": "set,delete", "gh gist": "create,edit,delete",
        "gh project": "create,edit,item-add,item-edit,delete",
        "glab mr": "create,merge,note,approve,close,update",
        "glab issue": "create,note,close,update", "glab release": "create", "glab api": "post,patch,put,delete",
    }),
    "deploy": {"vercel"} | _expand({
        "kubectl": "apply,delete,rollout,scale,create,patch,edit,replace,label,annotate,set,drain,cordon,uncordon,"
                   "taint,expose,autoscale",
        "vercel": "deploy,promote,rollback,remove,rm,redeploy",
        # named categories, tools outside the head
        "helm": "install,upgrade,uninstall,rollback", "terraform": "apply,destroy", "pulumi": "up,destroy",
        "fly": "deploy", "flyctl": "deploy", "firebase": "deploy", "wrangler": "deploy,publish",
        "netlify": "deploy", "serverless": "deploy", "sam": "deploy", "cdk": "deploy,destroy", "railway": "up",
        "gcloud run": "deploy", "gcloud app": "deploy", "gcloud functions": "deploy",
    }),
    "publish": _expand({
        "npm": "publish,unpublish,deprecate", "pnpm": "publish", "yarn": "publish", "bun": "publish",
        "cargo": "publish", "uv": "publish", "docker": "push", "./gradlew": "publish", "gradle": "publish",
        "twine": "upload", "gem": "push", "poetry": "publish",
    }),
    "migrate": {"prisma migrate deploy", "supabase db push", "alembic upgrade", "flyway migrate", "rails db:migrate",
                "knex migrate:latest", "sequelize db:migrate", "drizzle-kit push", "drizzle-kit migrate",
                "php artisan migrate"},
}
REMOTE_WRITE_CATEGORY = {p: c for c, ps in REMOTE_WRITE.items() for p in ps}

READ, LOCAL_WRITE, EXECUTE, NETWORK, WRITE = ("read-only", "local write", "execute code",
                                              "network (read / arg-dependent)", "remote write")
LEVEL = {READ: 0, LOCAL_WRITE: 1, EXECUTE: 2, NETWORK: 3, WRITE: 4}

HEADS = {
    "Version control": "git jj rev-parse merge-base symbolic-ref rev-list cherry-pick worktree",
    "Code hosting": "gh glab",
    "Build, test & packages": "npm pnpm yarn bun pip pip3 pipx uv uvx poetry cargo go dotnet brew apt apt-get conda "
                              "composer gem bundle mvn ./mvnw gradle ./gradlew make just cmake ctest rake mix turbo nx "
                              "xcodebuild xcrun codesign swift flutter dart rustup nvm corepack mise nix winget pixi "
                              "bazel vite ng astro expo forge rails twine pre-commit husky tailwindcss .venv/bin/pip "
                              "pytest vitest jest tsc eslint ruff prettier mypy black flake8 pylint biome golangci-lint "
                              "shellcheck phpunit rspec pyright gofmt markdownlint-cli2 dnf dpkg clawhub clawdhub skillpacks",
    "Interpreters & scripts": "python python3 py node bash sh zsh deno tsx ts-node ruby perl php java rscript "
                              ".venv/bin/python powershell powershell.exe pwsh iex uvicorn",
    "File & text utilities": "grep rg cat head tail ls find sed awk jq yq wc sort uniq cut tr xargs diff mkdir cp mv rm "
                             "rmdir touch chmod ln tee tar zip unzip gzip base64 realpath dirname basename stat du df "
                             "tree fd less file readlink md5sum sha256sum shasum date which open pbcopy findstr comm "
                             "strings bc vim dd get-childitem get-content select-string sort-object where-object "
                             "select-object foreach-object convertto-json convertfrom-json test-path new-item "
                             "remove-item copy-item set-content out-file nano xxd format-table column",
    "Network clients": "curl wget ssh scp rsync http nc ping dig nslookup telnet sftp invoke-restmethod k6 "
                       "invoke-webrequest irm ngrok tailscale host httpx mcporter",
    "Containers & orchestration": "docker docker-compose podman kubectl oc helm minikube kind k3d",
    "Cloud & online services": "aws gcloud az vercel netlify fly flyctl firebase wrangler terraform pulumi heroku "
                               "railway sam cdk serverless supabase doctl eas databricks convex stripe hf sf shopify "
                               "gws lark-cli cast membrane pm agentuity gog vault",
    "Databases & migrations": "psql mysql sqlite3 redis-cli mongosh mongo prisma alembic flyway knex sequelize "
                              "drizzle-kit pg_dump pg_restore duckdb",
    "AI agent CLIs": "claude codex gemini aider opencode cursor-agent ollama llm claude-flow ruv-swarm hermes copilot",
    "Browser automation": "playwright agent-browser playwright-cli puppeteer google-chrome lighthouse",
    "System & processes": "systemctl launchctl kill pkill killall ps lsof tmux sleep timeout crontab osascript service "
                          "journalctl nohup screen chown defaults pgrep netstat ss mount uname hostname whoami sysctl "
                          "nvidia-smi security ip adb pm2 xdg-open start-process stop-process get-process taskkill "
                          "start-sleep import-module iptables ufw passwd reg net usermod",
    "Media & documents": "ffmpeg ffprobe pandoc pdftoppm pdftotext pdfimages pdftk qpdf magick sips xelatex pdflatex "
                         "bibtex latexmk quarto soffice mmdc yt-dlp remotion pdfinfo dot",
    "Security tools": "openssl gpg ssh-keygen nmap ffuf nuclei msfconsole tshark hashcat trivy semgrep gitleaks "
                      "bandit pip-audit govulncheck trufflehog checkov tcpdump sqlmap subfinder john op",
    "Other tools": "openspec unity-mcp-cli bd graphify uloop spectra infsh rtk qmd scholaraio eidetic cortextos "
                   "gooseworks openclaw rai steward onecli search-conversations hyperframes obsidian betterprompt samtools",
}
HEAD_CATEGORY = {h: c for c, hs in HEADS.items() for h in hs.split()}

SHELL_GRAMMAR = set("if then else elif fi case esac for while until do done in function select time { } ! [[ ]] "
                    "echo printf cd export set unset source . read exit return break continue local declare eval exec "
                    "test [ true false shift trap wait alias type pwd let umask ulimit setopt eof pyeof end begin "
                    "foreach write-host write-output out-null".split())
# names used by >=50 skills that, on review, are not commands: code from other languages,
# variable and field names, placeholders, and ordinary words inside code blocks
NOT_COMMANDS = set("""import from const get pr with ... api skills run use data url length repo closes d routing
clarification log where token except nodes id issue s def // secret body path and await the error result next order
add new task g create remote r name no failed password key tag pass describe try this status review p total m line
post text config isresolved content last release query fail update report show build json delete generated group
auth t limit c raise / mutation fix project thread .id check async all a headless fixes print title implement version
session api_key extract tokens start see user author code state out or ts description analyze fixme not n medium put
prompt you labels insert write assert output commit branch sql root seen analysis files keys minor exception summary
container main merged cost xxx class conn cmd join i lines free warn serve spec warning rows script edges src cap
questions safety cached detect communities missing paste login ast agent patch saved surprises detection gods
cohesion cost_path db br extraction output_tok input_tok f convert identify when to what code_files sem all_nodes
client payload deduped merged_nodes all_files merged_edges all_edges optional js watch verify all_hyperedges
merged_hyperedges your .body .name results refactor docs target label port search ci hack breaking install b cfg
top chunks model be req view info traceback raw on glob left tool total_out total_in rand values after copy updated
list skipped issues unique databaseid errors also current pageinfo high msg h doc first md as bearer src/
html github.com .env process /plugin lorem production usage""".split())

# heads that are also English words or short tokens: in unlabeled code blocks they are more likely prose
AMBIGUOUS = set("find open test sort head tail date which make touch cut diff kill time less file top watch split "
                "join wait read go bundle just service screen swift mix dart ip security oc sf hf bd forge rails "
                "expo astro task column host net dot pm copilot membrane hermes process".split())
SCRIPT = re.compile(r"^\.{1,2}/|^(\.?[\w.-]+/)*(scripts|bin|tools)/|\.(sh|py|js|mjs|ts|rb|pl|ps1)$")

GIT_READ = set("diff log status show blame rev-parse ls-files rev-list merge-base describe symbolic-ref shortlog "
               "grep cat-file reflog ls-tree for-each-ref check-ignore help version".split())
GIT_NETWORK = {"fetch", "clone", "pull", "ls-remote"}
INSTALL = set("install i ci add remove rm uninstall update upgrade sync lock init link unlink dedupe prune tap "
              "reinstall get".split())
QUERY = set("audit outdated view info list ls search show why version doctor config whoami".split())
WRITE_UTILS = set("mkdir cp mv rm rmdir touch chmod ln tee tar zip unzip gzip vim dd new-item remove-item copy-item "
                  "set-content out-file nano".split())
DOCKER_READ = set("ps logs images inspect info version stats top events history port".split())
HELM_LOCAL = set("template lint package create dependency repo show pull env version plugin".split())
SYS_WRITE = set("systemctl launchctl kill pkill killall service crontab chown defaults osascript mount iptables ufw "
                "passwd reg taskkill stop-process net usermod".split())
SYS_READ = set("ps lsof journalctl pgrep netstat ss uname hostname whoami sysctl nvidia-smi security ip "
               "get-process".split())
MEDIA_EFFECT = {"ffprobe": READ, "pdfinfo": READ, "yt-dlp": NETWORK, "remotion": EXECUTE}
SECURITY_EFFECT = {**dict.fromkeys("nmap ffuf nuclei msfconsole tshark tcpdump sqlmap subfinder".split(), NETWORK), "ssh-keygen": LOCAL_WRITE}


def classify(prefix):
    """(type, effect) for a command prefix, or None if it is not a recognised program."""
    toks = prefix.split()
    head, sub = toks[0], (toks[1] if len(toks) > 1 else "")
    cat = HEAD_CATEGORY.get(head)
    if cat is None:
        if head in SHELL_GRAMMAR or head in NOT_COMMANDS or not SCRIPT.search(head):
            return None
        return "Interpreters & scripts", EXECUTE      # a script shipped in the repository or skill
    if prefix in REMOTE_WRITE_CATEGORY:
        return cat, WRITE
    if cat == "Version control":
        if head != "git":
            return cat, READ if head in GIT_READ else LOCAL_WRITE
        return cat, READ if (sub in GIT_READ or not sub) else NETWORK if sub in GIT_NETWORK else LOCAL_WRITE
    if cat == "Code hosting":
        return cat, LOCAL_WRITE if (sub == "auth" or prefix.startswith("gh pr checkout")) else NETWORK
    if cat == "Build, test & packages":
        if sub in INSTALL:
            return cat, LOCAL_WRITE
        if head in ("brew", "apt", "apt-get", "conda", "pipx", "rustup", "nvm", "winget"):
            return cat, READ
        return cat, READ if sub in QUERY else EXECUTE
    if cat in ("Interpreters & scripts", "AI agent CLIs", "Browser automation", "Other tools"):
        return cat, EXECUTE
    if cat == "File & text utilities":
        return cat, LOCAL_WRITE if head in WRITE_UTILS else READ
    if cat == "Network clients":
        return cat, NETWORK
    if cat == "Containers & orchestration":
        if head in ("docker", "docker-compose", "podman"):
            return cat, READ if sub in DOCKER_READ else NETWORK if sub in ("pull", "login", "search") else EXECUTE
        if head in ("kubectl", "oc"):
            return cat, LOCAL_WRITE if sub == "config" else NETWORK
        if head == "helm":
            return cat, LOCAL_WRITE if sub in HELM_LOCAL else NETWORK
        return cat, EXECUTE
    if cat == "Databases & migrations":
        if head == "sqlite3":
            return cat, LOCAL_WRITE
        if head == "prisma" and sub in ("generate", "format", "validate", "studio", "init"):
            return cat, EXECUTE
        return cat, NETWORK
    if cat == "System & processes":
        return cat, LOCAL_WRITE if head in SYS_WRITE else READ if head in SYS_READ else EXECUTE
    if cat == "Media & documents":
        return cat, MEDIA_EFFECT.get(head, LOCAL_WRITE)
    if cat == "Security tools":
        return cat, SECURITY_EFFECT.get(head, EXECUTE)
    return cat, NETWORK  # cloud & online services outside the remote-write list: argument-dependent


def label(prefix):
    """program / shell grammar / not a command / unreviewed."""
    head = prefix.split()[0]
    if head in SHELL_GRAMMAR:
        return "shell grammar"
    if classify(prefix):
        return "program"
    if head in NOT_COMMANDS:
        return "not a command"
    return "unreviewed"


def census_commands(strict, unlabeled):
    """Commands counted in the census: all from shell-labelled blocks and inline code, and from
    unlabelled blocks only when the program name cannot be an English word."""
    keep = {p for p in unlabeled if p.split()[0] in HEAD_CATEGORY and p.split()[0] not in AMBIGUOUS}
    return set(strict) | keep
