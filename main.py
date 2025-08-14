import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --------------------------------------------------
# Function to read CSV
# --------------------------------------------------
def read_csv_file(file):
    try:
        return pd.read_csv(file)
    except Exception as e:
        st.error(f"Error reading file {file.name}: {e}")
        return None

# --------------------------------------------------
# Function to prepare well data for map
# --------------------------------------------------
def prepare_well_data(welllist, prod, inj, include_unknown=True):
    df = welllist.copy()

    df["Well_Type"] = "Unknown"
    df.loc[df["UWI"].isin(prod["UWI"]), "Well_Type"] = "Production"
    df.loc[df["UWI"].isin(inj["UWI"]), "Well_Type"] = "Injection"

    deviation_col = "Deviation Ind" if "Deviation Ind" in df.columns else None
    if deviation_col:
        df["Deviation_Type"] = df[deviation_col].apply(
            lambda x: "Horizontal" if str(x).strip().upper().startswith("H") else "Vertical"
        )
    else:
        df["Deviation_Type"] = "Unknown"

    df["Well_ID"] = range(1, len(df) + 1)

    df["plot_lon"] = df["Longitude NAD 83"]
    df["plot_lat"] = df["Latitude NAD 83"]

    dup_mask = df.duplicated(subset=["plot_lon", "plot_lat"], keep=False)
    df.loc[dup_mask, "plot_lon"] += np.random.uniform(-0.0003, 0.0003, size=dup_mask.sum())
    df.loc[dup_mask, "plot_lat"] += np.random.uniform(-0.0003, 0.0003, size=dup_mask.sum())

    if not include_unknown:
        df = df[df["Well_Type"] != "Unknown"]

    return df

# --------------------------------------------------
# Function to plot map
# --------------------------------------------------
def plot_well_map(df, label_mode):
    color_map = {
        "Production": "blue",
        "Injection": "red",
        "Unknown": "gray"
    }

    import plotly.express as px
    if label_mode == "Hover tooltips":
        fig = px.scatter(
            df, x="plot_lon", y="plot_lat",
            color="Well_Type", symbol="Deviation_Type",
            hover_data=["Well_ID", "UWI"],
            title="Well Location Grid Map",
            labels={"plot_lon": "Longitude", "plot_lat": "Latitude"},
            color_discrete_map=color_map
        )
    else:
        fig = px.scatter(
            df, x="plot_lon", y="plot_lat",
            color="Well_Type", symbol="Deviation_Type",
            text="Well_ID",
            title="Well Location Grid Map",
            labels={"plot_lon": "Longitude", "plot_lat": "Latitude"},
            color_discrete_map=color_map
        )
        fig.update_traces(textposition="top center")

    fig.update_layout(
        xaxis=dict(showgrid=True, zeroline=False),
        yaxis=dict(showgrid=True, zeroline=False, scaleanchor="x", scaleratio=1),
        legend_title="Well Type / Deviation"
    )
    return fig

# --------------------------------------------------
# Function to plot Water Injection vs Water Production History
# --------------------------------------------------
def plot_water_inj_prod(prod_df, inj_df, prod_wells, inj_wells):
    fig = go.Figure()

    # Water production bars
    for well in prod_wells:
        data = prod_df[prod_df["UWI"] == well]
        fig.add_trace(go.Bar(
            x=pd.to_datetime(data["Date"], errors="coerce"),
            y=data["Water M3"],
            name=f"Water Production from well {well}",
            yaxis="y2"
        ))

    # Water injection lines
    for well in inj_wells:
        data = inj_df[inj_df["UWI"] == well]
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(data["Date"], errors="coerce"),
            y=data["Water Inj M3"],
            name=f"Water Injection into Well {well}",
            mode="lines+markers"
        ))

    # Calculate maximum for shared scale
    max_val = 0
    if prod_wells:
        max_val = max(max_val, prod_df[prod_df["UWI"].isin(prod_wells)]["Water M3"].max())
    if inj_wells:
        max_val = max(max_val, inj_df[inj_df["UWI"].isin(inj_wells)]["Water Inj M3"].max())

    fig.update_layout(
        title="Water Injection vs Water Production History",
        xaxis=dict(title="Date (month)"),
        yaxis=dict(title="Water Injection M3", range=[0, max_val]),
        yaxis2=dict(title="Water Production M3", overlaying="y", side="right", range=[0, max_val]),
        barmode="overlay"
    )
    return fig

