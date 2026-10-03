# ----------------------------
# Import necessary libraries
# ----------------------------
import dash
from dash import dcc, html, Input, Output, State, dash_table
from dash import dash_table, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import io
from datetime import timedelta

# ----------------------------
# Helper: Safe mean calculation
# ----------------------------
def safe_mean(df, column):
    return round(df[column].mean(), 1) if column in df and not df[column].dropna().empty else "-"

def safe_int_mean(df, column):
    return int(round(df[column].mean(), 0)) if column in df and not df[column].dropna().empty else "-"

def safe_max(df, column):
    return round(df[column].max(), 1) if column in df and not df[column].dropna().empty else "-"


# ----------------------------
# Initialize the Dash app
# ----------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# ----------------------------
# Define the Layout
# ----------------------------
app.layout = dbc.Container([
    html.H1("Return to Performance Tracking", className="text-center mt-4 mb-4"),
    html.Hr(),

    # --- Upload Section ---
    dbc.Card([
        dbc.CardBody([
            html.H4("Upload Your Data", className="card-title"),
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ', html.A('Select CSV File')
                ]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
                },
                multiple=False
            ),
        ])
    ], className="mb-4"),

    # --- Metric Chart Section with Dropdown ---
    dbc.Card([
        dbc.CardBody([
            html.H4("Metric Over Time", className="card-title"),
            dbc.Row([
                dbc.Col(html.Label("Select Metric"), width=3),
                dbc.Col(
                    dcc.Dropdown(
                        id='metric-selector',
                        options=[
                            {'label': 'Max Velocity', 'value': 'Velocity'},
                            {'label': 'Number of Throws', 'value': 'Number of Throws'},
                            {'label': 'Average Velocity', 'value': 'Average Velocity'},
                            {'label': 'Average Arm Speed', 'value': 'Average Arm Speed'},
                            {'label': 'Average Torque', 'value': 'Average Torque'},
                            {'label': 'Peak Velocity', 'value': 'Peak Velocity'},
                            {'label': 'Peak Arm Speed', 'value': 'Peak Arm Speed'},
                            {'label': 'Peak Torque', 'value': 'Peak Torque'},
                            {'label': 'Peak Velocity/Torque', 'value': 'Peak Velocity/Torque'},
                            {'label': 'One Day Workload', 'value': 'ODW'},
                            {'label': 'A:C Ratio', 'value': 'A:C Ratio'}
                        ],
                        value='Velocity',  # default
                        clearable=False
                    ),
                    width=9
                )
            ], className="mb-3"),
            dcc.Graph(id='metric-graph')
        ])
    ], className="mb-4"),

    html.Hr(),

    # --- Filters Section ---
    dbc.Card([
        dbc.CardBody([
            html.H4("Filters", className="card-title"),
            html.Div(id='filter-container')
        ])
    ], className="mb-4"),

    # --- NEW Throw-by-Throw Velocity Scatter Chart ---
    dbc.Card([
        dbc.CardBody([
            html.H4("Velocity of Each Throw", className="card-title"),
            dcc.Graph(id='throw-velocity-graph')
        ])
    ], className="mb-4"),

    # --- Summary Table Section ---
    dbc.Card([
        dbc.CardBody([
            html.H4("Summary Statistics", className="card-title"),
            dash_table.DataTable(
                id='summary-table',
                columns=[],  # Columns will now be dynamically generated
                style_cell={'textAlign': 'center'},
                style_header={'fontWeight': 'bold'},
                tooltip_data=[],  # Dynamically updated
                tooltip_duration=None,  # Tooltips stay visible while hovering
                style_data_conditional=[
                    {
                        'if': {'column_id': 'Peak Velocity/Torque'},
                        'type': 'numeric',
                        'backgroundColor': 'white',
                        'color': 'black'
                    },
                    {
                        'if': {
                            'filter_query': '{Average Velocity} = "-"',
                            'column_id': 'Average Velocity'
                        },
                        'backgroundColor': '#f0f0f0',
                        'color': '#a0a0a0',
                        'fontStyle': 'italic'
                    },
                    *[
                        {
                            'if': {
                                'filter_query': f'{{{col}}} = "-"',
                                'column_id': col
                            },
                            'backgroundColor': '#f0f0f0',
                            'color': '#a0a0a0',
                            'fontStyle': 'italic'
                        }
                        for col in [
                            'Average Velocity', 'Average Arm Speed', 'Average Torque',
                            'Maximum Velocity', 'Peak Velocity', 'Peak Arm Speed',
                            'Peak Torque', 'Peak Velocity/Torque'
                        ]
                    ]
                ]
            )
        ])
    ], className="mb-4"),
], fluid=True)

