#!/usr/bin/env python3
import os
import sys
import shutil
import tempfile
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent
    source_png = base_dir / "entry.png"

    if not source_png.is_file():
        print(f"Error: Bundled entry.png not found at {source_png}", file=sys.stderr)
        sys.exit(1)

    output_dir_env = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    output_dir = Path(output_dir_env)
    output_dir.mkdir(parents=True, exist_ok=True)

    target_png = output_dir / "entry.png"
    source_size = source_png.stat().st_size

    # Staged copy using tempfile in output_dir for atomic os.replace on same filesystem
    fd, temp_path = tempfile.mkstemp(dir=output_dir, prefix="entry_", suffix=".tmp")
    os.close(fd)

    try:
        shutil.copyfile(source_png, temp_path)
        temp_size = Path(temp_path).stat().st_size

        if temp_size != source_size:
            print(f"Error: Size mismatch between source ({source_size}) and staged ({temp_size})", file=sys.stderr)
            os.unlink(temp_path)
            sys.exit(1)

        # CRITICAL: ensure world-readable mode 0644 before replace
        os.chmod(temp_path, 0o644)

        os.replace(temp_path, target_png)
    except Exception as e:
        print(f"Error deploying entry.png: {e}", file=sys.stderr)
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        sys.exit(1)

    # Verify deployed copy size
    deployed_size = target_png.stat().st_size
    if deployed_size != source_size:
        print(f"Error: Deployed size ({deployed_size}) does not match source ({source_size})", file=sys.stderr)
        sys.exit(1)

    print(f"Successfully deployed entry.png to {target_png} ({deployed_size} bytes, mode {oct(target_png.stat().st_mode)})")
    sys.exit(0)

if __name__ == "__main__":
    main()
