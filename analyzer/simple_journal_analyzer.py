from typing import Any, Dict
import json
import re

from api.analyzer import AnalyzerManager
from transport.message import JournalMessage, Analyzer as MessageAnalyzerKind


class SimpleJournalAnalyzer(AnalyzerManager):
    """Pass-through analyzer for journalctl entries.

    Consumes a JournalMessage and returns the original dict entries without
    transformation. Useful for piping logs to downstream consumers or for simple
    display.
    """

    def analyze(self, message: JournalMessage) -> Dict[str, Any]:
        if not isinstance(message, JournalMessage):
            raise TypeError("SimpleJournalAnalyzer requires a JournalMessage input")

        raw_bytes = message.to_format_of_analyzer(MessageAnalyzerKind.SimpleJournal)
        json_obj = json.loads(raw_bytes.decode("utf-8", errors="replace"))
        attack_entries = []
        pattern = re.compile(r"invalid user ([a-zA-Z0-9_]+) from ((\d+\.){3}(\d+))")
        for e in json_obj:
            msg: str = e["MESSAGE"]
            match_ = pattern.search(msg.lower())
            if match_:
                attack_entries.append((match_.group(1), match_.group(2)))
        if not attack_entries:
            return {
                "is_attack": False
            }
        attack_users = {}
        attack_ips = {}
        for user, ip in attack_entries:
            if user not in attack_users:
                attack_users[user] = 0
            if ip not in attack_ips:
                attack_ips[ip] = 0
            attack_users[user] += 1
            attack_ips[ip] += 1
        return {
            "is_attack": True,
            "attack_users": [
                {"username": user, "count": count} for user, count in attack_users.items()
            ],
            "attack_ips": [
                {"ip": ip, "count": count} for ip, count in attack_ips.items()
            ]
        }