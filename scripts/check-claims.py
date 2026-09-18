#!/usr/bin/env python3
"""check-claims.py -- verify the skill's factual claims against the real sources.

The hush-uam-manifest skill asserts a lot about terraform-provider-hush and the Hush
API: which resources exist, which secrets may be omitted, which version floors apply.
Those claims were wrong three review cycles running, always in the same way -- a fact
inferred from one enforcement layer while another layer disagreed. This checks them
mechanically instead.

It needs the sibling repos checked out: terraform-provider-hush and midgard for the
Terraform and API claims, mufasa (the hush-uam operator) and helm-charts for the
Kubernetes ones. Point at them with --provider, --midgard, --mufasa and --helm-charts,
or keep them beside this one. Every repo is read at origin/main when the checkout has
it, since a sibling is often parked on a feature branch. Missing repos are skipped, not
failed, so this stays runnable without them.

    scripts/check-claims.py
    scripts/check-claims.py --provider ~/src/terraform-provider-hush

Exit 0 when every claim holds, 1 otherwise. This is a maintainer tool, deliberately
not wired into CI: it reads repos CI does not have.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "plugins/hush-uam/skills/hush-uam-manifest"

failures: list[str] = []
checked = 0


_refs: dict[Path, str] = {}


def main_ref(repo: Path) -> str:
    """origin/main when the checkout has it, else HEAD.

    A sibling checkout is often on someone's feature branch or months behind, and
    checking the skill against that would verify the wrong thing. Every read of a
    sibling repo goes through here.
    """
    if repo not in _refs:
        r = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify", "-q", "origin/main"],
            capture_output=True, text=True,
        )
        _refs[repo] = "origin/main" if r.returncode == 0 else "HEAD"
    return _refs[repo]


def git_show(repo: Path, path: str) -> str | None:
    """A file from the sibling repo's main branch, or None when it is not there."""
    r = subprocess.run(
        ["git", "-C", str(repo), "show", f"{main_ref(repo)}:{path}"],
        capture_output=True, text=True,
    )
    return r.stdout if r.returncode == 0 else None


def git_ls(repo: Path, directory: str) -> list[str]:
    """Entry names directly under a directory on the sibling repo's main branch."""
    r = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "--name-only", main_ref(repo), directory + "/"],
        capture_output=True, text=True,
    )
    return [line.rsplit("/", 1)[-1] for line in r.stdout.split()]


def check(ok: bool, label: str, detail: str = "") -> None:
    global checked
    checked += 1
    if not ok:
        failures.append(f"{label}{': ' + detail if detail else ''}")


def catalog_types(skill_md: str) -> dict[str, bool]:
    """Type name -> takes a privilege, from the SKILL.md catalog table."""
    types: dict[str, bool] = {}
    for line in skill_md.splitlines():
        m = re.match(r"^\| `([a-z_]+)` \| (\*\*no\*\*|yes¹?|no) \| \[`references/", line)
        if m:
            types[m.group(1)] = m.group(2).startswith("yes")
    return types


def check_resources(types: dict[str, bool], provider: Path) -> None:
    """Every catalogued type has the provider resources the skill implies."""
    resources = set(git_ls(provider, "internal/provider"))
    check(bool(resources), "could not list the provider's resources")
    for t, takes_priv in types.items():
        check(
            f"{t}_access_credential" in resources,
            f"credential resource missing for catalogued type `{t}`",
        )
        if takes_priv and t != "mariadb":  # mariadb's absence is documented
            check(
                f"{t}_access_privilege" in resources,
                f"privilege resource missing for `{t}`",
                "the catalog says it takes a privilege",
            )
    # The documented gap must still be a gap.
    check(
        "mariadb_access_privilege" not in resources,
        "mariadb privilege now exists",
        "the skill documents it as unavailable -- drop that note",
    )


def secret_facts(provider: Path, t: str) -> dict[str, bool]:
    c = git_show(provider, f"internal/provider/{t}_access_credential/common.go")
    if c is None:
        return {}
    r = git_show(provider, f"internal/provider/{t}_access_credential/resource.go") or ""
    return {
        "has_wo": "WriteOnly:" in c,
        "exactly_one_of": "ExactlyOneOf" in c and "WriteOnly:" in c,
        "customizediff": bool(re.search(r"func validate\w+\([^)]*\*schema\.ResourceDiff", r)),
        # An unconditional demand for a secret -- kafka/redis list them in `required`.
        # Distinct from a pairing guard, which only fires when an ID field is set
        # without its secret and so still permits omitting the whole pair.
        "requires_secret": bool(
            re.search(
                r"required = \[\]string\{[^}]*\b(password|token|secret_access_key|private_key)\b",
                r,
            )
        ),
    }


