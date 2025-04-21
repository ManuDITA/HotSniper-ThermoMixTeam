import os
import gzip
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def read_log_gz(filepath):
    with gzip.open(filepath, 'rt') as f:
        lines = f.readlines()
        header = lines[0].strip().split('\t')
        data = [list(map(float, line.strip().split('\t'))) for line in lines[1:]]
        return pd.DataFrame(data, columns=header)

def custom_downsample(df, group_size):
    output = []
    previous = np.zeros(df.shape[1])

    for i in range(0, len(df), group_size):
        chunk = df.iloc[i:i + group_size]
        if len(chunk) < group_size:
            break  # Skip incomplete chunk

        avg = chunk.mean().values
        min_vals = chunk.min().values
        max_vals = chunk.max().values

        # Apply custom logic per column
        new_row = []
        for j in range(len(avg)):
            if len(output) == 0 or avg[j] < previous[j]:
                new_row.append(min_vals[j])
            else:
                new_row.append(max_vals[j])
        previous = new_row
        output.append(new_row)

    return pd.DataFrame(output, columns=df.columns)

def plot_data(df, title, save_path):
    time = [i for i in range(len(df))]  # 1ns per step
    for column in df.columns:
        plt.plot(time, df[column], label=column)

    plt.title(title)
    plt.xlabel("Time [ms]")
    plt.ylabel(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def main(folder, timescale_ns):
    files = {
        'PeriodicFrequency': 'PeriodicFrequency.log.gz',
        'PeriodicPower': 'PeriodicPower.log.gz',
        'PeriodicThermal': 'PeriodicThermal.log.gz'
    }

    # Save 'charts' folder in the same directory as the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chart_dir = os.path.join(script_dir, "charts")
    os.makedirs(chart_dir, exist_ok=True)

    for name, filename in files.items():
        filepath = os.path.join(folder, filename)
        if os.path.exists(filepath):
            print(f"Processing {filename}")
            df = read_log_gz(filepath)

            if timescale_ns < 1.0:
                group_size = int(round(1.0 / timescale_ns))
                df = custom_downsample(df, group_size)
                print(f"Custom downsampled every {group_size} timepoints.")

            save_path = os.path.join(chart_dir, f"{name}.png")
            plot_data(df, name, save_path)
            print(f"Saved chart to {save_path}")
        else:
            print(f"File not found: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot periodic log data with 1ns timescale and custom downsampling.")
    parser.add_argument("folder", help="Folder containing the .log.gz files")
    parser.add_argument("timescale", type=float, help="Original timescale in miliseconds")
    args = parser.parse_args()

    main(args.folder, args.timescale)
