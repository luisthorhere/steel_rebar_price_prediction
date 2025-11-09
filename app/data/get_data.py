import yfinance as yf
import pandas as pd
import os

from ..logger.logger import logger

base_path = os.path.dirname(__file__)


def steel_rebar_data() -> pd.DataFrame:

    file_path = os.path.join(base_path, "steel_rebar_data.csv")
    steel_data = pd.read_csv(file_path, index_col="Date")
    steel_data.reset_index(inplace=True)
    steel_data["Date"] = pd.to_datetime(steel_data["Date"], errors="coerce")
    steel_data = steel_data.rename(columns={"Price": "steel_rebar"})
    steel_data = steel_data.dropna(subset=["Date"]).sort_values("Date")
    steel_data = steel_data.groupby(
        steel_data["Date"].dt.normalize(), as_index=False
    ).last()
    logger.info("Steel rebar data loaded")
    return steel_data


def correlational_feautures_historical() -> pd.DataFrame:
    symbols = {
        "HRC=F": "hot_rolled_coil",
        "TIO=F": "iron_ore",
        "MXN=X": "usd_mxn",
        "COAL": "coal",
    }

    data = {}

    for ticker, name in symbols.items():
        try:
            df = yf.download(ticker, period="5y", interval="1d")[["Close"]]
            df.reset_index(inplace=True)
            df.columns = ["Date", name]
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"]).sort_values("Date")
            df = df.groupby(df["Date"].dt.normalize(), as_index=False).last()
            data[name] = df

            logger.info(f"Downloading {name} data")
        except Exception as e:
            logger.warning((f"Downloading error {ticker}: {e}"))

    return data


def merge_feautures(steel_data: pd.DataFrame, feautures: pd.DataFrame) -> pd.DataFrame:
    steel_idx = steel_data.set_index("Date").sort_index()
    merged = steel_idx.copy()

    for name, df in feautures.items():
        df_idx = df.set_index("Date").sort_index()

        cols_ok = [c for c in df_idx.columns if c == name]
        if len(cols_ok) != 1:
            raise ValueError(
                f"The expected column '{name}' for feauture {name}, getting: {list(df_idx.columns)}"
            )
        merged = merged.join(df_idx, how="left")

    merged_ffill = merged.ffill().bfill()
    raw_data = os.path.join(base_path, "merged_steel_dataset_raw.csv")
    filled_data = os.path.join(base_path, "merged_steel_dataset_filled.csv")
    merged.reset_index().to_csv(raw_data, index=False)
    merged_ffill.reset_index().to_csv(filled_data, index=False)

    df_predict = merged_ffill.copy()
    df_predict["steel_rebar_next"] = df_predict["steel_rebar"].shift(-1)

    corr_next = df_predict.drop(columns=["steel_rebar"]).corr(method="pearson")

    dataset_model = df_predict.dropna(subset=["steel_rebar_next"]).reset_index()
    model_data = os.path.join(base_path, "dataset_model_ready.csv")
    dataset_model.to_csv(model_data, index=False)
    logger.info("Training data correctly saved")
