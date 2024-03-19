import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Load housing data
housing_data = pd.read_csv("housing_data.csv")

# Melt the wide-format dataset into a long format
housing_data_long = pd.melt(housing_data, id_vars=['RegionName'], var_name='Date', value_name='Price')

# Initialize Dash app
app = dash.Dash(__name__)

# Define app layout
app.layout = html.Div([
    html.H1("Housing Sales Dashboard"),
    
    dcc.Dropdown(
        id='region-dropdown',
        options=[{'label': region, 'value': region} for region in housing_data_long['RegionName'].unique()],
        value=housing_data_long['RegionName'].unique()[0],
        multi=False,
        searchable=True,
        placeholder="Select a region..."
    ),
    
    dcc.Graph(id='revenue-trends-graph'),
    
    dcc.Graph(id='sales-performance-by-year'),
])

# Callback to update revenue trends graph based on selected region
@app.callback(
    Output('revenue-trends-graph', 'figure'),
    [Input('region-dropdown', 'value')]
)
def update_revenue_trends_graph(selected_region):
    filtered_data = housing_data_long[housing_data_long['RegionName'] == selected_region]
    fig = px.line(filtered_data, x='Date', y='Price', title=f'Revenue Trends for {selected_region}')
    return fig

# Callback to update sales performance by year graph based on selected region
@app.callback(
    Output('sales-performance-by-year', 'figure'),
    [Input('region-dropdown', 'value')]
)
def update_sales_performance_graph(selected_region):
    sales_by_year = housing_data_long.groupby(['Date', 'RegionName'])['Price'].sum().reset_index()
    filtered_data = sales_by_year[sales_by_year['RegionName'] == selected_region]
    fig = px.bar(filtered_data, x='Date', y='Price', title=f'Sales Performance by Year for {selected_region}')
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
