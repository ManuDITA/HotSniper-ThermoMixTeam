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

def extract_total_power_series(df):
    return df.sum(axis=1)  # total power at each timestep

def calculate_energy(power_series, timestep_ms=1):
    return power_series.sum() * timestep_ms

def plot_total_power_over_time(runs, save_path):
    for label, (timestep, series) in runs.items():
        time = [i * timestep for i in range(len(series))]
        plt.plot(time, series, label=label)

    plt.title("Power Over Time")
    plt.xlabel("Time [ms]")
    plt.ylabel("Power [W]")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def plot_energy_bars(energy_dict, save_path):
    labels = list(energy_dict.keys())
    values = list(energy_dict.values())

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, values, color='blue')
    plt.title("Energy Usage")
    plt.ylabel("Energy [J]")
    plt.xticks(rotation=0, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    # Add labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height + 0.5, f"{height:.1f}", ha='center', va='bottom')

    # plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()


def main(runs):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chart_dir = os.path.join(script_dir, "charts")
    os.makedirs(chart_dir, exist_ok=True)

    power_runs = {}
    energy_totals = {}

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
        filepath = os.path.join(folder, 'PeriodicPower.log.gz')
        if os.path.exists(filepath):
            print(f"Reading power data from: {filepath}")
            df = read_log_gz(filepath)
            total_power_series = extract_total_power_series(df)
            total_energy = calculate_energy(total_power_series, timestep)
            power_runs[label] = (timestep, total_power_series)
            energy_totals[label] = total_energy
        else:
            print(f"File not found: {filepath}, skipping.")

    if power_runs:
        save_path = os.path.join(chart_dir, "power_comparison.png")
        plot_total_power_over_time(power_runs, save_path)
        print(f"Saved power comparison chart to: {save_path}")

        energy_chart_path = os.path.join(chart_dir, "energy_comparison.png")
        plot_energy_bars(energy_totals, energy_chart_path)
        print(f"Saved energy comparison chart to: {energy_chart_path}")

    else:
        print("No valid power data found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare total power usage over time and calculate total energy (Joules).")
    parser.add_argument("runs", nargs='+', help="Format: folder:timestep_ms:label (e.g. run1:0.1:1GHz)")
    args = parser.parse_args()
    main(args.runs)
