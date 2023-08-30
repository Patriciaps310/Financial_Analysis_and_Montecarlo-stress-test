import yfinance as yf
import datetime as datetime
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
from dash import dash, dcc, html, Input, Output
import talib as ta

# Get the stock data from 50 possible tickers
tickers = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "FB", "TSLA", "NVDA", "JPM", "JNJ", "V",
    "WMT", "MA", "PG", "UNH", "HD", "VZ", "BAC", "DIS", "PYPL", "ADBE", "CMCSA",
    "NFLX", "INTC", "PFE", "KO", "PEP", "CSCO", "ABT", "ABBV", "T", "NKE", "ORCL",
    "MRK", "CRM", "XOM", "IBM", "AMGN", "CVX", "AVGO", "TMO", "MDT", "WFC", "COST",
    "MCD", "ACN", "QCOM", "HON", "TXN", "PM", "MMM", "GE"
]

# Create the Dash app

app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div(children=[
    html.H1("Stock Analysis", style={'text-align': ' center'}),
    dcc.Dropdown(
        id='ticker-dropdown',
        options=[{'label': ticker, 'value': ticker} for ticker in tickers],
        value=tickers[0]  # set default value,

    ),

    html.H3("Predicted Price on Date:"),
    dcc.DatePickerSingle(
        id='date-picker',
        date=(datetime.datetime.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
        # set default date to a month from now
        min_date_allowed=datetime.datetime.today().strftime("%Y-%m-%d"),
        max_date_allowed=(datetime.datetime.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
        display_format='YYYY-MM-DD'
    ),

    html.H2("Stock Price - Past 10 Years"),
    dcc.Graph(id='stock-prices'),
    html.H2("Stock Analysis"),
    dcc.Graph(id='candlestick'),
    html.H2("Monte Carlo Simulation - Stock Prices"),
    dcc.Graph(id='monte-carlo-simulation'),
    html.H2("Distribution of Predicted Prices"),
    dcc.Graph(id='histogram')
])


# connect the plotly graphs with  dash  components
@app.callback([
    Output(component_id='stock-prices', component_property='figure'),
    Output(component_id='candlestick', component_property='figure'),
    Output(component_id='monte-carlo-simulation', component_property='figure'),
    Output(component_id='histogram', component_property='figure'),
    Input(component_id='ticker-dropdown', component_property='value'),
    Input(component_id='date-picker', component_property='date')
])
def update_graphs(ticker, selected_date):  # argument in this function always refers to component property of input

    end_date = datetime.datetime.today().strftime("%Y-%m-%d")

    # get past 10years of data
    start_date = (datetime.datetime.today() - datetime.timedelta(days=365 * 10)).strftime("%Y-%m-%d")
    stock_data = yf.download(ticker, start=start_date, end=end_date)

    # calculate returns using percent change from previous record
    returns = np.log(1 + stock_data['Close'].pct_change())

    # Define the number of simulations and trading days
    simulations = 500
    # set the number of business days that will run in each simulation
    trading_days = np.busday_count(np.datetime64(datetime.datetime.today().strftime("%Y-%m-%d")), selected_date)

    # save the simulated prices
    simulated_prices = [0] * simulations
    for i in range(simulations):
        prices = [0] * (trading_days + 1)
        latest_price = stock_data['Close'].iloc[1]
        prices[0] = latest_price
        for j in range(trading_days):
            # choose a random return following a normal distribution of the returns calculated
            random_returns = np.random.normal(returns.mean(), returns.std())
            # exponent of log to return a vlue that can be multiplied
            latest_price = latest_price * np.exp(random_returns)
            prices[j + 1] = latest_price

        simulated_prices[i] = prices

    # set dates
    last_date = stock_data.index[-1]
    future_dates = [last_date + datetime.timedelta(days=i) for i in range(trading_days)]

    # add exponential moving average to plot
    stock_data['EMA_12'] = ta.EMA(stock_data['Close'], 12)

    # add RSI
    stock_data['RSI'] = ta.RSI(stock_data['Close'])

    # Create the figure for the historical stock prices
    fig_stock_prices = go.Figure()

    fig_stock_prices.add_trace(go.Scatter(
        x=stock_data.index,
        y=stock_data['Close'],
        line=dict(color='blue', width=0.7),
        name='Historical Stock Prices',
        showlegend=False))

    fig_stock_prices.update_layout(
        title=f"{ticker} Stock Price - Past 10 Years",
        yaxis_title="Price (USD)"
    )

    # create candlestick graph

    # Create the figure for the historical stock prices
    fig_candlestick = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.01,
        row_width=[0.2, 0.1, 0.2, 0.5]
    )

    fig_candlestick.add_trace(
        go.Candlestick(
            x=stock_data.iloc[-252:].index,
            open=stock_data['Open'],
            high=stock_data['High'],
            low=stock_data['Low'],
            close=stock_data['Close'],
            showlegend=False),
        row=1, col=1)

    # add volume bars
    fig_candlestick.add_trace(
        go.Bar(x=stock_data.iloc[-252:].index,
               y=stock_data['Volume'],
               showlegend=False,
               marker={
                   "color": "grey",
               }),
        row=2, col=1
    )

    # add moving average line
    fig_candlestick.add_trace(go.Scatter(
        x=stock_data.iloc[-252:].index,
        y=stock_data['EMA_12'],
        line=dict(color='red', width=0.7),
        name='12-day Exponential Moving Average',
        showlegend=False),
        row=1, col=1)

    # add RSI graph
    fig_candlestick.add_trace(go.Scatter(
        x=stock_data.iloc[-252:].index,
        y=stock_data['RSI'],
        line=dict(color='blue', width=0.4),
        name='RSI',
        showlegend=False),
        row=3, col=1)

    # add oversold/overbought lines
    fig_candlestick.add_hline(
        y=30,
        line_dash='dash',
        line_color='green',
        line_width=0.2,
        row=3, col=1)

    # add oversold/overbought lines
    fig_candlestick.add_hline(
        y=70,
        line_dash='dash',
        line_color='red',
        line_width=0.2,
        row=3, col=1)

    # MCD

    macd, macdsignal, macdhist = ta.MACD(stock_data['Close'],
                                         slowperiod=26,
                                         fastperiod=12,
                                         signalperiod=9,
                                         )

    fig_candlestick.add_trace(go.Bar(
        x=stock_data.iloc[-252:].index,
        y=macdhist,
        showlegend=False
    ), row=4, col=1

    )

    fig_candlestick.add_trace(go.Scatter(
        x=stock_data.iloc[-252:].index,
        y=macd,
        line=dict(color='black', width=0.5,),
        showlegend=False
    ),
        row=4, col=1
    )

    fig_candlestick.add_trace(go.Scatter(
        x=stock_data.iloc[-252:].index,
        y=macdsignal,
        line=dict(color='red', width=0.5),
        showlegend=False),
        row=4, col=1
    )

    fig_candlestick.update_layout(
        title=f"{ticker} Stock Analysis - Past Year",
        yaxis_title="Price (USD)",
        height=800,
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )

    # remove slider
    fig_candlestick.update(layout_xaxis_rangeslider_visible=False)
    # hide weekends
    fig_candlestick.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

    # update y-axis label
    fig_candlestick.update_yaxes(title_text="OHLC", row=1, col=1)
    fig_candlestick.update_yaxes(title_text="Volume", row=2, col=1)
    fig_candlestick.update_yaxes(title_text="RSI", showgrid=False, row=3, col=1)
    fig_candlestick.update_yaxes(title_text="MACD", row=4, col=1)

    # create figure simulation for monte carlo simulation
    fig_monte_carlo = go.Figure()
    for i in range(simulations):
        # choose a random color
        color = f"rgb({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)})"
        fig_monte_carlo.add_trace(go.Scatter(
            x=future_dates,  # date values
            y=simulated_prices[i],  # simulated closing prices
            line=dict(color=color),
            showlegend=False  # Remove legend for each trace

        ))

    fig_monte_carlo.update_layout(
        title=f"{ticker} Monte Carlo Simulation - Stock Prices",
        xaxis_title="Date",
        yaxis_title="Price ( USD)")

    # Create the figure for the histogram
    last_simulated_prices = [sublist[-1] for sublist in simulated_prices]
    fig_histogram = go.Figure(data=[go.Histogram(x=last_simulated_prices, nbinsx=200)])
    fig_histogram.add_vline(x=np.nanpercentile(last_simulated_prices, 5), line_dash='dash', line_color='firebrick')
    fig_histogram.add_vline(x=np.nanpercentile(last_simulated_prices, 95), line_dash='dash', line_color='firebrick')
    fig_histogram.update_layout(
        title="Distribution of Predicted Prices",
        xaxis_title="Price (USD)",
        yaxis_title="Frequency"
    )

    return fig_stock_prices, fig_candlestick, fig_monte_carlo, fig_histogram


if __name__ == '__main__':
    app.run_server(debug=True)