def bucket_lists(tf_md: str) -> dict[str, set[str]]:
    """The type names terraform.md puts in each secret-optionality bucket."""
    buckets = {
        "omittable": r"\*\*Omittable, but only as a whole pair\*\*(.*?)(?=\n- \*\*|\Z)",
        "per_engine": r"\*\*Required per engine, checked at plan\*\*(.*?)(?=\n- \*\*|\Z)",
        "pair": r"\*\*Required as a pair\*\*(.*?)(?=\n- \*\*|\Z)",
        "api_only": r"\*\*Required by the API but unchecked by the provider\*\*(.*?)(?=\n- \*\*|\Z)",
        "no_secret": r"The remaining four types have no secret argument at all:(.*?)(?=\n\n)",
    }
    out: dict[str, set[str]] = {}
    for name, pat in buckets.items():
        m = re.search(pat, tf_md, re.S)
        out[name] = set(re.findall(r"`([a-z_]+)`", m.group(1))) if m else set()
    return out


def check_secret_buckets(provider: Path, tf_md: str) -> None:
    """The classification that was wrong in three consecutive reviews."""
    b = bucket_lists(tf_md)

    check(bool(b["omittable"]), "could not parse the secret-optionality buckets")

    # Nothing in a "not ExactlyOneOf" bucket may actually carry ExactlyOneOf.
    for name in ("omittable", "per_engine", "pair", "api_only"):
        for t in b[name]:
            f = secret_facts(provider, t)
            if not f:
                continue
            check(
                not f["exactly_one_of"],
                f"`{t}` is listed under '{name}' but its secret pair is ExactlyOneOf",
            )

    # Plan-time buckets must have a CustomizeDiff; the API-only bucket must not.
    for t in b["per_engine"]:
        f = secret_facts(provider, t)
        if f:
            check(f["requires_secret"], f"`{t}` is claimed to require a secret per engine, but none is listed")
    for t in b["pair"]:
        f = secret_facts(provider, t)
        if f:
            check(f["customizediff"], f"`{t}` is claimed plan-checked but has no CustomizeDiff")
    for t in b["api_only"]:
        f = secret_facts(provider, t)
        if f:
            check(
                not f["customizediff"],
                f"`{t}` is claimed API-only but the provider has a CustomizeDiff",
            )

    # "Omittable" types may carry a pairing guard (ID without secret), but nothing
    # that demands a secret outright -- that was the kafka/redis error.
    for t in b["omittable"]:
        f = secret_facts(provider, t)
        if f:
            check(
                not f["requires_secret"],
                f"`{t}` is claimed omittable but the provider requires its secret outright",
            )

    # The no-secret bucket must really have no write-only argument.
    for t in b["no_secret"]:
        f = secret_facts(provider, t)
        if f:
            check(not f["has_wo"], f"`{t}` is claimed to have no secret but defines a _wo argument")

    # The stated count of ExactlyOneOf types.
    claimed = re.search(r"(\d+) of the 29 types mark the pair `ExactlyOneOf`", tf_md)
    if claimed:
        actual = sum(
            1
            for d in git_ls(provider, "internal/provider")
            if d.endswith("_access_credential")
            and secret_facts(provider, d.removesuffix("_access_credential")).get("exactly_one_of")
        )
        check(
            int(claimed.group(1)) == actual,
            f"terraform.md says {claimed.group(1)} types are ExactlyOneOf; the provider has {actual}",
        )


