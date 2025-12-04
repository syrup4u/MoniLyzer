#!/usr/bin/env python3
"""Plot username and IP frequency bar charts from a MoniLyzer JSON output.

Usage:
  python scripts/plot_frequencies.py \
    --input testbed/attack_output/sshlogin.json \
    --outdir plots --top 30
"""
import argparse
import json
import os
from typing import List, Tuple

import matplotlib.pyplot as plt


def read_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def to_pairs(items: List[dict], key_name: str) -> List[Tuple[str, int]]:
    pairs = []
    for it in items:
        name = it.get(key_name)
        count = int(it.get('count', 0))
        if name:
            pairs.append((name, count))
    return pairs


def plot_barh(pairs: List[Tuple[str, int]], title: str, outpath: str, top_n: int = 30):
    pairs = sorted(pairs, key=lambda x: x[1], reverse=True)[:top_n]
    if not pairs:
        print(f"No data to plot for {title}")
        return
    names, counts = zip(*pairs)
    # horizontal bar chart with largest at top
    names = list(names)[::-1]
    counts = list(counts)[::-1]

    plt.figure(figsize=(10, max(4, 0.3 * len(names))))
    bars = plt.barh(range(len(names)), counts, color='C0')
    plt.yticks(range(len(names)), names)
    plt.xlabel('Count')
    plt.title(title)
    # annotate
    for i, b in enumerate(bars):
        plt.text(b.get_width() + max(1, max(counts) * 0.01), b.get_y() + b.get_height() / 2,
                 str(counts[i]), va='center')

    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()
    print(f"Saved: {outpath}")


def main():
    parser = argparse.ArgumentParser(description='Plot username and IP frequencies')
    parser.add_argument('--input', '-i', default='attack_output/sshlogin.json', help='Input JSON file')
    parser.add_argument('--outdir', '-o', default='attack_plots', help='Output directory for saved plots')
    parser.add_argument('--top', '-t', type=int, default=30, help='Top N items to plot')
    args = parser.parse_args()

    data = read_json(args.input)

    os.makedirs(args.outdir, exist_ok=True)

    # users
    user_pairs = []
    if 'attack_users' in data:
        user_pairs = to_pairs(data['attack_users'], 'username')

    total_cnt = sum(count for _, count in user_pairs)
    print(f"Total number of attacks: {total_cnt}")

    plot_barh(user_pairs, 'Username Frequency', os.path.join(args.outdir, 'username_frequency.png'), top_n=args.top)

    # ips
    ip_pairs = []
    if 'attack_ips' in data:
        ip_pairs = to_pairs(data['attack_ips'], 'ip')

    plot_barh(ip_pairs, 'IP Frequency', os.path.join(args.outdir, 'ip_frequency.png'), top_n=args.top)


if __name__ == '__main__':
    main()