# ----------------------------
# Helper function: Parse uploaded file
# ----------------------------
def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

    # Rename columns to match expected names in the Dash app
    column_map = {
        'datetime': 'Date',
        'tag': 'Drill',
        'ballWeight': 'Ball',
        'ballVelocity': 'Velocity',
        'armSpeed': 'Arm Speed',
        'torque': 'Torque'
    }

    df = df.rename(columns=column_map)

    # Convert 'Date' to datetime format
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date

    # Remap ball weights for consistent display
    ball_remap = {
        5: '5oz',
        5.11472: '5oz',
        6: '6oz',
        7: '7oz',
        9: '9oz',
        11: '11oz',
        3.5273962020874023: '100g',
        4.409245014190674: '125g',
        5.2910943031311035: '150g',
        7.936641216278076: '225g',
        9.700339317321777: '275g',
        12.34588623046875: '350g',
        15.873282432556152: '450g',
        35.27396011352539: '1000g',
        52.91094207763672: '1500g',
        70.54792022705078: '2000g',
        16: 'Football'
    }
    df['Ball'] = df['Ball'].astype(float).map(ball_remap).fillna(df['Ball'])

    # Ensure required columns exist
    for col in ['Velocity', 'Torque', 'Arm Speed']:
        if col not in df.columns:
            df[col] = pd.NA

    return df

# ----------------------------
# Callback to dynamically generate filters
# ----------------------------
@app.callback(
    Output('filter-container', 'children'),
    Input('upload-data', 'contents')
)
def generate_filters(contents):
    if contents is None:
        return []

    df = parse_contents(contents)

    # List only valid filters based on the actual columns in the uploaded DataFrame
    filter_candidates = ['Date', 'Drill', 'Ball']
    dropdowns = []

    for col in filter_candidates:
        if col in df.columns:
            raw_vals = df[col].dropna().astype(str).unique()
            dropdowns.append(
                dbc.Row([
                    dbc.Col(html.Label(f"Filter by {col}")),
                    dbc.Col(
                        dcc.Dropdown(
                            id=f'filter-{col}',
                            options=[{'label': val, 'value': val} for val in
                                     sorted(raw_vals)],
                            multi=True
                        )
                    )
                ], className='mb-2')
            )

    # --- Add Clear Filters Button here ---
    dropdowns.append(
        dbc.Row([
            dbc.Button(
                "Clear All Filters",
                id="clear-filters-btn",
                color="secondary",
                className="mt-3",
                disabled=True  # Start disabled
            )
        ])
    )
    return dropdowns