def check_floors(skill_md: str, midgard: Path) -> None:
    """Compatibility floors against midgard's MIN_ACCESS_MANAGER_VERSION."""
    declared: dict[str, str] = {}
    for line in skill_md.splitlines():
        m = re.match(r"^\| `([a-z_]+)` credential type.*?\| ([\d.]+) \|", line)
        if m:
            declared[m.group(1)] = m.group(2)

    actual: dict[str, str] = {}
    inventory = git_ls(midgard, "midgard/inventory")
    check(bool(inventory), "could not list midgard's inventory models")
    # Most types are <t>_access_creds.py; the WIF types are <t>_creds.py.
    for name in sorted(inventory, key=lambda n: not n.endswith("_access_creds.py")):
        if not name.endswith("_creds.py"):
            continue
        py = git_show(midgard, f"midgard/inventory/{name}") or ""
        m = re.search(r'MIN_ACCESS_MANAGER_VERSION: ClassVar\[str\] = "([\d.]+)"', py)
        if m:
            t = name.removesuffix("_access_creds.py").removesuffix("_creds.py")
            actual.setdefault(t, m.group(1))

    baseline = "0.13.0"
    for t, v in actual.items():
        if v == baseline:
            continue
        check(t in declared, f"`{t}` has an access-manager floor of {v} with no Compatibility row")
        if t in declared:
            check(
                declared[t] == v,
                f"`{t}` floor mismatch",
                f"skill says {declared[t]}, midgard says {v}",
            )
    for t, v in declared.items():
        check(
            t in actual,
            f"Compatibility claims a {v} floor for `{t}` that midgard does not have",
        )

    # Rows that are not a credential type: engines, features and the secret store.
    # Each is a constant somewhere in midgard rather than a MIN_ACCESS_MANAGER_VERSION.
    redis = git_show(midgard, "midgard/inventory/redis_access_creds.py") or ""
    helpers = git_show(midgard, "midgard/common/helpers.py") or ""
    sources = {
        "`redis` engine `elasticache`": re.search(
            r'RedisEngine\.ELASTICACHE:\s*return max\(cls\.MIN_ACCESS_MANAGER_VERSION, "([\d.]+)"', redis
        ),
        "`redis` engine `aiven`": re.search(
            r'HUSH_AIVEN_REDIS_MIN_AM_VERSION", "([\d.]+)"', redis
        ),
        "`redis` engine `azure_managed_redis`": re.search(
            r'HUSH_AZURE_MANAGED_REDIS_MIN_AM_VERSION", "([\d.]+)"', redis
        ),
        "`rabbitmq` `auto_rotate_root`": re.search(
            r'HUSH_ROOT_ROTATION_MIN_AM_VERSION", "([\d.]+)"', helpers
        ),
        "a secret store at all": re.search(
            r'HUSH_SECRET_STORE_MIN_AM_VERSION", "([\d.]+)"', helpers
        ),
        "an extended secret-store prefix": re.search(
            r'HUSH_EXTENDED_PREFIX_MIN_AM_VERSION", "([\d.]+)"', helpers
        ),
    }
    for label, m in sources.items():
        check(m is not None, f"could not find midgard's floor for {label}")
        if m is None:
            continue
        row = re.search(
            r"^\| " + re.escape(label) + r".*?\| ([\d.]+) \|$", skill_md, re.M
        )
        check(row is not None, f"no Compatibility row for {label}")
        if row is not None:
            check(
                row.group(1) == m.group(1),
                f"{label} floor mismatch",
                f"skill says {row.group(1)}, midgard says {m.group(1)}",
            )


def check_gaps(provider: Path, tf_md: str) -> None:
    """The 'Terraform cannot reach this' claims must still be true."""
    gaps = [
        ("gemini_access_credential", "service_account_bound", "gemini service_account_bound"),
        ("sendgrid_access_credential", '"host"', "sendgrid host"),
        ("elasticsearch_access_credential", '"api_key"', "elasticsearch api_key"),
        ("azure_app_access_privilege", "graph_api_permissions", "azure_app graph_api_permissions"),
    ]
    for d, needle, label in gaps:
        src = git_show(provider, f"internal/provider/{d}/common.go")
        if src is not None:
            check(
                needle not in src,
                f"{label} now exists in the provider",
                "the skill documents it as unreachable",
            )

    pg = git_show(provider, "internal/provider/postgres_access_privilege/common.go")
    if pg is not None:
        m = re.search(r'StringInSlice\(\[\]string\{([^}]+)\}', pg)
        if m:
            n = len(re.findall(r'"[^"]+"', m.group(1)))
            check(n == 5, "postgres object_type count changed", f"provider now allows {n}, skill says 5")


SECRET_TYPES = re.compile(
    r"^\s+(\w+):\s*(?:Password|ClientSecret|PrivateKey|PrivateKeySecret|"
    r"ServiceAccountKey|ApiToken|JWT|SecretStr|Secret\[)",
    re.M,
)


def request_model_fields(py: str) -> set[str]:
    """Field names of the create request model (`class <X>In(...)`), the contract."""
    m = re.search(r"^class \w+In\(.*?\):\n(.*?)(?=^class |\Z)", py, re.S | re.M)
    body = m.group(1) if m else py
    return set(re.findall(r"^\s+(\w+):\s*\w", body, re.M))


