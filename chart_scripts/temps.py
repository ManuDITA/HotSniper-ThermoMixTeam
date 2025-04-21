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
    for name, series in runs.items():
        label = name.split("+")[0][-6:]
        time = [i for i in range(len(series))]
        plt.plot(time, series, label=label)

    plt.title("Max Temperature Over Time")
    plt.xlabel("Time [ms]")
    plt.ylabel("Temperature [C]")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()

def main(folders):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chart_dir = os.path.join(script_dir, "charts")
    os.makedirs(chart_dir, exist_ok=True)

    thermal_runs = {}
    for folder in folders:
        label = os.path.basename(os.path.normpath(folder))
        filepath = os.path.join(folder, 'PeriodicThermal.log.gz')
        if os.path.exists(filepath):
            print(f"Reading thermal data from: {filepath}")
            df = read_log_gz(filepath)
            max_series = extract_max_thermal_series(df)
            thermal_runs[label] = max_series
        else:
            print(f"File not found: {filepath}, skipping.")

    if thermal_runs:
        save_path = os.path.join(chart_dir, "max_thermal_comparison.png")
        plot_max_thermal_over_time(thermal_runs, save_path)
        print(f"Saved comparison chart to: {save_path}")
    else:
        print("No valid thermal data found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare max thermal values over time from multiple folders.")
    parser.add_argument("folders", nargs='+', help="Paths to folders containing PeriodicThermal.log.gz")
    args = parser.parse_args()

    main(args.folders)
