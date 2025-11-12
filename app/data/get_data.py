import concurrent.futures
import yfinance as yf
import pandas as pd
import os

from ..logger.logger import logger

base_path = os.path.dirname(__file__)


def prepare_steel_rebar_data() -> pd.DataFrame:
    """
        Load and clean daily steel rebar price data.

        Reads the CSV file, converts dates, removes null values, sorts chronologically,
        and keeps only the last record per day. Returns a DataFrame ready for
        time series analysis or modeling.
    """
    file_path = os.path.join(base_path, "steel_rebar_data.csv")
    steel_data = pd.read_csv(file_path, index_col="Date")
    steel_data.reset_index(inplace=True)
    steel_data["Date"] = pd.to_datetime(steel_data["Date"], errors="coerce")
    steel_data = steel_data.rename(columns={"Price": "steel_rebar"})
    steel_data = steel_data.dropna(subset=["Date"]).sort_values("Date")
    steel_data = steel_data.groupby(
        steel_data["Date"].dt.normalize(), as_index=False
    ).last()

    logger.info("Steel rebar data loaded for analysis")

    return steel_data


def _download_and_clean(ticker: str, name: str) -> pd.DataFrame:
    """Helper: download and clean one ticker's data."""
    try:
        df = yf.download(ticker, period="5y", interval="1d")[["Close"]]
        df.reset_index(inplace=True)
        df.columns = ["Date", name]
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"]).sort_values("Date")
        df = df.groupby(df["Date"].dt.normalize(), as_index=False).last()
        logger.info(f"Downloaded {name}")
        return name, df
    except Exception as e:
        logger.warning(f"Error downloading {ticker}: {e}")
        return name, pd.DataFrame(columns=["Date", name])



def correlational_feautures_historical() -> dict[str, pd.DataFrame]:
    """
    Download 5-year daily data of commodities correlated with steel rebar prices.

    Fetches hot rolled coil, iron ore, USD/MXN, and coal one by one .
    Returns a dictionary of cleaned DataFrames keyed by the friendly variable name.
    """
    symbols = {
        "HRC=F": "hot_rolled_coil",
        "TIO=F": "iron_ore",
        "MXN=X": "usd_mxn",
        "COAL": "coal",
    }

    data = {}

    for ticker, name in symbols.items():
        name_out, df = _download_and_clean(ticker, name)
        data[name_out] = df

    return data
  

def merge_feautures(steel_data: pd.DataFrame, feautures: dict[str, pd.DataFrame]):
    """
    Une los datos del acero con sus features por fecha (sin bfill ni fuga de futuro)
    y guarda el dataset final listo para entrenamiento.
    """
    steel = steel_data.copy()
    steel["Date"] = pd.to_datetime(steel["Date"])
    steel = steel.sort_values("Date").set_index("Date")

    merged = steel.copy()

    for name, df in feautures.items():
        feat = df.copy()
        feat["Date"] = pd.to_datetime(feat["Date"])
        feat = feat.sort_values("Date")[["Date", name]]

        merged = pd.merge_asof(
            merged.reset_index().sort_values("Date"),
            feat.sort_values("Date"),
            on="Date",
            direction="backward",
        ).set_index("Date")

    merged = merged.ffill()

    if "steel_rebar" not in merged.columns:
        raise KeyError("Falta la columna 'steel_rebar' tras el merge.")
    merged["steel_rebar_next"] = merged["steel_rebar"].shift(-1)

    dataset_model = merged.dropna(subset=["steel_rebar_next"]).reset_index()

    model_data = os.path.join(base_path, "dataset_model_ready.csv")
    dataset_model.to_csv(model_data, index=False)
    logger.info("Training data correctly saved")