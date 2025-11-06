import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.analyzer import AnalyzerManager
from transport.message import Analyzer as MessageAnalyzerKind, NetworkPacketMessage


class SnortAnalyzer(AnalyzerManager):
    """Analyzer that invokes Snort3 to inspect packet captures.

    The analyzer looks up the snort executable in this order:
    1) Environment variable SNORT_EXECUTABLE
    2) First 'snort' found on PATH

    Optionally, a Snort configuration may be provided. The analyzer searches for a
    usable snort.lua in this order unless explicitly provided via 'snort_config':
    1) Environment variable SNORT_CONFIG
    2) /etc/snort/snort.lua
    3) /usr/local/etc/snort/snort.lua
    4) <repo_root>/tmp/install/etc/snort/snort.lua
    """

    def __init__(self, snort_exec: Optional[str] = None, snort_config: Optional[str] = None, extra_args: Optional[List[str]] = None):
        self._snort_exec = snort_exec or os.environ.get("SNORT_EXECUTABLE") or shutil.which("snort")
        if not self._snort_exec:
            raise FileNotFoundError(
                "Snort executable not found. Install Snort3, add it to PATH, or set SNORT_EXECUTABLE."
            )
        self._snort_config = snort_config or self._discover_config()
        self._extra_args = extra_args or []

    def _discover_config(self) -> Optional[str]:
        # Respect explicit env var first
        env_cfg = os.environ.get("SNORT_CONFIG")
        if env_cfg and Path(env_cfg).is_file():
            return env_cfg

        # Common installation locations
        candidates = [
            Path("/etc/snort/snort.lua"),
            Path("/usr/local/etc/snort/snort.lua"),
        ]

        # Repo-local compiled install, if present
        repo_root = Path(__file__).resolve().parents[1]
        local_cfg = repo_root / "tmp" / "install" / "etc" / "snort" / "snort.lua"
        candidates.append(local_cfg)

        for p in candidates:
            if p.is_file():
                return str(p)
        return None

    def analyze(self, message: NetworkPacketMessage) -> Dict[str, Any]:
        if not isinstance(message, NetworkPacketMessage):
            raise TypeError("SnortAnalyzer requires a NetworkPacketMessage input")

        # Prepare a temporary pcap file with the capture bytes from the message.
        pcap_bytes = message.to_format_of_analyzer(MessageAnalyzerKind.Snort)
        with tempfile.NamedTemporaryFile(suffix=".pcap", delete=True) as tf:
            tf.write(pcap_bytes)
            tf.flush()

            # At this point _snort_exec is guaranteed to be non-None (constructor check)
            snort_exec: str = str(self._snort_exec)
            cmd: List[str] = [snort_exec]

            # Use a quiet mode if supported to reduce noise
            cmd += ["-q"]

            # Read from pcap file
            cmd += ["-r", tf.name]

            # If a configuration is available, include it
            if self._snort_config:
                cmd += ["-c", self._snort_config]

            # Prefer a simple alert output format if supported
            cmd += ["-A", "alert_fast"]

            # Append any caller-provided arguments last
            cmd += self._extra_args

            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

        stdout = proc.stdout
        stderr = proc.stderr
        rc = proc.returncode

        # Heuristic: consider any non-empty fast alert output or 'Alert' token as an attack
        raw_output = (stdout or "") + ("\n" + stderr if stderr else "")
        is_attack = False
        details = ""
        if "[**]" in raw_output or "Alert" in raw_output or "ALERT" in raw_output or "alert" in raw_output:
            is_attack = True
            details = "Snort reported alerts."
        elif rc != 0:
            details = f"Snort exited with code {rc}. See raw_output for details."
        else:
            details = "No alerts detected by Snort."

        return {
            "analyzer": "Snort",
            "is_attack": is_attack,
            "details": details,
            "return_code": rc,
            "raw_output": raw_output,
            "snort_exec": self._snort_exec,
            "snort_config": self._snort_config,
        }
