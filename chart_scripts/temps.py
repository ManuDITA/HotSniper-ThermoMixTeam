import os
import gzip
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def read_log_gz(filepath):
    with gzip.open(filepath, 'rt') as f:
        lines = f.readlines()
        header = lines[0].strip().split('\t')
        data = [list(map(float, line.strip().split('\t'))) for line in lines[1:]]
        return pd.DataFrame(data, columns=header)

def extract_max_thermal_series(df):
    return df.max(axis=1)  # max across all cores/sensors per row

def plot_max_thermal_over_time(runs, save_path):
    for label, (timestep, series) in runs.items():
        time = [i * timestep for i in range(len(series))]
        plt.plot(time, series, label=label)

    plt.title("Maximum Temperature Over Time")
    plt.xlabel("Time [ms]")
    plt.ylabel("Max Temperature [C]")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()

def main(runs):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chart_dir = os.path.join(script_dir, "charts")
    os.makedirs(chart_dir, exist_ok=True)

    thermal_runs = {}

    parsed_runs = []
    for entry in runs:
        if ':' in entry:
            folder, timestep_str, label = entry.split(':')
            try:
                timestep = float(timestep_str)
                parsed_runs.append((folder, timestep, label))
            except ValueError:
                print(f"Invalid timestep for entry: {entry}, skipping.")
        else:
            print(f"Invalid format: {entry}. Use folder:timestep (e.g. run1:0.1), skipping.")

    for folder, timestep, label in parsed_runs:
        # label = os.path.basename(os.path.normpath(folder)).split("+")[2]#[0][-6:]
        filepath = os.path.join(folder, 'PeriodicThermal.log.gz')
        if os.path.exists(filepath):
            print(f"Reading thermal data from: {filepath}")
            df = read_log_gz(filepath)
            max_series = extract_max_thermal_series(df)
            thermal_runs[label] = (timestep, max_series)
        else:
            print(f"File not found: {filepath}, skipping.")

    if thermal_runs:
        save_path = os.path.join(chart_dir, "max_thermal_comparison.png")
        plot_max_thermal_over_time(thermal_runs, save_path)
        print(f"Saved comparison chart to: {save_path}")
    else:
        print("No valid thermal data found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare total power usage over time and calculate total energy (Joules).")
    parser.add_argument("runs", nargs='+', help="Format: folder:timestep_ms:label (e.g. run1:0.1:1GHz)")
    args = parser.parse_args()
    main(args.runs)