# ----------------------------
# Callback to update graph and full session summary
# ----------------------------
@app.callback(
    [Output('throw-velocity-graph', 'figure'),
     Output('summary-table', 'data'),
     Output('summary-table', 'columns')],
    [Input('upload-data', 'contents'),
     Input('filter-Date', 'value'),
     Input('filter-Drill', 'value'),
     Input('filter-Ball', 'value')]
)
def update_outputs(contents, date_filter, drill_filter, ball_filter):
    if contents is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # --- Parse uploaded file ---
    df_full = parse_contents(contents)

    # Ensure Date is datetime
    df_full['Date'] = pd.to_datetime(df_full['Date'], errors='coerce').dt.date
    df_full = df_full.dropna(subset=['Date'])

    # Calculate One Day Workload (ODW) per throw
    df_full['Torque'] = pd.to_numeric(df_full['Torque'], errors='coerce')
    df_full['ODW'] = (df_full['Torque'].fillna(0) / (1.9558 * 108.862)) ** 1.3

    # Build daily workload map
    daily_odw = df_full.groupby('Date')['ODW'].sum().to_dict()
    all_dates_sorted = sorted(daily_odw.keys())

    # --- Apply Filters for Summary Table and Throw-by-Throw Chart ---
    df_filtered = df_full.copy()

    # Ensure string comparisons for filters
    df_full['Ball'] = df_full['Ball'].astype(str)
    df_full['Drill'] = df_full['Drill'].astype(str)
    df_full['Date'] = df_full['Date'].astype(str)  # for dropdown match
    df_filtered['Date'] = df_filtered['Date'].astype(str)

    if date_filter:
        df_filtered = df_filtered[df_filtered['Date'].isin(date_filter)]
    if drill_filter:
        df_filtered = df_filtered[df_filtered['Drill'].isin(drill_filter)]
    if ball_filter:
        df_filtered = df_filtered[df_filtered['Ball'].isin(ball_filter)]

    if df_filtered.empty:
        return dash.no_update, [], []

    # -- Convert back to datetime.date for grouping/summary
    df_filtered['Date'] = pd.to_datetime(df_filtered['Date']).dt.date

    # --- Build Throw-by-Throw Velocity Chart (filtered) ---
    color_map = {
        "1000g": "green",
        "450g": "blue",
        "225g": "lightcoral",  # light red
        "150g": "yellow",
        "100g": "gray",
        "9oz": "darkgreen",
        "7oz": "darkred",
        "5oz +5%": "orange",
        "5oz": "black"
    }

    scatter_fig = px.scatter(
        df_filtered,
        x="Date",
        y="Velocity",
        color="Ball",
        color_discrete_map=color_map,
        title="Velocity of Each Throw",
        labels={"Velocity": "Velocity", "Date": "Date"}
    )

    scatter_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Velocity",
        legend_title="Ball Type",
        plot_bgcolor="white",
        xaxis=dict(
            showgrid=True,
            gridcolor="#e0e0e0"
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#e0e0e0"
        )
    )

    # --- Detect active filters ---
    ball_filter_active = bool(ball_filter)
    drill_filter_active = bool(drill_filter)
    filters_active = any([date_filter, drill_filter, ball_filter])

    # --- Group and Build Summary Statistics ---
    group_cols = ['Date']

    summary_rows = []

    df_filtered['Date'] = pd.to_datetime(df_filtered['Date'], errors='coerce').dt.date

    for group_keys, group in df_filtered.groupby(group_cols):
        # Always allow empty groups (we'll insert placeholders)
        # Convert group_keys to tuple for safe unpacking
        if not isinstance(group_keys, tuple):
            group_keys = (group_keys,)

        session_date = pd.to_datetime(group_keys[0]).date()
        ball = drill = "-"

        # Always treat group_keys as a tuple
        if not isinstance(group_keys, tuple):
            group_keys = (group_keys,)

        session_date = group_keys if not isinstance(group_keys, tuple) else group_keys[0]
        ball = drill = "-"

        # Preserve display values for Ball/Drill only if user is filtering by them
        if ball_filter_active:
            ball = ", ".join(sorted(set(df_filtered['Ball'])))
        if drill_filter_active:
            drill = ", ".join(sorted(set(df_filtered['Drill'])))

        n_throws = len(group)

        avg_velocity = group['Velocity'].mean()
        avg_arm_speed = group['Arm Speed'].mean()
        avg_torque = group['Torque'].mean()
        max_velocity = group['Velocity'].max()

        # Safely calculate Peak stats
        if 'Velocity' in group and group['Velocity'].dropna().shape[0] >= 1:
            threshold = group['Velocity'].quantile(0.90)
            top_throws = group[group['Velocity'] >= threshold]
        else:
            top_throws = pd.DataFrame()

        if not top_throws.empty:
            peak_velocity = top_throws['Velocity'].mean()
            peak_arm_speed = top_throws['Arm Speed'].mean()
            peak_torque = top_throws['Torque'].mean()
            peak_velocity_torque = peak_velocity / peak_torque if peak_torque != 0 else "-"
        else:
            peak_velocity = peak_arm_speed = peak_torque = peak_velocity_torque = "-"

        # ---- A:C Ratio Calculation ----
        acute_kernel = [0.7, 0.775, 0.85, 0.925, 1.0, 1.075, 1.15, 1.225, 1.3]
        acute_vals = []
        chronic_vals = []

        for i in range(28):
            offset_date = session_date - timedelta(days=i)
            odw = daily_odw.get(offset_date, 0)
            if i < 9:
                acute_vals.append(acute_kernel[8 - i] * odw)
            chronic_vals.append(odw)

        acute_days = sum(1 for i in range(9) if (session_date - timedelta(days=i)) in daily_odw)
        chronic_days = sum(1 for v in chronic_vals if v > 0)

        acute = sum(acute_vals) / max(min(acute_days, 9), 3) if acute_days >= 3 else None
        chronic = sum(chronic_vals) / chronic_days if chronic_days >= 5 else None

        # Robust A:C Ratio calculation
        try:
            ac_ratio = round(float(acute) / float(chronic), 2)
        except (ValueError, TypeError, ZeroDivisionError):
            ac_ratio = "-"

        summary_rows.append({
            'Ball': ball,
            'Drill': drill,
            'Date': session_date.strftime('%Y-%m-%d'),
            'Number of Throws': n_throws,
            'Average Velocity': safe_mean(group, 'Velocity'),
            'Average Arm Speed': safe_int_mean(group, 'Arm Speed'),
            'Average Torque': safe_mean(group, 'Torque'),
            'Maximum Velocity': safe_max(group, 'Velocity'),
            'Peak Velocity': safe_mean(top_throws, 'Velocity'),
            'Peak Arm Speed': safe_int_mean(top_throws, 'Arm Speed'),
            'Peak Torque': safe_mean(top_throws, 'Torque'),
            'Peak Velocity/Torque': round(peak_velocity_torque, 2) if (peak_torque != 0 and peak_torque != "-") else "-",
            'One Day Workload': round(group['ODW'].sum(), 2) if not group['Torque'].dropna().empty else "-",
            'A:C Ratio': ac_ratio
        })

    summary_df = pd.DataFrame(summary_rows)

    # --- Sort the Summary Table ---
    if filters_active:
        summary_df = summary_df.sort_values(by=['Ball', 'Drill', 'Date'])
    else:
        summary_df = summary_df.sort_values(by=['Date'])

    # --- Build Columns Dynamically ---
    columns = []

    if ball_filter_active:
        columns.append({'name': 'Ball', 'id': 'Ball'})
    if drill_filter_active:
        columns.append({'name': 'Drill', 'id': 'Drill'})

    columns += [
        {'name': 'Date', 'id': 'Date'},
        {'name': 'A:C Ratio', 'id': 'A:C Ratio'},
        {'name': 'One Day Workload', 'id': 'One Day Workload'},
        {'name': 'Number of Throws', 'id': 'Number of Throws'},
        {'name': 'Average Velocity', 'id': 'Average Velocity'},
        {'name': 'Average Arm Speed', 'id': 'Average Arm Speed'},
        {'name': 'Average Torque', 'id': 'Average Torque'},
        {'name': 'Maximum Velocity', 'id': 'Maximum Velocity'},
        {'name': 'Peak Velocity', 'id': 'Peak Velocity'},
        {'name': 'Peak Arm Speed', 'id': 'Peak Arm Speed'},
        {'name': 'Peak Torque', 'id': 'Peak Torque'},
        {'name': 'Peak Velocity/Torque', 'id': 'Peak Velocity/Torque'},
    ]

    return scatter_fig, summary_df.to_dict('records'), columns

