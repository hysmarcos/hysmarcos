"""Actualiza la sección "Latest activity" del README con la actividad pública reciente.

Lista los repos públicos con push más reciente (sin contar este) y su último commit.
Usa fechas absolutas: el README solo cambia cuando hay actividad nueva.
Uso: GITHUB_TOKEN=... python scripts/activity.py [usuario]
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "hysmarcos"
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- activity:start -->", "<!-- activity:end -->"
LIMIT = 5
# Repos que no se muestran en el perfil.
EXCLUDE = {"superprecios-claros", "cuerpo-ar-modelos"}


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": USER})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def rows():
    repos = get(f"https://api.github.com/users/{USER}/repos?type=owner&sort=pushed&per_page=30")
    out = []
    for repo in repos:
        if repo["fork"] or repo["private"] or repo["name"].lower() == USER.lower() or repo["name"] in EXCLUDE:
            continue
        commits = get(f"https://api.github.com/repos/{USER}/{repo['name']}/commits?per_page=1")
        if not commits:
            continue
        c = commits[0]
        msg = c["commit"]["message"].splitlines()[0].strip()
        msg = re.sub(r"[<>|\[\]]", "", msg)
        if len(msg) > 80:
            msg = msg[:78].rsplit(" ", 1)[0] + "…"
        day = c["commit"]["committer"]["date"][:10]
        out.append(f"| {day} | [{repo['name']}]({repo['html_url']}) | [{msg}]({c['html_url']}) |")
        if len(out) == LIMIT:
            break
    return out


def main():
    lines = rows()
    table = "| Date | Repository | Latest commit |\n|---|---|---|\n" + "\n".join(lines)
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    new = pattern.sub(f"{START}\n{table}\n{END}", text)
    if new != text:
        README.write_text(new, encoding="utf-8")
        print("README actualizado")
    else:
        print("Sin cambios")


if __name__ == "__main__":
    main()
