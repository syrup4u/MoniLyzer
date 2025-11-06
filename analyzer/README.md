## Analyzer Implementations

Two analyzers are provided:

### `LLMAnalyzer`
Uses a Large Language Model (OpenAI compatible) to classify whether a set of captured packets likely indicates an attack.

Requirements:
- Set environment variable `OPENAI_API_KEY`.
- Optional: set `LLM_MODEL` (defaults to `gpt-4o-mini`).
- Install dependencies: `pip install -r requirements.txt` (now includes `openai`).

Usage example:
```python
from transport.message import NetworkPacketMessage
from analyzer import LLMAnalyzer
import scapy.all as scapy

packets = [scapy.Ether()/scapy.IP(dst="1.2.3.4")/scapy.TCP(dport=80)]
msg = NetworkPacketMessage(packets)
analyzer = LLMAnalyzer()
result = analyzer.analyze(msg)
print(result)
```

### `SnortAnalyzer`
Invokes Snort3 to inspect a provided capture for alerts.

Snort executable discovery order:
1. Environment variable `SNORT_EXECUTABLE`
2. First `snort` found on `PATH`

Snort configuration discovery order (unless explicitly passed):
1. Environment variable `SNORT_CONFIG`
2. `/etc/snort/snort.lua`
3. `/usr/local/etc/snort/snort.lua`
4. `tmp/install/etc/snort/snort.lua` inside repository

Usage example:
```python
from transport.message import NetworkPacketMessage
from analyzer import SnortAnalyzer
import scapy.all as scapy

packets = [scapy.Ether()/scapy.IP(dst="1.2.3.4")/scapy.TCP(dport=80)]
msg = NetworkPacketMessage(packets)
snort = SnortAnalyzer()
result = snort.analyze(msg)
print(result)
```

Returned dictionary keys:
- `analyzer`: Analyzer name (`LLM` or `Snort`)
- `is_attack`: Boolean classification
- For LLM: `reasoning`, `raw_output`, `model`
- For Snort: `details`, `return_code`, `raw_output`, `snort_exec`, `snort_config`