# ----------------------------
# Add a clear filters button
# ----------------------------
@app.callback(
    [Output('filter-Date', 'value'),
     Output('filter-Drill', 'value'),
     Output('filter-Ball', 'value')],
    Input('clear-filters-btn', 'n_clicks'),
    prevent_initial_call=True
)
def clear_filters(n_clicks):
    # Setting all dropdown values to None (cleared)
    return None, None, None

# ----------------------------
# Enable clear filters button when a filter is selected
# ----------------------------
@app.callback(
    Output('clear-filters-btn', 'disabled'),
    [Input('filter-Date', 'value'),
     Input('filter-Drill', 'value'),
     Input('filter-Ball', 'value')]
)
def toggle_clear_button(date, drill, ball):
    # If all filters are empty, disable the button
    if not date and not drill and not ball:
        return True  # disabled
    return False  # enabled

# ----------------------------
# Create a dynamic coloring callback
# ----------------------------
@app.callback(
    Output('summary-table', 'style_data_conditional'),
    Input('summary-table', 'data')
)
def update_peak_velocity_torque_colors(table_data):
    if not table_data:
        return []

    # Extract Peak Velocity/Torque values
    peak_vt_values = [
        float(row['Peak Velocity/Torque'])
        for row in table_data
        if isinstance(row['Peak Velocity/Torque'], (int, float)) or (
                isinstance(row['Peak Velocity/Torque'], str) and row['Peak Velocity/Torque'].replace('.', '',
                                                                                                      1).isdigit()
        )
    ]

    if not peak_vt_values:
        return []

    min_val = min(peak_vt_values)
    max_val = max(peak_vt_values)
    range_val = max_val - min_val if (max_val - min_val) != 0 else 1

    # Define color scale manually
    def color_scale(value):
        # Normalize between 0 and 1
        norm = (value - min_val) / range_val
        if norm < 0.5:
            # From Red to White
            red = 255
            green = int(255 * (norm * 2))
            blue = int(255 * (norm * 2))
        else:
            # From White to Green
            red = int(255 * (1 - (norm - 0.5) * 2))
            green = 255
            blue = int(255 * (1 - (norm - 0.5) * 2))

        return f'rgb({red},{green},{blue})'

    return [
        {
            'if': {
                'filter_query': f'{{Peak Velocity/Torque}} = {value}',
                'column_id': 'Peak Velocity/Torque'
            },
            'backgroundColor': color_scale(value),
            'color': 'black'
        }
        for value in peak_vt_values
    ]


