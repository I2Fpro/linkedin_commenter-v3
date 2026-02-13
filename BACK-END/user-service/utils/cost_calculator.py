"""
OpenAI cost calculation utilities for GPT-4o-mini.
"""
import os
from decimal import Decimal, ROUND_HALF_UP

# GPT-4o-mini pricing (USD per 1M tokens)
GPT4O_MINI_INPUT_PRICE = Decimal("0.15")
GPT4O_MINI_OUTPUT_PRICE = Decimal("0.60")
ONE_MILLION = Decimal("1000000")


def calculate_openai_cost(tokens_input: int, tokens_output: int, model: str = "gpt-4o-mini") -> Decimal:
    """
    Calculate the cost in USD for an OpenAI API call.

    Args:
        tokens_input: Number of input tokens
        tokens_output: Number of output tokens
        model: Model name (only "gpt-4o-mini" supported)

    Returns:
        Cost in USD with 6 decimal precision

    Raises:
        ValueError: If model is not "gpt-4o-mini"
    """
    if model != "gpt-4o-mini":
        raise ValueError(f"Model '{model}' not supported. Only 'gpt-4o-mini' is supported.")

    # Convert ints to Decimal via string to avoid floating point issues
    input_tokens_dec = Decimal(str(tokens_input))
    output_tokens_dec = Decimal(str(tokens_output))

    # Calculate cost: (input/1M * price_input) + (output/1M * price_output)
    input_cost = (input_tokens_dec / ONE_MILLION) * GPT4O_MINI_INPUT_PRICE
    output_cost = (output_tokens_dec / ONE_MILLION) * GPT4O_MINI_OUTPUT_PRICE
    total_cost = input_cost + output_cost

    # Return with 6 decimals USD
    return total_cost.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def convert_usd_to_eur(usd_amount: Decimal, eur_rate: Decimal = None) -> Decimal:
    """
    Convert USD amount to EUR.

    Args:
        usd_amount: Amount in USD
        eur_rate: EUR conversion rate (if None, read from OPENAI_EUR_RATE env var, default 0.92)

    Returns:
        Amount in EUR with 2 decimal precision
    """
    if eur_rate is None:
        eur_rate_str = os.getenv("OPENAI_EUR_RATE", "0.92")
        eur_rate = Decimal(eur_rate_str)

    # Convert USD to EUR
    eur_amount = usd_amount * eur_rate

    # Return with 2 decimals EUR
    return eur_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_cost_eur(tokens_input: int, tokens_output: int, model: str = "gpt-4o-mini") -> str:
    """
    Calculate the cost in EUR for an OpenAI API call.

    Args:
        tokens_input: Number of input tokens
        tokens_output: Number of output tokens
        model: Model name (only "gpt-4o-mini" supported)

    Returns:
        Cost in EUR as string (e.g., "12.45")
    """
    usd_cost = calculate_openai_cost(tokens_input, tokens_output, model)
    eur_cost = convert_usd_to_eur(usd_cost)
    return str(eur_cost)
