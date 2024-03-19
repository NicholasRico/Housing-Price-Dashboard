import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import numpy as np

# Load housing data
housing_data = pd.read_csv("housing_data.csv")

# Melt the wide-format dataset into a long format
housing_data_long = pd.melt(housing_data, id_vars=['RegionName'], var_name='Date', value_name='Price')
housing_data_long['Date'] = pd.to_datetime(housing_data_long['Date'], errors='coerce')

# Define a function to calculate average home sale and percentage change vs prior year for each year
import numpy as np

def calculate_yearly_metrics(data):
    yearly_metrics = data.groupby(data['Date'].dt.year)['Price'].agg(['mean']).reset_index()
    yearly_metrics.columns = ['Year', 'Average Home Sale']
    yearly_metrics['Prior Year Average Home Sale'] = yearly_metrics['Average Home Sale'].shift(fill_value=0)
    yearly_metrics['Average Home Sale'] = yearly_metrics['Average Home Sale'].round().astype(int)
    
    # Calculate percentage change vs prior year
    prior_year_avg = yearly_metrics['Prior Year Average Home Sale']
    yearly_metrics['% Change vs Prior Year'] = ((yearly_metrics['Average Home Sale'] - prior_year_avg) / np.where((prior_year_avg == 0) | (prior_year_avg.isna()), np.nan, prior_year_avg)) * 100
    yearly_metrics['% Change vs Prior Year'] = yearly_metrics['% Change vs Prior Year'].round(2)
    
    return yearly_metrics


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
    dcc.Graph(id='sales-performance-bar'),
    html.Div(id='average-sales-text')
])

# Callback to update revenue trends graph based on selected region
@app.callback(
    [Output('revenue-trends-graph', 'figure'),
     Output('sales-performance-bar', 'figure'),
     Output('average-sales-text', 'children')],
    [Input('region-dropdown', 'value')]
)
def update_charts(selected_region):
    filtered_data = housing_data_long[housing_data_long['RegionName'] == selected_region]
    
    # Check if there's enough data
    if len(filtered_data) < 2:
        return {}, {}, {}
    
    # Create the line plot with customized format
    line_fig = px.line(filtered_data, x='Date', y='Price', title=f'Home Value Trends for {selected_region}',
                  line_shape='spline', # Change line shape to spline
                  color_discrete_sequence=['#FF0055'] # Change line color to #FF0055
                  )
    
    # Create the bar plot with customized format
    bar_fig = px.bar(filtered_data, x='Date', y='Price', title=f'Home Value Trends for {selected_region}',
                 labels={'Date': 'Date', 'Price': 'Price'},  # Set x-axis and y-axis labels
                 color_discrete_sequence=['#0000FF']  # Change bar color to #00DBF2
                )
    
    # Calculate average home sale and percentage change vs prior year for each year
    yearly_metrics = calculate_yearly_metrics(filtered_data)
    
     # Create text box with average home sale and percentage change vs prior year for each year
    text_box = html.Table(
        # Header
        [html.Tr([html.Th("Year", style={'text-align': 'center', 'font-weight': 'bold'}), 
                  html.Th("Average Home Sale", style={'text-align': 'center', 'font-weight': 'bold'}),
                  html.Th("% Change vs Prior Year", style={'text-align': 'center', 'font-weight': 'bold'})])] +
        # Rows
        [html.Tr([html.Td(year, style={'text-align': 'center'}), 
                  html.Td(f"${avg:,.0f}", style={'text-align': 'center'}),
                  html.Td(f"{change:.2f}%" if not np.isnan(change) else "", style={'text-align': 'center'})]) for year, avg, change in yearly_metrics[['Year', 'Average Home Sale', '% Change vs Prior Year']].itertuples(index=False)]
    )
    return line_fig, bar_fig, text_box

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