# ----------------------------
# Sets tooltips based on missing data
# ----------------------------
@app.callback(
    Output('summary-table', 'tooltip_data'),
    Input('summary-table', 'data')
)
def update_tooltips(table_data):
    if not table_data:
        return []

    tooltip = []

    for row in table_data:
        tooltip_row = {}
        for col in row:
            if row[col] == "-":
                tooltip_row[col] = {'value': 'No data available', 'type': 'text'}
            else:
                tooltip_row[col] = {'value': '', 'type': 'text'}  # Empty tooltip for normal cells
        tooltip.append(tooltip_row)

    return tooltip

# --- Build dynamic charts for summary metrics ---
@app.callback(
    Output('metric-graph', 'figure'),
    [Input('upload-data', 'contents'),
     Input('metric-selector', 'value')]
)
def update_metric_chart(contents, selected_metric):
    if contents is None:
        return dash.no_update

    df = parse_contents(contents)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
    df = df.dropna(subset=['Date'])

    df['ODW'] = (df['Torque'].fillna(0) / (1.9558 * 108.862)) ** 1.3

    if selected_metric == 'Velocity':
        df_velocity = df[['Date', 'Velocity']].dropna()
        df_metric = df_velocity.groupby('Date')['Velocity'].max().reset_index()
    else:
        summary_metric_map = {
            'Number of Throws': 'Number of Throws',  # placeholder key; logic handled separately
            'Average Velocity': 'Velocity',
            'Average Arm Speed': 'Arm Speed',
            'Average Torque': 'Torque',
            'Peak Velocity': 'Velocity',
            'Peak Arm Speed': 'Arm Speed',
            'Peak Torque': 'Torque',
            'Peak Velocity/Torque': ('Velocity', 'Torque'),
            'ODW': 'ODW',
            'A:C Ratio': None  # Optional to implement later
        }

        col = summary_metric_map[selected_metric]

        if selected_metric == 'A:C Ratio':
            # Compute ODW per date
            df['ODW'] = (df['Torque'] / (1.9558 * 108.862)) ** 1.3
            df_odw = df.groupby('Date')['ODW'].sum()

            ac_ratios = []
            for date in df_odw.index:
                acute_kernel = [0.7, 0.775, 0.85, 0.925, 1.0, 1.075, 1.15, 1.225, 1.3]
                acute_vals = []
                chronic_vals = []

                for i in range(28):
                    offset = timedelta(days=i)
                    odw_val = df_odw.get(date - offset, 0)
                    if i < 9:
                        acute_vals.append(acute_kernel[8 - i] * odw_val)
                    chronic_vals.append(odw_val)

                acute_days = sum(1 for i in range(9) if (date - timedelta(days=i)) in df_odw)
                chronic_days = sum(1 for val in chronic_vals if val > 0)

                acute = sum(acute_vals) / max(min(acute_days, 9), 3) if acute_days >= 3 else None
                chronic = sum(chronic_vals) / chronic_days if chronic_days >= 5 else None

                if acute is not None and chronic is not None and chronic > 0:
                    ac_ratio = round(acute / chronic, 2)
                else:
                    ac_ratio = None

                ac_ratios.append((date, ac_ratio))

            df_metric = pd.DataFrame(ac_ratios, columns=['Date', 'A:C Ratio']).dropna()
            # skip the rest of the metric-building logic
        else:
            if isinstance(col, tuple):
                df['peak'] = df.groupby('Date')[col[0]].transform(lambda g: g.quantile(0.90).mean())
                df['torque_peak'] = df.groupby('Date')[col[1]].transform(lambda g: g.quantile(0.90).mean())
                df['metric'] = df['peak'] / df['torque_peak']
            else:
                if selected_metric.startswith('Peak'):
                    df['metric'] = df.groupby('Date')[col].transform(lambda g: g[g >= g.quantile(0.90)].mean())
                elif selected_metric.startswith('Average'):
                    df['metric'] = df.groupby('Date')[col].transform('mean')
                elif selected_metric == 'ODW':
                    df['metric'] = (df['Torque'] / (1.9558 * 108.862)) ** 1.3
                    df['metric'] = df.groupby('Date')['metric'].transform('sum')
                elif selected_metric == 'Number of Throws':
                    df_metric = df.groupby('Date').size().reset_index(name='Number of Throws')
                else:
                    df['metric'] = df[col]

        if selected_metric != 'A:C Ratio' and selected_metric != 'Number of Throws':
            df_metric = df[['Date', 'metric']].dropna().drop_duplicates().sort_values(by='Date')
            df_metric.rename(columns={'metric': selected_metric}, inplace=True)

    # Create a bar graph for ODW and a line chart for all other metrics
    if selected_metric == 'ODW':
        # Compute both ODW and A:C Ratio
        df_odw = df.groupby('Date')['ODW'].sum()
        dates = df_odw.index

        # Compute A:C ratio
        ac_ratios = []
        for date in dates:
            acute_kernel = [0.7, 0.775, 0.85, 0.925, 1.0, 1.075, 1.15, 1.225, 1.3]
            acute_vals = []
            chronic_vals = []
            for i in range(28):
                offset = timedelta(days=i)
                odw_val = df_odw.get(date - offset, 0)
                if i < 9:
                    acute_vals.append(acute_kernel[8 - i] * odw_val)
                chronic_vals.append(odw_val)

            acute_days = sum(1 for i in range(9) if (date - timedelta(days=i)) in df_odw)
            chronic_days = sum(1 for val in chronic_vals if val > 0)

            acute = sum(acute_vals) / max(min(acute_days, 9), 3) if acute_days >= 3 else None
            chronic = sum(chronic_vals) / chronic_days if chronic_days >= 5 else None

            if acute is not None and chronic is not None and chronic > 0:
                ac_ratio = round(acute / chronic, 2)
            else:
                ac_ratio = None

            ac_ratios.append(ac_ratio)

        df_combo = pd.DataFrame({
            'Date': dates,
            'ODW': df_odw.values,
            'A:C Ratio': ac_ratios
        })

        # Create dual-axis chart
        fig = go.Figure()

        fig.add_bar(
            x=df_combo['Date'],
            y=df_combo['ODW'],
            name='ODW',
            yaxis='y1'
        )

        fig.add_trace(
            go.Scatter(
                x=df_combo['Date'],
                y=df_combo['A:C Ratio'],
                name='A:C Ratio',
                yaxis='y2',
                mode='lines+markers'
            )
        )

        fig.update_layout(
            title="One Day Workload and A:C Ratio Over Time",
            xaxis=dict(title='Date'),
            yaxis=dict(
                title='One Day Workload',
                showgrid=True,
                gridcolor="#e0e0e0"
            ),
            yaxis2=dict(
                title='A:C Ratio',
                overlaying='y',
                side='right',
                range=[0.4,2.4]
            ),
            legend=dict(x=0.01, y=0.99),
            plot_bgcolor="white",
            shapes=[
                # Green zone (safe)
                dict(
                    type="rect",
                    xref="paper",  # full x-axis span
                    yref="y2",
                    x0=0,
                    x1=1,
                    y0=0.7,
                    y1=1.3,
                    fillcolor="rgba(144,238,144,0.3)",  # light green
                    layer="below",
                    line_width=0,
                ),
                # Red zone (high)
                dict(
                    type="rect",
                    xref="paper",
                    yref="y2",
                    x0=0,
                    x1=1,
                    y0=1.3,
                    y1=2.4,
                    fillcolor="rgba(255,99,71,0.25)",  # tomato red
                    layer="below",
                    line_width=0,
                ),
                # Red zone (low)
                dict(
                    type="rect",
                    xref="paper",
                    yref="y2",
                    x0=0,
                    x1=1,
                    y0=0,
                    y1=0.7,
                    fillcolor="rgba(255,99,71,0.25)",
                    layer="below",
                    line_width=0,
                )
            ]
        )

    else:
        # All other metrics (line chart)
        fig = px.line(
            df_metric,
            x='Date',
            y=selected_metric,
            title=f"{selected_metric} Over Time",
            markers=True
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=selected_metric,
            plot_bgcolor="white",
            xaxis=dict(showgrid=True, gridcolor="#e0e0e0"),
            yaxis=dict(showgrid=True, gridcolor="#e0e0e0")
        )

    return fig

# ----------------------------
# Run the Dash app
# ----------------------------
if __name__ == '__main__':
    app.run(
        debug=False,  # Set True if you want to auto-reload on changes (may not work if threads restricted)
        host="0.0.0.0",
        port=8051,
        use_reloader=False,
        threaded=False
    )
