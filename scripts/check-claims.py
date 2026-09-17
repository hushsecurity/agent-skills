#!/usr/bin/env python3
"""check-claims.py -- verify the skill's factual claims against the real sources.

The hush-uam-manifest skill asserts a lot about terraform-provider-hush and the Hush
API: which resources exist, which secrets may be omitted, which version floors apply.
Those claims were wrong three review cycles running, always in the same way -- a fact
inferred from one enforcement layer while another layer disagreed. This checks them
mechanically instead.

It needs the sibling repos checked out. Point at them with --provider and --midgard,
or keep them beside this one. Missing repos are skipped, not failed, so this stays
runnable without them.

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
    prov = provider / "internal/provider"
    for t, takes_priv in types.items():
        check(
            (prov / f"{t}_access_credential").is_dir(),
            f"credential resource missing for catalogued type `{t}`",
        )
        if takes_priv and t != "mariadb":  # mariadb's absence is documented
            check(
                (prov / f"{t}_access_privilege").is_dir(),
                f"privilege resource missing for `{t}`",
                "the catalog says it takes a privilege",
            )
    # The documented gap must still be a gap.
    check(
        not (prov / "mariadb_access_privilege").is_dir(),
        "mariadb privilege now exists",
        "the skill documents it as unavailable -- drop that note",
    )


def secret_facts(provider: Path, t: str) -> dict[str, bool]:
    common = provider / f"internal/provider/{t}_access_credential/common.go"
    resource = provider / f"internal/provider/{t}_access_credential/resource.go"
    if not common.exists():
        return {}
    c = common.read_text()
    r = resource.read_text() if resource.exists() else ""
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
            for d in (provider / "internal/provider").glob("*_access_credential")
            if secret_facts(provider, d.name.removesuffix("_access_credential")).get("exactly_one_of")
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
    for f in (midgard / "midgard/inventory").glob("*_access_creds.py"):
        m = re.search(r'MIN_ACCESS_MANAGER_VERSION: ClassVar\[str\] = "([\d.]+)"', f.read_text())
        if m:
            actual[f.name.removesuffix("_access_creds.py")] = m.group(1)
    # WIF types are named <t>_creds.py, not <t>_access_creds.py.
    for f in (midgard / "midgard/inventory").glob("*_creds.py"):
        if f.name.endswith("_access_creds.py"):
            continue
        m = re.search(r'MIN_ACCESS_MANAGER_VERSION: ClassVar\[str\] = "([\d.]+)"', f.read_text())
        if m:
            actual.setdefault(f.name.removesuffix("_creds.py"), m.group(1))

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
    redis = (midgard / "midgard/inventory/redis_access_creds.py").read_text()
    helpers = (midgard / "midgard/common/helpers.py").read_text()
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
        f = provider / f"internal/provider/{d}/common.go"
        if f.exists():
            check(
                needle not in f.read_text(),
                f"{label} now exists in the provider",
                "the skill documents it as unreachable",
            )

    pg = provider / "internal/provider/postgres_access_privilege/common.go"
    if pg.exists():
        m = re.search(r'StringInSlice\(\[\]string\{([^}]+)\}', pg.read_text())
        if m:
            n = len(re.findall(r'"[^"]+"', m.group(1)))
            check(n == 5, "postgres object_type count changed", f"provider now allows {n}, skill says 5")


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
    changelog = (provider / "CHANGELOG.md").read_text()
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
    args = ap.parse_args()

    skill_md = (SKILL / "SKILL.md").read_text()
    tf_md = (SKILL / "references/terraform.md").read_text()
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
    else:
        print(f"skipping midgard checks: {args.midgard} not found", file=sys.stderr)

    if failures:
        print(f"{len(failures)} of {checked} claims failed:\n")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"all {checked} claims hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
