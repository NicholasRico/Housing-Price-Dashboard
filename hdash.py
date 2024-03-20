import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import numpy as np
from statsmodels.tsa.arima.model import ARIMA

# Load housing data
housing_data = pd.read_csv("housing_data.csv")

# Melt the wide-format dataset into a long format
housing_data_long = pd.melt(housing_data, id_vars=['RegionName'], var_name='Date', value_name='Price')
housing_data_long['Date'] = pd.to_datetime(housing_data_long['Date'], errors='coerce')
housing_data_long['Price'] = pd.to_numeric(housing_data_long['Price'], errors='coerce')

# Define a function to calculate average home sale and percentage change vs prior year for each year
def calculate_yearly_metrics(data):
    yearly_metrics = data.groupby(data['Date'].dt.year)['Price'].agg(['mean']).reset_index()
    yearly_metrics.columns = ['Year', 'Average Home Sale']
    yearly_metrics['PY Average Home Sale'] = yearly_metrics['Average Home Sale'].shift(fill_value=0)
    yearly_metrics['Average Home Sale'] = yearly_metrics['Average Home Sale'].round().astype(int)
    
    # Calculate percentage change vs prior year
    prior_year_avg = yearly_metrics['PY Average Home Sale']
    yearly_metrics['% Change vs PY'] = ((yearly_metrics['Average Home Sale'] - prior_year_avg) / np.where((prior_year_avg == 0) | (prior_year_avg.isna()), np.nan, prior_year_avg)) * 100
    yearly_metrics['% Change vs PY'] = yearly_metrics['% Change vs PY'].round(2)
    
    return yearly_metrics

# Define a function to forecast next 24 months of home sales
def forecast_next_24_months(data):
    model = ARIMA(data, order=(5,1,0))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=24)
    return forecast

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
    dcc.Graph(id='forecast-graph'),
    
    # Center aligned div for 'Year Average Home Sale % Change vs Prior Year' table
    html.Div(id='average-sales-text', style={'text-align': 'center'}),
    
    # Center aligned divs for top 10 highest and lowest tables
    html.Div([
        html.Div([
            html.H3("Top 10 Highest value home locations over last 10 years", style={'text-align': 'center', 'font-weight': 'bold', 'color': '#0000FF'}),
            html.Table(id='top-10-highest-values', style={'margin': 'auto', 'text-align': 'center'})
        ], style={'display': 'inline-block', 'width': '45%'}),
        html.Div([
            html.H3("Top 10 Lowest value home locations over last 10 years", style={'text-align': 'center', 'font-weight': 'bold', 'color': '#0000FF'}),
            html.Table(id='top-10-lowest-values', style={'margin': 'auto', 'text-align': 'center'})
        ], style={'display': 'inline-block', 'width': '45%'})
    ], style={'text-align': 'center'})
])

# Callback to update charts based on selected region
@app.callback(
    [Output('revenue-trends-graph', 'figure'),
     Output('sales-performance-bar', 'figure'),
     Output('forecast-graph', 'figure'),
     Output('average-sales-text', 'children'),
     Output('top-10-highest-values', 'children'),
     Output('top-10-lowest-values', 'children')],
    [Input('region-dropdown', 'value')]
)
def update_charts(selected_region):
    filtered_data = housing_data_long[housing_data_long['RegionName'] == selected_region]
    
    # Check if there's enough data
    if len(filtered_data) < 2:
        return {}, {}, {}, {}, {}, {}

    # Ensure 'Price' column is numeric
    filtered_data['Price'] = pd.to_numeric(filtered_data['Price'], errors='coerce')

    # Create the line plot with customized format
    line_fig = px.line(filtered_data, x='Date', y='Price', title=f'Home Value Trends for {selected_region}',
                  line_shape='spline', color_discrete_sequence=['#FF0055'])

    # Create the bar plot with customized format
    bar_fig = px.bar(filtered_data, x='Date', y='Price', title=f'Home Value Trends for {selected_region}',
                     labels={'Date': 'Date', 'Price': 'Price'}, color_discrete_sequence=['#0000FF'])

    # Forecast next 24 months of home sales
    forecast_data = forecast_next_24_months(filtered_data['Price'])
    forecast_dates = pd.date_range(start=filtered_data['Date'].iloc[-1], periods=25, freq='ME')[1:]  
    forecast_df = pd.DataFrame({'Date': forecast_dates, 'Forecast': forecast_data})
    forecast_fig = px.line(forecast_df, x='Date', y='Forecast', 
                           title=f'Forecast for Next 24 Months in {selected_region}',
                           color_discrete_sequence=['#FF0055'])

    # Calculate average home sale and percentage change vs prior year for each year
    yearly_metrics = calculate_yearly_metrics(filtered_data)
    
    # Create text box with average home sale and percentage change vs prior year for each year
    text_box = html.Div([
    html.H3("Average Home Value by Year", style={'text-align': 'center'}),
    html.Table(
        [html.Tr([html.Th(col, style={'text-align': 'center', 'border': '1px solid black', 'padding': '8px', 'font-weight': 'bold', 'color': '#0000FF'}) for col in ['Year', 'Average Home Sale', '% Change vs PY']])] +
        [html.Tr([html.Td(html.Strong(str(int(year))), style={'text-align': 'center', 'border': '1px solid black', 'padding': '8px', 'color': '#0000FF'}),
                  html.Td(f"${avg:,.0f}", style={'text-align': 'center', 'border': '1px solid black', 'padding': '8px', 'color': '#0000FF'}),
                  html.Td(f"{change:.2f}%" if not np.isnan(change) else "", style={'text-align': 'center', 'border': '1px solid black', 'padding': '8px', 'color': '#0000FF'})]) 
         for year, avg, change in yearly_metrics[['Year', 'Average Home Sale', '% Change vs PY']].itertuples(index=False)]
    )
])



    # Calculate top 10 highest and lowest average home values
    top_10_highest = housing_data_long.groupby('RegionName')['Price'].mean().nlargest(10)
    top_10_lowest = housing_data_long.groupby('RegionName')['Price'].mean().nsmallest(10)
    
    # Format the output for display
    top_10_highest_formatted = html.Table(
        [html.Tr([html.Th("Region Name", style={'text-align': 'center', 'font-weight': 'bold', 'color': '#0000FF'}), html.Th("Average Home Value", style={'text-align': 'center', 'font-weight': 'bold', 'color': '#0000FF'})])] +
        [html.Tr([html.Td(region, style={'text-align': 'center'}), html.Td(f"${value:,.0f}", style={'text-align': 'center'})]) for region, value in top_10_highest.items()]
    )

    top_10_lowest_formatted = html.Table(
        [html.Tr([html.Th("Region Name", style={'text-align': 'center', 'font-weight': 'bold', 'color': '#0000FF'}), html.Th("Average Home Value", style={'text-align': 'center', 'font-weight': 'bold', 'color': '#0000FF'})])] +
        [html.Tr([html.Td(region, style={'text-align': 'center'}), html.Td(f"${value:,.0f}", style={'text-align': 'center'})]) for region, value in top_10_lowest.items()]
    )

    return line_fig, bar_fig, forecast_fig, text_box, top_10_highest_formatted, top_10_lowest_formatted


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
