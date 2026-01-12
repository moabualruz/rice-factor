"""Tests for calculator module."""

import pytest
from src.calculator import add, subtract, multiply, divide


class TestAdd:
    """Tests for add function."""

    def test_add_positive_numbers(self):
        assert add(2, 3) == 5

    def test_add_negative_numbers(self):
        assert add(-2, -3) == -5

    def test_add_mixed_numbers(self):
        assert add(-2, 3) == 1

    def test_add_floats(self):
        assert add(2.5, 3.5) == 6.0


class TestSubtract:
    """Tests for subtract function."""

    def test_subtract_positive_numbers(self):
        assert subtract(5, 3) == 2

    def test_subtract_negative_result(self):
        assert subtract(3, 5) == -2


class TestMultiply:
    """Tests for multiply function."""

    def test_multiply_positive_numbers(self):
        assert multiply(2, 3) == 6

    def test_multiply_by_zero(self):
        assert multiply(5, 0) == 0


class TestDivide:
    """Tests for divide function."""

    def test_divide_positive_numbers(self):
        assert divide(6, 2) == 3

    def test_divide_by_zero_raises(self):
        with pytest.raises(ZeroDivisionError):
            divide(5, 0)

    def test_divide_floats(self):
        assert divide(7.5, 2.5) == 3.0
