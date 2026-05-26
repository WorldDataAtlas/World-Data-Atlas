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
from scatter_plot import create_scatter_chart

# ============================================================

for atribute in ('pages','users','articles','edits','active_users','admins'):
    print(atribute)

    query = """SELECT 
                    case when l.[language_name] = 'Modern Greek' then 'Greek' else l.[language_name] end as [label]
                    ,l.[speakers]
                    ,s.[""" + atribute + """]
                FROM [World_Data_Atlas].[wiki].[sites] AS s
                LEFT JOIN [wiki].[languages] AS l ON l.[iso639_1] = s.[language_code]
                WHERE l.[speakers] > 1000000 AND s.[active_users] >= 1500
            """

    FILE_NAME = "wiki_languages_speakers_vs_" + atribute + ".png"
    X_COL = "speakers"
    Y_COL = atribute
    MAP_TITLE = "Wikipedia Language Size"
    MAP_SUBTITLE = "Number of speakers vs total Wikipedia " + atribute.capitalize()
    X_LABEL = "Speakers"
    Y_LABEL = atribute.capitalize()
    FOOTER_LEFT = "Only languages with >1 million speakers and 1500+ active Wikipedia users"
    FOOTER_RIGHT = "Source: Wikimedia"
    X_LOG = True
    Y_LOG = True
    SHOW_LABELS = True
    POINT_COLOR = "#29D789"

    # ============================================================

    OUTPUT_DIR = BASE_DIR / "results"
    OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
    engine = sa.create_engine(s.connection_string)
    df = pd.read_sql(query, engine)
    create_scatter_chart(
        df=df,
        output_file=OUTPUT_FILE,
        x_col=X_COL,
        y_col=Y_COL,
        title=MAP_TITLE,
        subtitle=MAP_SUBTITLE,
        x_label=X_LABEL,
        y_label=Y_LABEL,
        footer_left=FOOTER_LEFT,
        footer_right=FOOTER_RIGHT,
        logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..","Logos","4.png",)),
        x_log=X_LOG,
        y_log=Y_LOG,
        show_labels=SHOW_LABELS, 
        point_color=POINT_COLOR)