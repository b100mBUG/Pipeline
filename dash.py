import streamlit as st
import pandas as pd
import io

# -------------------- PAGE SETUP --------------------
st.set_page_config(
    page_title="Sample Data Pipeline",  
    page_icon="🛠️",                   
    layout="wide",             
)

st.title("Sample Data Pipeline")
st.header("Let's clean your data")
st.subheader("Processed data will appear here")

sb = st.sidebar

# -------------------- SESSION STATE --------------------
if "data" not in st.session_state:
    st.session_state.data = None

# -------------------- LOAD FILE (CACHED) --------------------
@st.cache_data
def load_file(file):
    if file is None:
        return None

    if file.type == "text/csv":
        return pd.read_csv(file, low_memory=False)

    if file.type.endswith("sheet"):
        return pd.read_excel(file)

    return None

# -------------------- DISPLAY DATA --------------------
def show_file_data(rows: int = 10):
    data = st.session_state.data

    if data is None or data.empty:
        st.toast("No data to display")
        return

    rows = min(rows, len(data))

    with st.expander(
        f"Show data ({data.shape[0]} rows × {data.shape[1]} columns)",
        expanded=True,
    ):
        st.dataframe(data.head(rows), use_container_width=True)

# -------------------- FILE PICKER --------------------
sb.header("Navigation")

file_form = sb.form("file_picker")
file = file_form.file_uploader("Select file", ["csv", "xlsx"])
file_btn = file_form.form_submit_button("Load file")

if file_btn:
    df = load_file(file)
    if df is not None:
        st.session_state.data = df
        st.toast("File loaded successfully")
    else:
        st.toast("Unsupported file type")

# -------------------- ROW DISPLAY CONTROL --------------------
rows_form = st.form("rows_form")
rows_count = rows_form.number_input(
    "Rows to display", min_value=1, value=10
)
rows_btn = rows_form.form_submit_button("Show rows")

if rows_btn:
    show_file_data(rows_count)

# -------------------- FILE INFO --------------------
if sb.button("File Information", type="primary"):
    if st.session_state.data is not None:
        buffer = io.StringIO()
        st.session_state.data.info(buf=buffer)
        with st.expander("Dataset Information", expanded=True):
            st.text(buffer.getvalue())
    else:
        st.toast("No file loaded")

# -------------------- COLUMN FILTER --------------------
sb.subheader("Column filtering")

if st.session_state.data is not None:
    col_filter_form = sb.form("col_filter")
    selected_cols = col_filter_form.multiselect(
        "Select columns", st.session_state.data.columns
    )
    col_filter_btn = col_filter_form.form_submit_button("Filter")

    if col_filter_btn:
        if selected_cols:
            with st.expander("Filtered Data", expanded=True):
                st.dataframe(
                    st.session_state.data[selected_cols],
                    use_container_width=True,
                )
        else:
            st.toast("No columns selected")

# -------------------- DROP COLUMNS --------------------
def drop_columns(columns: list[str]):
    if not columns:
        st.toast("No columns selected")
        return

    st.session_state.data.drop(columns=columns, inplace=True)
    st.toast(f"Dropped columns: {columns}")

sb.subheader("Drop columns")

if st.session_state.data is not None:
    drop_form = sb.form("drop_form")
    drop_cols = drop_form.multiselect(
        "Select columns to drop", st.session_state.data.columns
    )
    drop_btn = drop_form.form_submit_button("Drop")

    if drop_btn:
        drop_columns(drop_cols)

# -------------------- TRANSFORM COLUMNS --------------------
def transform_columns(column: str, usage: str):
    data = st.session_state.data

    if data is None:
        st.toast("No data loaded")
        return

    try:
        if usage == "Currency":
            data[column] = (
                data[column]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
                .replace("", pd.NA)
                .astype(float)
            )

        elif usage == "General Text":
            data[column] = data[column].astype(str)

        elif usage == "Number":
            data[column] = pd.to_numeric(
                data[column], errors="raise"
            ).astype(int)

        elif usage == "DateTime":
            data[column] = pd.to_datetime(
                data[column], errors="raise"
            )

        elif usage == "Non Currency (Floating)":
            data[column] = pd.to_numeric(
                data[column], errors="raise"
            ).astype(float)

        else:
            st.toast("Invalid transformation type")
            return

        st.toast(f"{column} converted to {usage}")

    except Exception as e:
        st.toast(f"Conversion failed: {e}")

sb.subheader("Column transformation")

if st.session_state.data is not None:
    trans_form = sb.form("transform_form")
    c1, c2 = trans_form.columns(2)

    col_name = c1.selectbox(
        "Column", st.session_state.data.columns
    )
    usage = c2.selectbox(
        "Usage",
        [
            "Currency",
            "General Text",
            "Number",
            "DateTime",
            "Non Currency (Floating)",
        ],
    )

    trans_btn = trans_form.form_submit_button("Transform")

    if trans_btn:
        transform_columns(col_name, usage)
        show_file_data(10)

def rename_column(column: str | None = None, name: str | None = None):
    data = st.session_state.data

    if data is None:
        st.toast("No data loaded")
        return

    if not column or not name:
        st.toast("Missing column or new name")
        return

    if name in data.columns:
        st.toast(f"Column '{name}' already exists")
        return

    try:
        data.rename(columns={column: name}, inplace=True)
        st.toast(f"Renamed '{column}' to '{name}'")
    except Exception as e:
        st.toast(f"Rename failed: {e}")


sb.subheader("Rename Columns")

if st.session_state.data is not None:
    rename_form = sb.form("rename_form")
    rc1, rc2 = rename_form.columns(2)

    curr_col = rc1.selectbox(
        "Column", st.session_state.data.columns
    )
    new_name = rc2.text_input("New name")

    rename_btn = rename_form.form_submit_button("Rename")

    if rename_btn:
        rename_column(curr_col, new_name)

sb.write("")
