import torch
from torch import nn


class TradingModel(nn.Module):
    def __init__(self, input_features=7):
        super().__init__()
        self.input_layer = nn.Linear(input_features, 128)
        self.lstm1 = nn.LSTM(128, 128, batch_first=True)
        self.lstm2 = nn.LSTM(128, 128, batch_first=True)
        self.hidden_layer = nn.Linear(128, 128)
        self.return_head = nn.Linear(128, 1)

    def forward(self, windows):
        """Predict one signed return per window."""
        sequence = torch.relu(self.input_layer(windows))
        sequence, _ = self.lstm1(sequence)
        sequence, _ = self.lstm2(sequence)
        last_session = sequence[:, -1, :]
        hidden = torch.relu(self.hidden_layer(last_session))
        return self.return_head(hidden).squeeze(-1)


def trading_action(predicted_return, is_invested):
    """Turn one return forecast and the current position into a trading action."""
    if predicted_return > 0 and not is_invested:
        return "Buy"
    if predicted_return < 0 and is_invested:
        return "Sell"
    return "Hold"