# --------------------------------------------------
# Function to plot Oil Production vs Water Injection History
# --------------------------------------------------
def plot_oil_inj_prod(prod_df, inj_df, prod_wells, inj_wells):
    fig = go.Figure()

    # Oil production lines
    for i, well in enumerate(prod_wells):
        data = prod_df[prod_df["UWI"] == well]
        oil_color = "brown" if i == 0 else None  # First production well = brown

        fig.add_trace(go.Scatter(
            x=pd.to_datetime(data["Date"], errors="coerce"),
            y=data["Oil M3"],
            name=f"Oil Production from well {well}",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color=oil_color) if oil_color else {}
        ))

    # Water injection lines
    for j, well in enumerate(inj_wells):
        data = inj_df[inj_df["UWI"] == well]
        inj_color = "blue" if j == 0 else None  # First injection well = blue

        fig.add_trace(go.Scatter(
            x=pd.to_datetime(data["Date"], errors="coerce"),
            y=data["Water Inj M3"],
            name=f"Water Injection into Well {well}",
            mode="lines+markers",
            line=dict(color=inj_color) if inj_color else {}
        ))

    # Calculate maximum for shared scale
    max_val = 0
    if prod_wells:
        max_val = max(max_val, prod_df[prod_df["UWI"].isin(prod_wells)]["Oil M3"].max())
    if inj_wells:
        max_val = max(max_val, inj_df[inj_df["UWI"].isin(inj_wells)]["Water Inj M3"].max())

    fig.update_layout(
        title="Water Injection vs Oil Production History",
        xaxis=dict(title="Date (month)"),
        yaxis=dict(title="Water Injection M3", range=[0, max_val]),
        yaxis2=dict(title="Oil Production M3", overlaying="y", side="right", range=[0, max_val])
    )
    return fig

# --------------------------------------------------
# Function to plot Gas Production vs Water Injection History
# --------------------------------------------------
def plot_gas_inj_prod(prod_df, inj_df, prod_wells, inj_wells):
    fig = go.Figure()

    # Gas production bars
    for i, well in enumerate(prod_wells):
        data = prod_df[prod_df["UWI"] == well]
        gas_color = "green" if i == 0 else None  # first well = green

        fig.add_trace(go.Bar(
            x=pd.to_datetime(data["Date"], errors="coerce"),
            y=data["Gas E3M3"],
            name=f"Gas Production from well {well}",
            yaxis="y2",
            marker=dict(color=gas_color) if gas_color else {}
        ))

    # Water injection lines
    for well in inj_wells:
        data = inj_df[inj_df["UWI"] == well]
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(data["Date"], errors="coerce"),
            y=data["Water Inj M3"],
            name=f"Water Injection into Well {well}",
            mode="lines+markers"
        ))

    max_val = 0
    if prod_wells:
        max_val = max(max_val, prod_df[prod_df["UWI"].isin(prod_wells)]["Gas E3M3"].max())
    if inj_wells:
        max_val = max(max_val, inj_df[inj_df["UWI"].isin(inj_wells)]["Water Inj M3"].max())

    fig.update_layout(
        title="Water Injection vs Gas Production History",
        xaxis=dict(title="Date (month)"),
        yaxis=dict(title="Water Injection M3", range=[0, max_val]),
        yaxis2=dict(title="Gas Production M3", overlaying="y", side="right", range=[0, max_val]),
        barmode="overlay"
    )
    return fig

# --------------------------------------------------
# Function to plot Oil vs Water Production History
# --------------------------------------------------
def plot_oil_water_prod(prod_df, prod_wells):
    fig = go.Figure()

    for well in prod_wells:
        data = prod_df[prod_df["UWI"] == well]
        oil_color = "brown" if len(prod_wells) == 1 else None

        fig.add_trace(go.Scatter(
            x=pd.to_datetime(data["Date"], errors="coerce"),
            y=data["Oil M3"],
            name=f"Oil Production {well}",
            mode="lines+markers",
            yaxis="y1",
            line=dict(color=oil_color) if oil_color else {}
        ))

        fig.add_trace(go.Bar(
            x=pd.to_datetime(data["Date"], errors="coerce"),
            y=data["Water M3"],
            name=f"Water Production {well}",
            yaxis="y2",
            opacity=0.5
        ))

    max_val = 0
    if prod_wells:
        max_val = max(
            prod_df[prod_df["UWI"].isin(prod_wells)]["Oil M3"].max(),
            prod_df[prod_df["UWI"].isin(prod_wells)]["Water M3"].max()
        )

    fig.update_layout(
        title="Oil vs Water Production History",
        xaxis=dict(title="Date (month)"),
        yaxis=dict(title="Oil Production M3", range=[0, max_val]),
        yaxis2=dict(title="Water Production M3", overlaying="y", side="right", range=[0, max_val]),
        barmode="overlay"
    )
    return fig

