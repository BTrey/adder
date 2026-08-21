# Adder

Adder is a calculator and a notepad in one terminal window. You type lines. Each
line joins a growing List in the left column. A line that starts with an
operator also changes a single Value, and the new Value prints in the right
column on the same row. A line with no operator is only text.

```
┌ List ───────────────────┐┌ Value ──────┐
│ hello                   ││             │
│ + 100                   ││         100 │
│ * 3                     ││         300 │
└◀━━━━━━━━━━━━━━━━━━━━━━▶─┘└─────────────┘
┌─────────────────────────────────────────┐
│ + 5                                     │
└─────────────────────────────────────────┘
```

## Install

```
uv tool install git+https://github.com/BTrey/adder.git
```

This puts an `adder` command on your path. To run Adder once without an
install, use `uvx --from git+https://github.com/BTrey/adder.git adder`. To
remove it, use `uv tool uninstall adder`.

## Run

```
adder [-w N] [-c [PATH]]
```

| Flag | What it does |
| --- | --- |
| `-w N`, `--width N` | Width of the List column, in percent of the screen. The range is 0 to 100. The default is 75. |
| `-c PATH`, `--config PATH` | Read the colors from PATH. |
| `-c`, `--config` | Print the default config file and exit. |

Type a line and press Enter. Press Ctrl+Q to quit.

A width of 0 hides the List column. A width of 100 hides the Value column.

## Operators

The first character of a line selects the operator. The space after it is
optional, so `+100` and `+ 100` do the same thing.

| Line | What it does |
| --- | --- |
| `+ 100` | Add 100 to the Value. |
| `- 100` | Subtract 100 from the Value. |
| `* 3` | Multiply the Value by 3. |
| `/ 3` | Divide the Value by 3. |
| `^ 2` | Raise the Value to the power of 2. |
| `$rate = 0.07` | Set the variable `rate` to 0.07. The `=` is optional. |
| `@clear` | Empty the List and reset the Value to 0. |
| `hello` | Add a text row. The Value does not change. |

An operand is a number or a variable. `+ $rate` adds the value of `rate`. An
assignment does not change the Value, so the right column stays blank on that
row.

A line that cannot be evaluated becomes an error row. The row shows the line and
the reason, and the Value does not change. `/ 0` is an example.

## Colors

Adder reads its colors from an INI file. To get a copy of the defaults:

```
adder -c > ~/.config/adder/adder.conf
```

With no `-c` flag, Adder reads `$XDG_CONFIG_HOME/adder/adder.conf`, or
`~/.config/adder/adder.conf` if `XDG_CONFIG_HOME` is not set. Adder uses the
built-in colors if that file is not there.

A value is any color Textual accepts, such as `#268bd2` or `red`. A key that is
missing keeps its default, so a partial file is valid. A key that Adder does not
know is ignored. A file that Adder cannot read, or a color that Adder cannot
parse, stops the program with status 2.

| Section | Key | What it colors |
| --- | --- | --- |
| `colors` | `background` | The window. |
| `colors` | `border` | The panel borders. |
| `colors` | `text` | A row with no operator. |
| `colors` | `value` | The right column. |
| `colors` | `input` | The entry field. |
| `operators` | `arithmetic` | The `+ - * /` rows. |
| `operators` | `exponent` | The `^` rows. |
| `operators` | `variable` | The `$` rows. |
| `operators` | `command` | The `@` rows. |
| `operators` | `error` | A row that failed. |

The defaults are solarized dark.

## Develop

```
git clone https://github.com/BTrey/adder.git
cd adder
uv sync
uv run adder -w 40
```

`uv sync` installs the project into `.venv`, so `uv run adder` runs your working
copy. `uv run python -m adder` does the same thing.

| File | What it holds |
| --- | --- |
| `src/adder/main.py` | The entry point. |
| `src/adder/__main__.py` | Support for `python -m adder`. |
| `src/adder/cli.py` | The command line. |
| `src/adder/config.py` | The palette and its INI file. |
| `src/adder/model.py` | The rows, the List, the Value, and the variables. |
| `src/adder/operators.py` | The operator registry. |
| `src/adder/commands.py` | The command registry. |
| `src/adder/evaluator.py` | Line parsing and dispatch. |
| `src/adder/formatting.py` | The two column renderables. |
| `src/adder/app.py` | The Textual app. |

To add an operator, add one class to `src/adder/operators.py`:

```python
@register("%")
class Percent(ArithmeticOperator):
    """Take a percent of the Value."""

    name = "percent"

    def apply(self, value: float, operand: float) -> float:
        return value * operand / 100
```

To add a command, add one class to `src/adder/commands.py` with the `@register`
decorator and an `execute` method. A command that returns `None` adds no row.

Raise `EvaluationError` for anything the user can get wrong. The evaluator turns
it into an error row, so no typed line can stop the program.

Checks:

```
uv run pytest --cov=adder --cov-report=term-missing
uv run mypy --strict .
uv run pylint src
```