def check_secret_keys(midgard: Path) -> None:
    """Each type's `secretRef` keys line names midgard's secret-typed fields."""
    for md in sorted((SKILL / "references").glob("*.md")):
        t = md.stem
        if t == "kv":  # its keys are the user's own, not model fields
            continue
        py = git_show(midgard, f"midgard/api/dynamic_{t}.py")
        if py is None:
            py = git_show(midgard, f"midgard/api/{t}_access_creds.py")
        if py is None:
            continue
        secret = set(SECRET_TYPES.findall(py))
        fields = request_model_fields(py)
        claimed: set[str] = set()
        for line in re.findall(r"`secretRef` keys?: (.*)", md.read_text()):
            claimed |= set(re.findall(r"`([a-z_]+)`", line))
        if not secret and not claimed:
            continue
        check(
            secret <= claimed,
            f"`{t}` secretRef keys miss a secret field",
            f"midgard marks {sorted(secret - claimed)} secret",
        )
        check(
            claimed <= fields,
            f"`{t}` secretRef keys name a field midgard does not have",
            f"{sorted(claimed - fields)}",
        )


def check_operator(skill_md: str, k8s_md: str, mufasa: Path) -> None:
    """Kubernetes claims against the api-controller (hush-uam) source."""
    types_go = git_show(mufasa, "internal/api_controller/api/v1alpha1/types_accesspolicy.go")
    helpers_go = git_show(mufasa, "internal/api_controller/helpers.go")
    check(bool(types_go and helpers_go), "could not read the operator source")
    if not (types_go and helpers_go):
        return

    m = re.search(
        r"type AttestationCriterion struct \{.*?validation:Enum=(.*?)\n", types_go, re.S
    )
    enum = set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()
    check(bool(enum), "could not find the attestation enum on AttestationCriterion")
    declared = set(re.findall(r"^\| `(k8s:[a-z-]+)` \|", skill_md, re.M))
    check(enum == declared, "attestation criteria enum", f"skill {sorted(declared)}, operator {sorted(enum)}")

    states = set(re.findall(r'SyncState\w+\s*=\s*"(\w+)"', helpers_go))
    check(bool(states), "could not find the operator's sync states")
    m = re.search(r"sync state, one of (.*?)\.", k8s_md, re.S)
    listed = re.sub(r"\([^)]*\)", "", m.group(1)) if m else ""  # drop asides
    documented = set(re.findall(r"`(\w+)`", listed))
    check(
        documented == states,
        "kubernetes.md sync states disagree with the operator",
        f"skill {sorted(documented)}, operator {sorted(states)}",
    )

    m = re.search(r'foreignIDKey\s*=\s*"(\w+)"', helpers_go)
    if m:
        check(
            f"`{m.group(1)}`" in k8s_md,
            "kubernetes.md does not name the controller-owned config field",
            m.group(1),
        )

    # The plaintext rule: a single-entry Secret needs no keyMappings, more is an error.
    check(
        "mergeSecretIntoPlaintextField" in helpers_go
        and re.search(r"exactly \**one\**\s+entry", k8s_md) is not None,
        "the plaintext single-entry Secret rule is not documented or no longer exists",
    )


def check_chart(skill_md: str, helm: Path) -> None:
    """The hush-uam column of Compatibility is the chart's appVersion."""
    log = subprocess.run(
        ["git", "-C", str(helm), "log", main_ref(helm), "--format=%h", "--", "charts/hush-am/Chart.yaml"],
        capture_output=True, text=True,
    )
    app_of: dict[str, str] = {}
    for sha in log.stdout.split():
        y = subprocess.run(
            ["git", "-C", str(helm), "show", f"{sha}:charts/hush-am/Chart.yaml"],
            capture_output=True, text=True,
        ).stdout
        v = re.search(r"^version:\s*(\S+)", y, re.M)
        a = re.search(r'^appVersion:\s*"?(v[\d.]+)', y, re.M)
        if v and a:
            app_of.setdefault(v.group(1), a.group(1))
    check(bool(app_of), "could not map chart versions to appVersions", "is the checkout shallow or not a git repo?")
    if not app_of:
        return

    def vkey(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.split("."))

    newest = max(app_of, key=vkey)
    for line in skill_md.splitlines():
        m = re.match(r"^\| (.+?) \| (v[\d.]+|—) \| ([\d.]+) \|$", line)
        if not m:
            continue
        feature, uam, chart = m.groups()
        if chart not in app_of:
            # A floor ahead of every release is a documented Unreleased dependency;
            # anything else is a chart version that never existed.
            check(
                vkey(chart) > vkey(newest),
                f"{feature}: chart {chart} not found in helm-charts history",
                f"newest released is {newest}",
            )
            continue
        if uam != "—":
            check(
                app_of[chart] == uam,
                f"{feature}: hush-uam column disagrees with the chart",
                f"skill says {uam}, chart {chart} ships {app_of[chart]}",
            )

    changelog = git_show(helm, "charts/hush-am/CHANGELOG.md") or ""
    sections = re.split(r"^## (?:hush-am )?(Unreleased|[\d.]+)\b.*$", changelog, flags=re.M)
    # sections = [preamble, ver1, body1, ver2, body2, ...]; oldest mention wins.
    first = None
    for ver, body in zip(sections[1::2], sections[2::2]):
        if "remoteName" in body:
            first = ver
    m = re.search(r"^\| `remoteName`.*?\| v[\d.]+ \| ([\d.]+) \|$", skill_md, re.M)
    if first and m:
        check(first == m.group(1), "remoteName chart floor", f"skill says {m.group(1)}, changelog says {first}")


