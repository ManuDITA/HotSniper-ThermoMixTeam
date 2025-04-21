import os
import gzip
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
from collections import defaultdict

def read_log_gz(filepath):
    with gzip.open(filepath, 'rt') as f:
        lines = f.readlines()
        header = lines[0].strip().split('\t')
        data = [list(map(float, line.strip().split('\t'))) for line in lines[1:]]
        return pd.DataFrame(data, columns=header)

def upsample_df(df, original_step_ms):
    if original_step_ms <= 0.1:
        return df
    factor = int(round(original_step_ms / 0.1))
    return pd.DataFrame(
        np.repeat(df.values, factor, axis=0),
        columns=df.columns
    )

def group_columns(df):
    groups = defaultdict(list)
    pattern = re.compile(r'([A-Za-z]+_\d+)')
    for col in df.columns:
        match = pattern.match(col)
        key = match.group(1) if match else col
        groups[key].append(col)
    return groups

def reduce_df_by_group(df, method='max'):
    groups = group_columns(df)
    reduced_data = {}
    for group, cols in groups.items():
        if method == 'max':
            reduced_data[group] = df[cols].max(axis=1)
        elif method == 'sum':
            reduced_data[group] = df[cols].sum(axis=1)
        else:
            raise ValueError("Method must be 'max' or 'sum'")
    return pd.DataFrame(reduced_data)

def plot_data(df, title, save_path):
    time = [i * 0.1 for i in range(len(df))]  # 0.1ms steps
    for column in df.columns:
        plt.plot(time, df[column], label=column)

    plt.title(title)
    plt.xlabel("Time [ms]")
    plt.ylabel(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()

def main(folder, timescale_ms):
    files = {
        'PeriodicFrequency': 'PeriodicFrequency.log.gz',
        'PeriodicPower': 'PeriodicPower.log.gz',
        'PeriodicThermal': 'PeriodicThermal.log.gz'
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    chart_dir = os.path.join(script_dir, "charts")
    os.makedirs(chart_dir, exist_ok=True)

    for name, filename in files.items():
        filepath = os.path.join(folder, filename)
        if os.path.exists(filepath):
            print(f"Processing {filename}")
            df = read_log_gz(filepath)

            if timescale_ms > 0.1:
                df = upsample_df(df, timescale_ms)
                print(f"Upsampled {name} by duplicating each row {int(round(timescale_ms / 0.1))} times.")

            if name == 'PeriodicThermal':
                df = reduce_df_by_group(df, method='max')
                print("Reduced Thermal data by taking max per core group per timestep.")
            elif name == 'PeriodicPower':
                df = reduce_df_by_group(df, method='sum')
                print("Reduced Power data by summing per core group per timestep.")

            save_path = os.path.join(chart_dir, f"{name}.png")
            plot_data(df, name, save_path)
            print(f"Saved chart to {save_path}")
        else:
            print(f"File not found: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot periodic log data with 0.1ms resolution and per-core aggregation.")
    parser.add_argument("folder", help="Folder containing the .log.gz files")
    parser.add_argument("timescale", type=float, help="Original timescale in milliseconds")
    args = parser.parse_args()

    main(args.folder, args.timescale)
