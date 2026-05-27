#!/usr/bin/env python3

from pathlib import Path
import pprint

# ============================================================
# Settings
# ============================================================

input_parent = Path("/data/pt_03187/data/in_vivo/source")
output_parent = input_parent

name_storage_dir = "nii_loraks_recon"
output_config = Path("generated_loraks_config.py")

SKIP_PROCESSED = False

DUPLICATE_WARNING_THRESHOLD_GB = 1.0
DUPLICATE_WARNING_THRESHOLD_BYTES = DUPLICATE_WARNING_THRESHOLD_GB * 1024**3

PATTERNS = {
    "pdw_raw": ["pdw"],
    "t1w_raw": ["t1w"],
    "mtw_raw": ["mtw"],
    "ernst_raw": ["ernst"],
}


# ============================================================
# Helper functions
# ============================================================

def size_gb(path: Path) -> float:
    return path.stat().st_size / 1024**3


def is_processed(subject: str, session: str) -> bool:
    outdir = output_parent / subject / session / name_storage_dir
    return outdir.exists() and any(outdir.iterdir())


def find_largest_matching_file(
    raw_dir: Path,
    keywords: list[str],
    subject: str,
    session: str,
    contrast_name: str,
) -> str | None:
    candidates = []

    for f in raw_dir.glob("*.dat"):
        name = f.name.lower()

        if all(k.lower() in name for k in keywords):
            candidates.append(f)

    if not candidates:
        return None

    large_candidates = [
        f for f in candidates
        if f.stat().st_size > DUPLICATE_WARNING_THRESHOLD_BYTES
    ]

    if len(large_candidates) > 1:
        print()
        print("WARNING: duplicate large files detected")
        print(f"  Subject:  {subject}")
        print(f"  Session:  {session}")
        print(f"  Contrast: {contrast_name}")
        print(f"  Raw dir:  {raw_dir}")
        print("  Candidates > 1 GB:")

        for f in sorted(large_candidates, key=lambda p: p.stat().st_size, reverse=True):
            print(f"    {f.name}  ({size_gb(f):.2f} GB)")

        print("  Selected largest file:")
        largest_tmp = max(candidates, key=lambda p: p.stat().st_size)
        print(f"    {largest_tmp.name}  ({size_gb(largest_tmp):.2f} GB)")
        print()

    largest = max(candidates, key=lambda p: p.stat().st_size)
    return largest.name


def collect_sessions():
    sessions = []

    for subject_dir in sorted(input_parent.iterdir()):
        if not subject_dir.is_dir():
            continue

        subject = subject_dir.name

        for session_dir in sorted(subject_dir.iterdir()):
            if not session_dir.is_dir():
                continue

            session = session_dir.name
            raw_dir = session_dir / "raw"

            if not raw_dir.exists():
                continue

            dat_files = list(raw_dir.glob("*.dat"))

            if not dat_files:
                continue

            if SKIP_PROCESSED and is_processed(subject, session):
                print(f"Skipping already processed: {subject} / {session}")
                continue

            files = {
                key: find_largest_matching_file(
                    raw_dir=raw_dir,
                    keywords=keywords,
                    subject=subject,
                    session=session,
                    contrast_name=key,
                )
                for key, keywords in PATTERNS.items()
            }

            missing = [key for key, value in files.items() if value is None]

            if missing:
                print(f"WARNING: missing {missing}: {raw_dir}")
                continue

            sessions.append((subject, session, files))

    return sessions


def build_config(sessions):
    grouped = {}

    for subject, session, files in sessions:
        grouped.setdefault(subject, [])
        grouped[subject].append((session, files))

    sub_ses = []
    pdw_raw = []
    t1w_raw = []
    mtw_raw = []
    ernst_raw = []

    for subject, entries in sorted(grouped.items()):
        entries = sorted(entries, key=lambda x: x[0])

        sub_ses.append([
            subject,
            [session for session, _ in entries],
        ])

        pdw_raw.append([files["pdw_raw"] for _, files in entries])
        t1w_raw.append([files["t1w_raw"] for _, files in entries])
        mtw_raw.append([files["mtw_raw"] for _, files in entries])
        ernst_raw.append([files["ernst_raw"] for _, files in entries])

    return {
        "sub_ses": sub_ses,
        "pdw_raw": pdw_raw,
        "t1w_raw": t1w_raw,
        "mtw_raw": mtw_raw,
        "ernst_raw": ernst_raw,
    }


def write_config(config):
    with output_config.open("w") as f:
        f.write("#!/usr/bin/env python3\n\n")
        f.write("# Auto-generated LORAKS config.\n")
        f.write("# Inspect this file before running reconstruction.\n\n")

        f.write(f"sub_ses = {pprint.pformat(config['sub_ses'], width=120)}\n\n")

        f.write(f"input_parent = {str(input_parent)!r}\n")
        f.write(f"output_parent = {str(output_parent)!r}\n")
        f.write(f"name_storage_dir = {name_storage_dir!r}\n\n")

        f.write("with_smaps = False\n")
        f.write("smaps_per_session = 0\n\n")

        f.write("pdw_raw = ")
        f.write(pprint.pformat(config["pdw_raw"], width=120))
        f.write("\n\n")

        f.write("t1w_raw = ")
        f.write(pprint.pformat(config["t1w_raw"], width=120))
        f.write("\n\n")

        f.write("mtw_raw = ")
        f.write(pprint.pformat(config["mtw_raw"], width=120))
        f.write("\n\n")

        f.write("ernst_raw = ")
        f.write(pprint.pformat(config["ernst_raw"], width=120))
        f.write("\n\n")

        f.write("b1afi_ptx_raw = None\n")
        f.write("b1afi_stx_raw = None\n")


def main():
    sessions = collect_sessions()

    if not sessions:
        print("No complete sessions found.")
        return

    config = build_config(sessions)
    write_config(config)

    print()
    print(f"Found {len(sessions)} complete sessions.")
    print(f"Wrote config: {output_config.resolve()}")


if __name__ == "__main__":
    main()