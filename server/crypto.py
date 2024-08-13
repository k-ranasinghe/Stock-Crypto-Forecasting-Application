# -*- coding: utf-8 -*-
"""Crypto.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1opW0__14RlC5yX4soQ-VHGwXlBU7M2WO
"""

import yfinance as yf
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import io
import base64

import pandas_datareader.data as web
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error,mean_absolute_error, r2_score
from copy import deepcopy as dc
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import Dataset
from torch.utils.data import DataLoader


start_date = '1900-01-01'
end_date = '2025-01-01'

# Define the tickers for Bitcoin and Ethereum
tickers = ['BTC-USD', 'ETH-USD', 'USDT-USD', 'BNB-USD', 'SOL-USD']

# Download historical data
data = yf.download(tickers, start='2015-01-01', end='2025-01-01')['Close']

target = 'Close'

# Fill missing values
data = data.fillna(method='ffill')

forcast_size = 50

# Lookback for time series
lookback = 30

batch_size = 28
global device
device = 'cuda:0' if torch.cuda.is_available() else 'cpu'

# LSTM model parameters
hidden_size = 4
num_stacked_layers = 1
learning_rate = 0.01
num_epochs = 100


def compute_rsi(data, window):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def build_model_LR(data, forcast_size, start_date, end_date, target):
  # Calculate technical indicators
  data['BTC_SMA'] = data['BTC-USD'].rolling(window=20).mean()
  data['BTC_EMA'] = data['BTC-USD'].ewm(span=20, adjust=False).mean()
  data['ETH_SMA'] = data['ETH-USD'].rolling(window=20).mean()
  data['ETH_EMA'] = data['ETH-USD'].ewm(span=20, adjust=False).mean()
  data['USDT_SMA'] = data['USDT-USD'].rolling(window=20).mean()
  data['USDT_EMA'] = data['USDT-USD'].ewm(span=20, adjust=False).mean()
  data['BNB_SMA'] = data['BNB-USD'].rolling(window=20).mean()
  data['BNB_EMA'] = data['BNB-USD'].ewm(span=20, adjust=False).mean()
  data['SOL_SMA'] = data['SOL-USD'].rolling(window=20).mean()
  data['SOL_EMA'] = data['SOL-USD'].ewm(span=20, adjust=False).mean()


  data['BTC_RSI'] = compute_rsi(data['BTC-USD'], window=14)
  data['ETH_RSI'] = compute_rsi(data['ETH-USD'], window=14)
  data['USDT_RSI'] = compute_rsi(data['USDT-USD'], window=14)
  data['BNB_RSI'] = compute_rsi(data['BNB-USD'], window=14)
  data['SOL_RSI'] = compute_rsi(data['SOL-USD'], window=14)

  # Bollinger Bands
  data['BTC_BB_upper'] = data['BTC_SMA'] + 2 * data['BTC-USD'].rolling(window=20).std()
  data['BTC_BB_lower'] = data['BTC_SMA'] - 2 * data['BTC-USD'].rolling(window=20).std()
  data['ETH_BB_upper'] = data['ETH_SMA'] + 2 * data['ETH-USD'].rolling(window=20).std()
  data['ETH_BB_lower'] = data['ETH_SMA'] - 2 * data['ETH-USD'].rolling(window=20).std()
  data['USDT_BB_upper'] = data['USDT_SMA'] + 2 * data['USDT-USD'].rolling(window=20).std()
  data['USDT_BB_lower'] = data['USDT_SMA'] - 2 * data['USDT-USD'].rolling(window=20).std()
  data['BNB_BB_upper'] = data['BNB_SMA'] + 2 * data['BNB-USD'].rolling(window=20).std()
  data['BNB_BB_lower'] = data['BNB_SMA'] - 2 * data['BNB-USD'].rolling(window=20).std()
  data['SOL_BB_upper'] = data['SOL_SMA'] + 2 * data['SOL-USD'].rolling(window=20).std()
  data['SOL_BB_lower'] = data['SOL_SMA'] - 2 * data['SOL-USD'].rolling(window=20).std()

  # Moving Average Convergence Divergence (MACD)
  data['BTC_MACD'] = data['BTC-USD'].ewm(span=12, adjust=False).mean() - data['BTC-USD'].ewm(span=26, adjust=False).mean()
  data['BTC_MACD_signal'] = data['BTC_MACD'].ewm(span=9, adjust=False).mean()
  data['ETH_MACD'] = data['ETH-USD'].ewm(span=12, adjust=False).mean() - data['ETH-USD'].ewm(span=26, adjust=False).mean()
  data['ETH_MACD_signal'] = data['ETH_MACD'].ewm(span=9, adjust=False).mean()
  data['USDT_MACD'] = data['USDT-USD'].ewm(span=12, adjust=False).mean() - data['USDT-USD'].ewm(span=26, adjust=False).mean()
  data['USDT_MACD_signal'] = data['USDT_MACD'].ewm(span=9, adjust=False).mean()
  data['BNB_MACD'] = data['BNB-USD'].ewm(span=12, adjust=False).mean() - data['BNB-USD'].ewm(span=26, adjust=False).mean()
  data['BNB_MACD_signal'] = data['BNB_MACD'].ewm(span=9, adjust=False).mean()
  data['SOL_MACD'] = data['SOL-USD'].ewm(span=12, adjust=False).mean() - data['SOL-USD'].ewm(span=26, adjust=False).mean()
  data['SOL_MACD_signal'] = data['SOL_MACD'].ewm(span=9, adjust=False).mean()

  # Stochastic Oscillator
  data['BTC_L14'] = data['BTC-USD'].rolling(window=14).min()
  data['BTC_H14'] = data['BTC-USD'].rolling(window=14).max()
  data['BTC_%K'] = 100 * (data['BTC-USD'] - data['BTC_L14']) / (data['BTC_H14'] - data['BTC_L14'])
  data['BTC_%D'] = data['BTC_%K'].rolling(window=3).mean()

  data['ETH_L14'] = data['ETH-USD'].rolling(window=14).min()
  data['ETH_H14'] = data['ETH-USD'].rolling(window=14).max()
  data['ETH_%K'] = 100 * (data['ETH-USD'] - data['ETH_L14']) / (data['ETH_H14'] - data['ETH_L14'])
  data['ETH_%D'] = data['ETH_%K'].rolling(window=3).mean()

  data['USDT_L14'] = data['USDT-USD'].rolling(window=14).min()
  data['USDT_H14'] = data['USDT-USD'].rolling(window=14).max()
  data['USDT_%K'] = 100 * (data['USDT-USD'] - data['USDT_L14']) / (data['USDT_H14'] - data['USDT_L14'])
  data['USDT_%D'] = data['USDT_%K'].rolling(window=3).mean()

  data['BNB_L14'] = data['BNB-USD'].rolling(window=14).min()
  data['BNB_H14'] = data['BNB-USD'].rolling(window=14).max()
  data['BNB_%K'] = 100 * (data['BNB-USD'] - data['BNB_L14']) / (data['BNB_H14'] - data['BNB_L14'])
  data['BNB_%D'] = data['BNB_%K'].rolling(window=3).mean()

  data['SOL_L14'] = data['SOL-USD'].rolling(window=14).min()
  data['SOL_H14'] = data['SOL-USD'].rolling(window=14).max()
  data['SOL_%K'] = 100 * (data['SOL-USD'] - data['SOL_L14']) / (data['SOL_H14'] - data['SOL_L14'])
  data['SOL_%D'] = data['SOL_%K'].rolling(window=3).mean()

  # Drop rows with NaN values created by rolling calculations
  data = data.dropna()

  # Define features and target variable
  features = ['BTC_SMA', 'BTC_EMA', 'BTC_RSI', 'BTC_BB_upper', 'BTC_BB_lower', 'BTC_MACD', 'BTC_MACD_signal', 'BTC_%K', 'BTC_%D',
              'ETH_SMA', 'ETH_EMA', 'ETH_RSI', 'ETH_BB_upper', 'ETH_BB_lower', 'ETH_MACD', 'ETH_MACD_signal', 'ETH_%K', 'ETH_%D',
              'USDT_SMA', 'USDT_EMA', 'USDT_RSI', 'USDT_BB_upper', 'USDT_BB_lower', 'USDT_MACD', 'USDT_MACD_signal', 'USDT_%K', 'USDT_%D',
              'BNB_SMA', 'BNB_EMA', 'BNB_RSI', 'BNB_BB_upper', 'BNB_BB_lower', 'BNB_MACD', 'BNB_MACD_signal', 'BNB_%K', 'BNB_%D',
              'SOL_SMA', 'SOL_EMA', 'SOL_RSI', 'SOL_BB_upper', 'SOL_BB_lower', 'SOL_MACD', 'SOL_MACD_signal', 'SOL_%K', 'SOL_%D']

  # target = 'BTC-USD'

  X = data[features]
  y = data[target]

  # Split the data into training and test sets with 50 rows for the test set
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=50, shuffle=False)

  # Train a simple model
  model = LinearRegression()
  model.fit(X_train, y_train)

  # Make predictions
  y_pred = model.predict(X_test)

  # Evaluate the model
  rmse = mean_squared_error(y_test, y_pred, squared=False)
  mae = mean_absolute_error(y_test, y_pred)
  mse = mean_squared_error(y_test, y_pred)
  r2 = r2_score(y_test, y_pred)

  print(f'RMSE: {rmse}')
  print(f'MAE: {mae}')
  print(f'MSE: {mse}')
  print(f'R-squared: {r2}')

  return y_pred, y_test