# --------------------------------------------------
# Function to plot Gas vs Water Production History
# --------------------------------------------------
def plot_gas_water_prod(prod_df, prod_wells):
    fig = go.Figure()

    for i, well in enumerate(prod_wells):
        data = prod_df[prod_df["UWI"] == well]
        gas_color = "green" if i == 0 else None  # first well = green

        fig.add_trace(go.Scatter(
            x=pd.to_datetime(data["Date"], errors="coerce"),
            y=data["Gas E3M3"],
            name=f"Gas Production {well}",
            mode="lines+markers",
            yaxis="y1",
            line=dict(color=gas_color) if gas_color else {}
        ))

        fig.add_trace(go.Bar(
            x=pd.to_datetime(data["Date"], errors="coerce"),
            y=data["Water M3"],
            name=f"Water Production {well}",
            yaxis="y2",
            opacity=0.5
        ))

    max_val = 0
    if prod_wells:
        max_val = max(
            prod_df[prod_df["UWI"].isin(prod_wells)]["Gas E3M3"].max(),
            prod_df[prod_df["UWI"].isin(prod_wells)]["Water M3"].max()
        )

    fig.update_layout(
        title="Gas vs Water Production History",
        xaxis=dict(title="Date (month)"),
        yaxis=dict(title="Gas Production M3", range=[0, max_val]),
        yaxis2=dict(title="Water Production M3", overlaying="y", side="right", range=[0, max_val]),
        barmode="overlay"
    )
    return fig



# --------------------------------------------------
# Streamlit App
# --------------------------------------------------
st.title("Production/Injection Analysis")

# File uploaders
st.sidebar.image("./data/logo.png", use_container_width=True)

#st.sidebar.header("Cnergreen")
welllist_file = st.sidebar.file_uploader("Upload Welllist CSV", type=["csv"])
prod_file = st.sidebar.file_uploader("Upload Production History CSV", type=["csv"])
inj_file = st.sidebar.file_uploader("Upload Injection History CSV", type=["csv"])

if welllist_file and prod_file and inj_file:
    df_welllist = read_csv_file(welllist_file)
    df_prod = read_csv_file(prod_file)
    df_inj = read_csv_file(inj_file)

    if df_welllist is not None and df_prod is not None and df_inj is not None:
        st.subheader("Map Display Settings")
        include_unknown = st.radio(
            "Include Unknown Well_Type?", ["Yes", "No"], index=1, horizontal=True
        ) == "Yes"
        label_mode = st.radio(
            "Label Display Mode", ["Hover tooltips", "Visible labels"], index=1, horizontal=True
        )

        df_wells = prepare_well_data(df_welllist, df_prod, df_inj, include_unknown)

        fig_map = plot_well_map(df_wells, label_mode)
        st.plotly_chart(fig_map, use_container_width=True)

        st.subheader("Well ID to UWI Mapping")
        st.dataframe(df_wells[["UWI", "Well_ID", "Well_Type", "Deviation_Type"]])

        st.subheader("Select Wells for Plots")
        inj_wells = st.multiselect("Select Injection Wells (UWI)", sorted(df_inj["UWI"].unique()))
        prod_wells = st.multiselect("Select Production Wells (UWI)", sorted(df_prod["UWI"].unique()))
        

        #if prod_wells or inj_wells:
        if prod_wells or inj_wells:
            if prod_wells and inj_wells:
                fig1 = plot_water_inj_prod(df_prod, df_inj, prod_wells, inj_wells)
                st.plotly_chart(fig1, use_container_width=True)

                fig3 = plot_gas_inj_prod(df_prod, df_inj, prod_wells, inj_wells)
                st.plotly_chart(fig3, use_container_width=True)
 
                fig_oil_inj = plot_oil_inj_prod(df_prod, df_inj, prod_wells, inj_wells)
                st.plotly_chart(fig_oil_inj, use_container_width=True)

            elif inj_wells:
                fig1 = plot_water_inj_prod(df_prod, df_inj, prod_wells, inj_wells)
                st.plotly_chart(fig1, use_container_width=True)

            if prod_wells:
                fig2 = plot_oil_water_prod(df_prod, prod_wells)
                st.plotly_chart(fig2, use_container_width=True)

                fig4 = plot_gas_water_prod(df_prod, prod_wells)
                st.plotly_chart(fig4, use_container_width=True)




else:
    st.info("Please upload all three files to generate the map and plots.")
