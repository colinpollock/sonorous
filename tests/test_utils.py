import math
from unittest import mock

import pandas as pd
import pytest
import torch
from torch.nn.modules import rnn

from sonorant.utils import (
    count_origins,
    get_rnn_model_by_name,
    get_torch_device_by_name,
    has_decreased,
    split_data,
    truncate,
)


def test_split_data():
    df = pd.DataFrame({"data": list(range(1, 101))})
    train_df, dev_df, test_df = split_data(
        df, dev_proportion=0.2, test_proportion=0.1, random_state=47
    )

    # Because of float imprecision .3 can end up as .3000001, which sklearn appears to round up. I
    # could handle the rounding myself in `split_data`, but this doesn't matter as long as it's
    # roughly right.
    assert len(train_df) in (69, 70, 71)
    assert len(dev_df) in (19, 20, 21)
    assert len(test_df) in (9, 10, 11)

    # There should be no items occurring in more than one set.
    length_of_all_unique = len(
        set(train_df.data) | set(dev_df.data) | set(test_df.data)
    )
    lengths_of_each = len(train_df.data) + len(dev_df.data) + len(test_df.data)
    assert length_of_all_unique == lengths_of_each


def test_has_decreased():
    def check(scores, in_last, expected):
        assert has_decreased(scores, in_last) == expected

    check([2, 1], 1, True)
    check([2, 1], 2, True)
    check([1, 2], 2, True)
    check([1, 2], 1, False)
    check([], 1, True)
    check([1, 2, 1, 4], 3, True)


def test_count_origins():
    one = list("one")
    two = list("two")
    three = list("three")
    four = list("four")

    generated = [one, two, three, four]
    train = [one, two]
    dev = [three]

    train_proportion, dev_proportion, novel_proportion = count_origins(
        generated, train, dev
    )
    assert train_proportion == 50
    assert dev_proportion == 25
    assert novel_proportion == 25


def test_get_rnn_model_by_name():
    assert get_rnn_model_by_name("rnn") == rnn.RNN
    assert get_rnn_model_by_name("lstm") == rnn.LSTM
    assert get_rnn_model_by_name("gru") == rnn.GRU

    with pytest.raises(ValueError):
        get_rnn_model_by_name("frank zappa")


def test_get_torch_device_by_name():
    cpu = torch.device("cpu")
    cuda = torch.device("cuda")

    with mock.patch("sonorant.utils.torch.cuda.is_available", lambda: True):
        assert get_torch_device_by_name("cpu") == cpu
        assert get_torch_device_by_name("cuda") == cuda

        assert get_torch_device_by_name() == cuda

    with mock.patch("sonorant.utils.torch.cuda.is_available", lambda: False):
        assert get_torch_device_by_name("cpu") == cpu

        with pytest.raises(ValueError):
            get_torch_device_by_name("cuda")

        assert get_torch_device_by_name() == cpu

    with pytest.raises(RuntimeError):
        get_torch_device_by_name("lol what?")


def test_truncate():
    assert truncate(98.6, 0) == 98.0
    assert truncate(1.234567, 3) == 1.234
