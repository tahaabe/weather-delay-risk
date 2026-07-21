import pandas as pd
import os

BTS_FOLDER = os.path.join("data", "raw", "bts")


def load_bts_data() -> pd.DataFrame:
    """Load and combine all BTS CSV files."""
    all_files = [f for f in os.listdir(BTS_FOLDER) if f.endswith(".csv")]

    if not all_files:
        raise FileNotFoundError(f"No CSV files found in {BTS_FOLDER}")

    dfs = []
    for file in all_files:
        path = os.path.join(BTS_FOLDER, file)
        df = pd.read_csv(path, low_memory=False)
        dfs.append(df)
        print(f"✅ Loaded: {file} ({len(df)} rows)")

    combined = pd.concat(dfs, ignore_index=True)
    print(f"\n📦 Total records loaded: {len(combined)}")
    return combined


if __name__ == "__main__":
    df = load_bts_data()
    print(df.head())
    print(df.columns.tolist())