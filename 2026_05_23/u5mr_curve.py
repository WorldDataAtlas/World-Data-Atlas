from pathlib import Path
import sys
import os
import pandas as pd
import sqlalchemy as sa
BASE_DIR = Path(__file__).resolve().parent
etl_path = (BASE_DIR.parent / "ETL").resolve()
sys.path.insert(0, str(etl_path))
import settings as s
module_path = (BASE_DIR.parent / "modules").resolve()
sys.path.insert(0, str(module_path))
from graph_curve import create_multi_line_chart

query = """
SELECT [year], CAST([value] AS FLOAT) AS value, [sex_name]
FROM [World_Data_Atlas].[un].[data]
WHERE [indicator_id] = 22 AND [variant_id] = 4 AND [location_name] = 'World' AND [value] IS NOT NULL AND [year] < 2025
ORDER BY [year], [sex_name];
"""

OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_FILE = OUTPUT_DIR / "u5mr_world_by_sex.png"

engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
df["year"] = df["year"].astype(int)
df["value"] = df["value"].astype(float)
start_year = int(df["year"].min())
end_year = int(df["year"].max())

series_config = [   {"source_value": "Male", "label": "Male", "color": "#60A5FA"},
                    {"source_value": "Female", "label": "Female", "color": "#F472B6"},
                    {"source_value": "Both sexes", "label": "Both sexes", "color": "#22C55E"}]

create_multi_line_chart(
    df=df,
    output_file=OUTPUT_FILE,
    x_col="year",
    y_col="value",
    series_col="sex_name",
    series_config=series_config,
    title="Global Under-Five Mortality by Sex",
    subtitle=f"World, {start_year}–{end_year}",
    y_label="Deaths per 1,000 live births",
    footer_left="Metric: Deaths before age 5 per 1,000 live births",
    footer_right="Source: United Nations",
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
)