def forcast_LR(y_pred, y_test):
  # Create a DataFrame to hold the actual and predicted values
  results = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred}, index=y_test.index)

  # Plot the actual and predicted values
  plt.plot(results.index, results['Actual'], label='Actual')
  plt.plot(results.index, results['Predicted'], label='Predicted')
  plt.legend()
  plt.title('Actual vs Predicted Stock Prices(LR)')
  plt.xlabel('Date')
  plt.ylabel('Stock Price')
  # plt.show()

  # Save the plot as a PNG image in memory
  img = io.BytesIO()
  plt.savefig(img, format='png')
  img.seek(0)  # Rewind the file pointer to the beginning of the file

  # Encode the image as base64 to send to frontend
  img_base64 = base64.b64encode(img.read()).decode('utf-8')
  plt.close()

  return img_base64


def prepare_dataframe_for_lstm(df, n_steps):
    df = dc(df)

    for i in range(1, n_steps+1):
        df[f'Close(t-{i})'] = df['Close'].shift(i)

    df.dropna(inplace=True)

    return df


class TimeSeriesDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):
        return self.X[i], self.y[i]


def feature_preprocessing(shifted_df, forcast_size, batch_size):
  shifted_df_as_np = shifted_df.to_numpy()
  scaler = MinMaxScaler(feature_range=(-1, 1))
  shifted_df_as_np = scaler.fit_transform(shifted_df_as_np)

  X = shifted_df_as_np[:, 1:]
  y = shifted_df_as_np[:, 0]
  X = dc(np.flip(X, axis=1))

  split_index = int(len(X) - (forcast_size+1))

  X_train = X[:split_index]
  X_test = X[split_index:]
  y_train = y[:split_index]
  y_test = y[split_index:]

  X_train = X_train.reshape((-1, lookback, 1))
  X_test = X_test.reshape((-1, lookback, 1))
  y_train = y_train.reshape((-1, 1))
  y_test = y_test.reshape((-1, 1))

  X_train = torch.tensor(X_train).float()
  y_train = torch.tensor(y_train).float()
  X_test = torch.tensor(X_test).float()
  y_test = torch.tensor(y_test).float()

  return scaler, X_train, X_test, y_train, y_test


class LSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_stacked_layers):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_stacked_layers = num_stacked_layers

        self.lstm = nn.LSTM(input_size, hidden_size, num_stacked_layers,
                            batch_first=True)

        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        batch_size = x.size(0)
        h0 = torch.zeros(self.num_stacked_layers, batch_size, self.hidden_size).to(device)
        c0 = torch.zeros(self.num_stacked_layers, batch_size, self.hidden_size).to(device)

        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out


def train_one_epoch(model, epoch, loss_function, train_loader, optimizer):
    model.train(True)
    print(f'Epoch: {epoch + 1}')
    running_loss = 0.0

    for batch_index, batch in enumerate(train_loader):
        x_batch, y_batch = batch[0].to(device), batch[1].to(device)

        output = model(x_batch)
        loss = loss_function(output, y_batch)
        running_loss += loss.item()

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if batch_index % 100 == 99:  # print every 100 batches
            avg_loss_across_batches = running_loss / 100
            print('Batch {0}, Loss: {1:.3f}'.format(batch_index+1,
                                                    avg_loss_across_batches))
            running_loss = 0.0
    print()


def validate_one_epoch(model, loss_function, test_loader):
    model.train(False)
    running_loss = 0.0

    for batch_index, batch in enumerate(test_loader):
        x_batch, y_batch = batch[0].to(device), batch[1].to(device)

        with torch.no_grad():
            output = model(x_batch)
            loss = loss_function(output, y_batch)
            running_loss += loss.item()

    avg_loss_across_batches = running_loss / len(test_loader)

    print('Val Loss: {0:.3f}'.format(avg_loss_across_batches))
    print('***************************************************')
    print()


