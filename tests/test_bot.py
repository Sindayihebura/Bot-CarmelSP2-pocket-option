import bot


def test_supported_symbols_are_unique_and_nonempty():
    assert bot.SYMBOLS
    assert len(set(bot.SYMBOLS.values())) == len(bot.SYMBOLS)
    assert {"BTC", "ETH", "BNB"}.issubset(bot.SYMBOLS)


def test_ema_returns_one_value_per_input():
    values = [1.0, 2.0, 3.0, 4.0]
    result = bot.ema(values, 3)
    assert len(result) == len(values)
    assert all(isinstance(value, float) for value in result)
    assert result[-1] > result[0]


def test_rsi_is_bounded_for_rising_series():
    result = bot.rsi([float(i) for i in range(1, 40)])
    assert result is not None
    assert 0 <= result <= 100


def test_rsi_is_bounded_for_falling_series():
    result = bot.rsi([float(40 - i) for i in range(40)])
    assert result is not None
    assert 0 <= result <= 100
