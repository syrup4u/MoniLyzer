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

class MessageKind(Enum):
    """Enumerates logical categories of data exchanged between modules."""

    NetworkPacket = 1

class Analyzer(Enum):
    """Enumerates analyzers that can consume transport messages."""

    Snort = 1
    LLM = 2

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