def build_model_LSTM(X_train, X_test, y_train,y_test, learning_rate, num_epochs, scaler):
  train_dataset = TimeSeriesDataset(X_train, y_train)
  test_dataset = TimeSeriesDataset(X_test, y_test)

  train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
  test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
  for _, batch in enumerate(train_loader):
      x_batch, y_batch = batch[0].to(device), batch[1].to(device)
      print(x_batch.shape, y_batch.shape)
      break

  model = LSTM(1, hidden_size, num_stacked_layers)
  model.to(device)

  loss_function = nn.MSELoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

  for epoch in range(num_epochs):
      train_one_epoch(model, epoch, loss_function, train_loader, optimizer)
      validate_one_epoch(model, loss_function, test_loader)

  with torch.no_grad():
    predicted = model(X_train.to(device)).to('cpu').numpy()

  train_predictions = predicted.flatten()

  dummies = np.zeros((X_train.shape[0], lookback+1))
  dummies[:, 0] = train_predictions
  dummies = scaler.inverse_transform(dummies)
  train_predictions = dc(dummies[:, 0])

  dummies = np.zeros((X_train.shape[0], lookback+1))
  dummies[:, 0] = y_train.flatten()
  dummies = scaler.inverse_transform(dummies)
  new_y_train = dc(dummies[:, 0])

  test_predictions = model(X_test.to(device)).detach().cpu().numpy().flatten()

  dummies = np.zeros((X_test.shape[0], lookback+1))
  dummies[:, 0] = test_predictions
  dummies = scaler.inverse_transform(dummies)
  test_predictions = dc(dummies[1:, 0])

  dummies = np.zeros((X_test.shape[0], lookback+1))
  dummies[:, 0] = y_test.flatten()
  dummies = scaler.inverse_transform(dummies)
  new_y_test = dc(dummies[:-1, 0])

  return test_predictions, new_y_test


