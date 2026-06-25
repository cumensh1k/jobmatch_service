from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "linkedin"


def main() -> None:
    csv_files = sorted(RAW_DIR.rglob("*.csv"))

    if not csv_files:
        print(f"CSV files not found in {RAW_DIR}")
        return

    for path in csv_files:
        print("\n" + "=" * 100)
        print(f"FILE: {path.relative_to(PROJECT_ROOT)}")

        try:
            df = pd.read_csv(path, nrows=5)
            print(f"COLUMNS ({len(df.columns)}):")
            for col in df.columns:
                print(f"  - {col}")

            print("\nSAMPLE:")
            print(df.head(2).to_string())

        except Exception as exc:
            print(f"ERROR READING FILE: {exc}")


if __name__ == "__main__":
    main()