def check_provider_release(tf_md: str, skill_md: str, provider: Path) -> None:
    """The pinned `~> X.Y` and the 'not in X.Y.x' note track the provider's releases."""
    tags = subprocess.run(
        ["git", "-C", str(provider), "tag", "--sort=-v:refname"],
        capture_output=True, text=True,
    ).stdout.split()
    tags = [t for t in tags if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    check(bool(tags), "no release tags in the provider checkout", "fetch tags")
    if not tags:
        return
    newest = tags[0].lstrip("v")
    minor = ".".join(newest.split(".")[:2])

    pins = set(re.findall(r'~> (\d+\.\d+)\b', tf_md + skill_md))
    check(
        pins == {minor},
        "provider version pin is stale",
        f"skill pins {sorted(pins)}, newest release is {newest}",
    )
    xs = set(re.findall(r"\b(\d+\.\d+)\.x\b", tf_md))
    check(
        xs <= {minor},
        "terraform.md names a provider minor that is not the current one",
        f"{sorted(xs)} vs {minor}",
    )

    # The per-kind prefix rules are described as Unreleased; once they ship the note
    # (and the plain-prefix advice that goes with it) has to go.
    changelog = git_show(provider, "CHANGELOG.md") or ""
    sections = re.split(r"^## \[(Unreleased|[\d.]+)\].*$", changelog, flags=re.M)
    where = next(
        (ver for ver, body in zip(sections[1::2], sections[2::2])
         if "Per-kind secret store prefixes" in body),
        None,
    )
    check(where is not None, "could not find the per-kind prefix entry in the provider CHANGELOG")
    if where is not None:
        claims_unreleased = "`[Unreleased]` section" in tf_md
        check(
            (where == "Unreleased") == claims_unreleased,
            "the per-kind prefix note in terraform.md is stale",
            f"CHANGELOG puts it under {where}",
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", type=Path, default=REPO.parent / "terraform-provider-hush")
    ap.add_argument("--midgard", type=Path, default=REPO.parent / "midgard")
    ap.add_argument("--mufasa", type=Path, default=REPO.parent / "mufasa")
    ap.add_argument("--helm-charts", type=Path, default=REPO.parent / "helm-charts")
    args = ap.parse_args()

    skill_md = (SKILL / "SKILL.md").read_text()
    tf_md = (SKILL / "references/terraform.md").read_text()
    k8s_md = (SKILL / "references/kubernetes.md").read_text()
    types = catalog_types(skill_md)

    check(len(types) == 29, "catalog type count", f"found {len(types)}, expected 29")
    for t in types:
        check((SKILL / f"references/{t}.md").exists(), f"no reference file for catalogued type `{t}`")

    if args.provider.is_dir():
        check_resources(types, args.provider)
        check_secret_buckets(args.provider, tf_md)
        check_gaps(args.provider, tf_md)
        check_provider_release(tf_md, skill_md, args.provider)
    else:
        print(f"skipping provider checks: {args.provider} not found", file=sys.stderr)

    if args.midgard.is_dir():
        check_floors(skill_md, args.midgard)
        check_secret_keys(args.midgard)
    else:
        print(f"skipping midgard checks: {args.midgard} not found", file=sys.stderr)

    if args.mufasa.is_dir():
        check_operator(skill_md, k8s_md, args.mufasa)
    else:
        print(f"skipping operator checks: {args.mufasa} not found", file=sys.stderr)

    if args.helm_charts.is_dir():
        check_chart(skill_md, args.helm_charts)
    else:
        print(f"skipping chart checks: {args.helm_charts} not found", file=sys.stderr)

    if failures:
        print(f"{len(failures)} of {checked} claims failed:\n")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"all {checked} claims hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