def forcast_LSTM(test_predictions, new_y_test):
  # LSTM prediction
  plt.plot(new_y_test, label='Actual Close')
  plt.plot(test_predictions, label='Predicted Close')
  plt.xlabel('Day')
  plt.ylabel('Close')
  plt.title('Actual vs Predicted Stock Prices(LSTM)')
  plt.legend()
  plt.show()


def final_forcast(y_pred, y_test, test_predictions):
  results = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred}, index=y_test.index)
  for i in range(0,len(test_predictions)):
    results['Predicted'][i] = (results['Predicted'][i]*60 + test_predictions[i]*40)/100

  plt.plot(results.index, results['Actual'], label='Actual')
  plt.plot(results.index, results['Predicted'], label='Predicted')
  plt.legend()
  plt.title('Actual vs Predicted Stock Prices(Final)')
  plt.xlabel('Date')
  plt.ylabel('Stock Price')
  # plt.show()

  # Save the plot as a PNG image in memory
  img = io.BytesIO()
  plt.savefig(img, format='png')
  img.seek(0)  # Rewind the file pointer to the beginning of the file

  # Encode the image as base64 to send to frontend
  img_base64 = base64.b64encode(img.read()).decode('utf-8')
  plt.close()

  return img_base64


def predict_LSTM(data, forcast_size, start_date, end_date, lookback, batch_size, hidden_size, num_stacked_layers, learning_rate, num_epochs):
  shifted_df = prepare_dataframe_for_lstm(data, lookback)
  scaler, X_train, X_test, y_train, y_test = feature_preprocessing(shifted_df, forcast_size, batch_size)
  test_predictions, new_y_test = build_model_LSTM(X_train, X_test, y_train, y_test, learning_rate, num_epochs, scaler)

  return test_predictions, new_y_test


def final_forcast(y_pred, y_test, test_predictions):
  results = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred}, index=y_test.index)
  for i in range(0,len(test_predictions)):
    results['Predicted'][i-1] = (results['Predicted'][i]*30 + test_predictions[i]*70)/100

  plt.plot(results.index, results['Actual'], label='Actual')
  plt.plot(results.index, results['Predicted'], label='Predicted')
  plt.legend()
  plt.title('Actual vs Predicted Stock Prices(Final)')
  plt.xlabel('Date')
  plt.ylabel('Stock Price')
  # plt.show()

  # Save the plot as a PNG image in memory
  img = io.BytesIO()
  plt.savefig(img, format='png')
  img.seek(0)  # Rewind the file pointer to the beginning of the file

  # Encode the image as base64 to send to frontend
  img_base64 = base64.b64encode(img.read()).decode('utf-8')
  plt.close()

  return img_base64

def forcaster1(ticker, end_date, forcast_size, tdata=data, lookback=lookback, batch_size=batch_size, hidden_size=hidden_size, num_stacked_layers=num_stacked_layers, learning_rate=learning_rate, num_epochs=num_epochs, start_date=start_date, competitors=tickers, target=target):

  dataM = yf.download(ticker, start=start_date, end=end_date)

  data = dataM.copy()
  y_pred, y_test = build_model_LR(tdata, forcast_size, start_date, end_date, ticker)

  data = dataM.copy()
  data = data[['Close']]
  test_predictions, new_y_test = predict_LSTM(data, forcast_size, start_date, end_date, lookback, batch_size, hidden_size, num_stacked_layers, learning_rate, num_epochs)

  img1 = forcast_LR(y_pred, y_test)
  img2 = forcast_LSTM(test_predictions, new_y_test)
  img3 = final_forcast(y_pred, y_test, test_predictions)

  return img1, img2, img3



# y_pred, y_test, test_predictions, new_y_test = forcaster('BTC-USD', '2025-01-01', 50)

# forcast_LR(y_pred, y_test)
# forcast_LSTM(test_predictions, new_y_test)
# final_forcast(y_pred, y_test, test_predictions)