# PyReparse Notes

## Add and LLM Help

  - Add and LLM Helper to get a Parsing Engine Started.

## Using Decimal instead of Floats for Money

Floats (floating-point numbers) are generally not recommended for performing money calculations due to significant drawbacks related to precision and accuracy. Here's a breakdown of the issues and better alternatives.

### Drawbacks of Using Floats for Money
Floating-point numbers, as defined by standards like IEEE 754 (used in most programming languages such as Python, JavaScript, Java, C++, etc.), represent values in binary with a fixed number of bits for the mantissa (significant digits) and exponent. This leads to inherent limitations:

1. **Rounding Errors and Inexact Representations**: Many decimal fractions cannot be represented exactly in binary. For instance:
   - 0.1 in decimal is a repeating binary fraction (similar to how 1/3 is repeating in decimal), so it's approximated.
   - A simple addition like 0.1 + 0.2 often results in something like 0.30000000000000004 instead of exactly 0.3.
   - Over multiple operations (e.g., adding taxes, discounts, or compounding interest), these tiny errors accumulate, leading to discrepancies that can be off by cents or more.

2. **Loss of Precision in Large or Small Values**: Floats have limited precision (typically about 15-16 decimal digits for double-precision floats). For monetary amounts involving large sums or very small fractions (e.g., cryptocurrency subunits), this can cause truncation or overflow issues.

3. **Unpredictable Behavior Across Operations**: Subtraction, multiplication, and division can exacerbate errors. For example, subtracting two nearly equal floats might lose significant digits due to catastrophic cancellation.

4. **Legal and Financial Risks**: In real-world applications like banking, e-commerce, or accounting, even small errors can lead to compliance issues, audits, or disputes. Regulations (e.g., GAAP or IFRS) often require exact arithmetic for financial reporting.

These problems are well-documented in programming literature, such as in "What Every Computer Scientist Should Know About Floating-Point Arithmetic" by David Goldberg.

### Best Numeric Format for Money Calculations
If floats have drawbacks, the recommended approach is to use formats that support exact decimal arithmetic or avoid fractional representations altogether. The choice depends on your programming language and requirements, but here are the top options:

1. **Decimal Types (Preferred for Precision)**:
   - Use a dedicated decimal arithmetic library or type that handles base-10 representations with controllable precision.
   - **Why it's better**: It avoids binary approximation issues and supports exact operations for decimal fractions common in currencies (e.g., two decimal places for USD).
   - **Examples by Language**:
     - **Python**: Use the `decimal` module's `Decimal` class. Set precision via `getcontext().prec` and always initialize from strings (e.g., `Decimal('0.1') + Decimal('0.2') == Decimal('0.3')`).
     - **Java**: Use `BigDecimal` from `java.math` (e.g., `new BigDecimal("0.1").add(new BigDecimal("0.2"))`).
     - **JavaScript/TypeScript**: Use libraries like `decimal.js` or `bignumber.js`.
     - **C#/.NET**: Use the `decimal` type (128-bit, up to 28-29 decimal digits).
     - **SQL Databases**: Use `DECIMAL` or `NUMERIC` types for columns storing money.
   - **When to use**: For applications needing arbitrary precision or handling multiple currencies with varying decimal places (e.g., JPY has 0 decimals, while some cryptos have 8+).

2. **Integers Representing the Smallest Unit**:
   - Store amounts as integers in the smallest currency unit (e.g., cents for USD, satoshis for Bitcoin).
   - **Why it's better**: Integers have exact arithmetic with no precision loss, and operations are fast and simple.
   - **Examples**:
     - $10.50 becomes 1050 cents (as a long or BigInteger if needed).
     - Add/subtract directly, then divide by 100 for display.
     - In Python: Use `int` (e.g., amount_in_cents = 100 + 200; total = amount_in_cents / 100).
   - **When to use**: For simpler systems where precision is fixed (e.g., always 2 decimals) and you don't need built-in rounding modes.

In summary, avoid floats for money to prevent subtle bugs—opt for decimals or integers instead. If you're implementing this in code, always include unit tests for edge cases like rounding and large sums. If you have a specific language or scenario in mind, I can provide more tailored examples.

