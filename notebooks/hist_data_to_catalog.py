# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2024 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

from os import PathLike
from pathlib import Path

import requests
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.wranglers import QuoteTickDataWrangler
from nautilus_trader.test_kit.providers import CSVTickDataLoader
from nautilus_trader.test_kit.providers import TestInstrumentProvider


ROOT = Path(__file__).parent.parent
CATALOG_DIR = ROOT / "catalog"
CATALOG_DIR.mkdir(exist_ok=True)


def load_fx_hist_data(
    filename: str,
    currency: str,
    catalog_path: PathLike[str] | str,
) -> None:
    instrument = TestInstrumentProvider.default_fx_ccy(currency)
    wrangler = QuoteTickDataWrangler(instrument)

    df = CSVTickDataLoader.load(
        filename,
        index_col=0,
        datetime_format="%Y%m%d %H%M%S%f",
    )
    df.columns = ["bid_price", "ask_price", "size"]
    print(df)

    print("Preparing ticks...")
    ticks = wrangler.process(df)

    print("Writing data to catalog...")
    catalog = ParquetDataCatalog(catalog_path)
    catalog.write_data([instrument])
    catalog.write_data(ticks)

    print("Done")


def download(url: str) -> None:
    filename = url.rsplit("/", maxsplit=1)[1]
    with open(filename, "wb") as f:
        f.write(requests.get(url).content)


def main():
    # Download raw data
    download(
        "https://raw.githubusercontent.com/nautechsystems/nautilus_data/main/raw_data/fx_hist_data/DAT_ASCII_EURUSD_T_202001.csv.gz",
    )
    load_fx_hist_data(
        filename="DAT_ASCII_EURUSD_T_202001.csv.gz",
        currency="EUR/USD",
        catalog_path=CATALOG_DIR,
    )


if __name__ == "__main__":
    main()
