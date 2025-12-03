"""Message transport primitives shared between monitor backends and analyzers.

This module defines the wire protocol between the monitoring component (which
captures raw telemetry) and analyzer components (which perform detection or
summarization).  Additional message types should extend the :class:`Message`
interface so analyzers can declare which artifacts they understand and how
those artifacts are serialized.
"""

from enum  import Enum
from abc import ABC, abstractmethod
from typing import override, Sequence
import pickle
import scapy.all as scapy
import tempfile
import json

class MessageKind(Enum):
    """Enumerates logical categories of data exchanged between modules."""

    NetworkPacket = 1
    Journal = 2

class Analyzer(Enum):
    """Enumerates analyzers that can consume transport messages."""

    Snort = 1
    LLM = 2
    SimpleJournal = 3

class Message(ABC):
    """Base contract for any payload exchanged between monitor and analyzer."""

    @property
    @abstractmethod
    def kind(self) -> MessageKind:
        """Return the high-level category of this message."""
        pass

    @property
    @abstractmethod
    def json_obj(self) -> dict:
        """Return a JSON-serializable representation of the message."""
        pass

    @classmethod
    @abstractmethod
    def load(cls, json_obj: dict) -> "Message":
        """Instantiate a message from the serialized JSON representation."""
        pass

    @abstractmethod
    def supported_analyzers(self) -> set[Analyzer]:
        """Return analyzers that can consume this message without conversion."""
        pass

    def to_format_of_analyzer(self, analyzer: Analyzer) -> bytes:
        if analyzer not in self.supported_analyzers():
            raise ValueError(f"Analyzer {analyzer} is not supported by this message")
        return self._to_format_of_analyzer(analyzer)

    @abstractmethod
    def _to_format_of_analyzer(self, analyzer: Analyzer) -> bytes:
        """Convert the message into analyzer-specific bytes ready for ingestion."""
        pass

class LinkLayerType(Enum):
    """Link-layer encapsulations supported when decoding packet captures."""

    Ethernet = 1
    WiFi = 2

class NetworkPacketMessage(Message):
    """Carries one or more captured packets for downstream inspection."""

    def __init__(self, packets: Sequence[scapy.Packet]):
        self._packets = packets

    @property
    @override
    def kind(self) -> MessageKind:
        return MessageKind.NetworkPacket

    @property
    @override
    def json_obj(self) -> dict:
        return {
            "packets": [
                {
                    "pickled_data": pickle.dumps(packet).hex()
                }
                for packet in self._packets
            ]
        }

    @classmethod
    @override
    def load(cls, json_obj: dict) -> "NetworkPacketMessage":
        packets = [
            pickle.loads(bytes.fromhex(packet_dict["pickled_data"]))
            for packet_dict in json_obj["packets"]
        ]
        return cls(packets)

    @override
    def supported_analyzers(self) -> set[Analyzer]:
        return {Analyzer.Snort, Analyzer.LLM}

    def _to_format_of_analyzer(self, analyzer: Analyzer) -> bytes:
        match analyzer:
            case Analyzer.Snort:
                return self._to_snort_format()
            case Analyzer.LLM:
                return self._to_llm_format()
        raise ValueError(f"Unsupported analyzer {analyzer} for NetworkPacketMessage")

    def _to_snort_format(self) -> bytes:
        with tempfile.NamedTemporaryFile() as temp_pcap:
            scapy.wrpcap(temp_pcap.name, self._packets)
            temp_pcap.seek(0)
            pcap_data = temp_pcap.read()
        return pcap_data

    def _to_llm_format(self) -> bytes:
        packets_prompts = []
        for packet in self._packets:
            packet_summary = packet.summary()
            packet_hexdump = scapy.hexdump(packet, dump=True)
            prompt = f"Packet Summary:\n{packet_summary}\n\nHexdump:\n{packet_hexdump}\n"
            packets_prompts.append(prompt)
        full_prompt = "Analyze the following network packets we captured:\n\n" + "\n---\n".join(packets_prompts)
        return full_prompt.encode('utf-8')

class JournalMessage(Message):
    """Carries journalctl log entries for analyzers.

    This message encapsulates one or more journalctl JSON objects (dicts).
    It preserves the original dicts for pass-through in SimpleJournal analyzer
    and can convert them into an LLM-friendly prompt for the LLM analyzer.
    """

    def __init__(self, entries: Sequence[dict]):
        self._entries = list(entries)

    @property
    @override
    def kind(self) -> MessageKind:
        return MessageKind.Journal

    @property
    @override
    def json_obj(self) -> dict:
        # Entries are already JSON-serializable dicts from journalctl output
        return {
            "entries": self._entries,
        }

    @classmethod
    @override
    def load(cls, json_obj: dict) -> "JournalMessage":
        entries = json_obj.get("entries", [])
        if not isinstance(entries, list):
            raise ValueError("JournalMessage 'entries' must be a list")
        return cls(entries)

    @override
    def supported_analyzers(self) -> set[Analyzer]:
        return {Analyzer.LLM, Analyzer.SimpleJournal}

    def _to_format_of_analyzer(self, analyzer: Analyzer) -> bytes:
        match analyzer:
            case Analyzer.SimpleJournal:
                return self._to_simple_journal_format()
            case Analyzer.LLM:
                return self._to_llm_format()
        raise ValueError(f"Unsupported analyzer {analyzer} for JournalMessage")

    def _to_simple_journal_format(self) -> bytes:
        # Pass-through: original dicts as JSON array
        return json.dumps(self._entries, ensure_ascii=False).encode("utf-8")

    def _to_llm_format(self) -> bytes:
        # Build a concise, analyzable prompt summarizing key fields per entry
        lines = []
        for e in self._entries:
            ts = e.get("__SOURCE_REALTIME_TIMESTAMP") or e.get("_SOURCE_REALTIME_TIMESTAMP") or e.get("__REALTIME_TIMESTAMP") or e.get("_REALTIME_TIMESTAMP")
            msg = e.get("MESSAGE")
            unit = e.get("_SYSTEMD_UNIT") or e.get("SYSLOG_IDENTIFIER") or e.get("_COMM")
            pid = e.get("_PID")
            host = e.get("_HOSTNAME")
            # Fallback to a compact representation if MESSAGE missing
            if msg is None:
                msg = json.dumps({k: e[k] for k in ("PRIORITY", "SYSLOG_IDENTIFIER", "_COMM", "_PID") if k in e})
            line = f"[{ts}] host={host} unit={unit} pid={pid} message={msg}"
            lines.append(line)
        prompt = "Analyze the following journalctl logs for potential security incidents. For each log, assess if it indicates suspicious or malicious activity and summarize why.\n\n" + "\n".join(lines)
        return prompt.encode("utf-8")
