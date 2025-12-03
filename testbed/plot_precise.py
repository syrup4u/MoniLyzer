import pandas as pd
import matplotlib.pyplot as plt
import sys
from datetime import datetime

# --- Configuration ---
if len(sys.argv) < 2:
    print(f"Usage: python3 {sys.argv[0]} <CSV file path>")
    sys.exit(1)

file_path = sys.argv[1]

# --- 1. Read CLK_TCK and data ---
CLK_TCK = 100 # Default value if not found in file header
PAGE_SIZE = 4 # Default page size in KiB

try:
    # 1a. Read CLK_TCK from file header
    with open(file_path, 'r') as f:
        first_line = f.readline().strip()
        if first_line.startswith("#CLK_TCK:"):
            CLK_TCK = int(first_line.split(':')[1])
    
    # 1b. Read CSV data (skip file header)
    df = pd.read_csv(file_path, comment='#')
except FileNotFoundError:
    print(f"Error: File {file_path} not found.")
    sys.exit(1)
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

print(f"System CLK_TCK used (Hz): {CLK_TCK}")

# --- 2. Core Calculation: CPU Usage ---

# Calculate Jiffies delta (current - previous)
df['Delta_Jiffies'] = df['CPU_Jiffies_Cumulative'].diff()

# Calculate time delta (current timestamp - previous timestamp)
df['Delta_Time'] = df['Timestamp'].diff()

# Calculate CPU usage (%) = (Delta_Jiffies / (Delta_Time * CLK_TCK)) * 100
# Ignore the first row (diff results in NaN)
df['CPU_Usage_Precise'] = (df['Delta_Jiffies'] / (df['Delta_Time'] * CLK_TCK)) * 100.0

# Clean NaN values (first row)
df = df.dropna()

# --- 3. Core Calculation: Memory (Pages to MiB) ---

# Linux page size is typically 4 KiB.
# RSS_Pages (pages) * 4 (KiB/page) / 1024 (KiB/MiB) = Memory MiB
df['Memory_MiB'] = (df['RSS_Pages'] * PAGE_SIZE) / 1024.0

# --- 4. Visualization ---
df['Time'] = df['Timestamp'].apply(lambda x: datetime.fromtimestamp(x))

fig, ax1 = plt.subplots(figsize=(12, 6))
fig.suptitle(f'Resource Usage Over Time')

# --- Plot CPU (Left Y-axis) ---
color = 'tab:blue'
ax1.set_xlabel('Time')
ax1.set_ylabel('CPU Usage (%)', color=color)
ax1.plot(df['Time'], df['CPU_Usage_Precise'], color=color, label='CPU')
ax1.tick_params(axis='y', labelcolor=color)
ax1.set_ylim(bottom=0) # Ensure Y-axis starts at 0
ax1.grid(True, linestyle='--', alpha=0.7)

# --- Plot Memory (Right Y-axis) ---
ax2 = ax1.twinx()  
color = 'tab:red'
ax2.set_ylabel('Memory (MiB)', color=color)  
ax2.plot(df['Time'], df['Memory_MiB'], color=color, label='Memory')
ax2.tick_params(axis='y', labelcolor=color)

# Format X-axis labels
fig.autofmt_xdate(rotation=45)
plt.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust layout to fit suptitle

# Save and display the plot
output_png = file_path.replace('.csv', '.png')
plt.savefig(output_png)
print(f"\nHigh-precision plot saved to: {output_png}")