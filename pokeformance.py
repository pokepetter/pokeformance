import ast
import re
import sys
import traceback
from pathlib import Path
from textwrap import dedent
import subprocess


def measure_performance(file, min_limit=.01, rounding=4, skip_fast_lines=False, show_line_numbers=True, sort_by_time=False, max_width=999, skip_lines_containing='', imports_only=False, suppress_print=True):
    print('profiling script:', file)
    if isinstance(file, str):
        file = Path(file)

    with file.open('r') as f:
        lines = f.readlines()
        if imports_only:
            lines = [l.lstrip() for l in lines if l.lstrip().startswith('import ') or l.lstrip().startswith('from ')]
            print('lines:', lines)
    # add timing code
    num_lines = len(lines)
    code = f'from time import perf_counter; '
    code += f'num_lines={num_lines}; '
    code += f'durations = [0 for i in range(num_lines+1)]; '
    code += f'num_times_run = [0 for i in range(num_lines+1)]; '
    code += f'min_limit = {min_limit}; '
    code += f'rounding = {rounding}; '
    code += f'skip_fast_lines = {skip_fast_lines}; '
    code += f'show_line_numbers = {show_line_numbers}; '
    code += f'sort_by_time = {sort_by_time}; '
    code += f'max_width = {max_width}; '
    code += f'skip_lines_containing = "{skip_lines_containing}"; '
    code += f'original_print = print; '

    if suppress_print:
        code += dedent('''\

            import builtins
            def _eat_print(*args, **kwargs):
                return
            builtins.print = _eat_print
            ''')

    single_line_statement = None
    prev_line_continues = None

    previous_line_valid = False

    for i, line in enumerate(lines):
        if skip_lines_containing and skip_lines_containing in line:
            continue

        line = remove_comments_from_line(line)
        current_line_valid = is_valid_single_line_statement(line)
        new_line = ''
        prev_line = ''
        if i > 0:
            prev_line = lines[i-1]

        # add timing code before and after line
        if (previous_line_valid or prev_line == '\n') and current_line_valid:   # consecutive valid lines
            indentation = len(line) - len(line.lstrip())
            new_line = f'{" "*indentation}__t=perf_counter(); {line.strip()}; dur=perf_counter()-__t; durations[{i}]+=dur; num_times_run[{i}]+=1;'
        elif current_line_valid:
            new_line = line.rstrip()    # valid line
        else:
            new_line = line.rstrip()    # invalid line

        previous_line_valid = current_line_valid

        code += new_line + '\n'

    code += "\n\n# print results\n"
    code += f"lines={lines}\n\n"

    code += "results = [[i, durations[i], num_times_run[i], lines[i]] for i in range(num_lines)]\n"
    code += "if sort_by_time: results.sort(key=lambda x: x[1])\n"

    code += "for res in results:\n"
    code += "    i, duration, n, text = res\n"
    code += "    if skip_fast_lines and duration < min_limit: continue\n"
    code += "    duration_text = f'{round(duration,rounding)}' if duration >= min_limit else ''\n"
    code += "    num_times_run_text = n if n > 0 else ''\n"
    code += "    line_number = i if show_line_numbers else ''\n"
    code += "    original_print(f'{duration_text:<7}|{num_times_run_text:>3} |{line_number:>4}|{text.rstrip()[:max_width]}')\n"

    code += "total_time = sum([line[1] for line in results])\n"
    code += "original_print('total time:', total_time)\n"

    path = Path(file.parent / f'{file.stem}_pokeformance_profiling_temp.py')
    with path.open('w') as f:
        f.write(code)
    subprocess.Popen([sys.executable, path])
    # path.unlink()
    # subprocess.Popen(['python', '-c', code])




def is_valid_single_line_statement(line):
    if len(line.strip()) == 0:
        return False

    if line.strip().endswith(','):
        return False

    for invalid_start in ('+', '-', '*', '/', 'if ', 'elif ', 'else:', 'for '):
        if line.strip().startswith(invalid_start):
            return False

    if line.strip().startswith('self.'):
        line = line.strip()[len('self.'):]

    try:
        line = line.lstrip()
        ast.parse(line)
        return True
    except SyntaxError:
        return False


def remove_comments_from_line(line):
    # Use regular expression to remove comments but not within strings
    line_without_comments = re.sub(r'(#.*)|(\'[^\']*\'|\"[^\"]*\")', lambda match: match.group(2) or '', line)
    return line_without_comments


def convert_argv(prefix='--'):
    kwargs = {}
    for arg in sys.argv:
        if '=' in arg:
            name, value = arg.split('=')
            if value == 'True':
                value = True
            elif value == 'False':
                value = False
            elif value.startswith('\''):
                value = f'"{value}"'
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass

            print('set arg:', name, value)
            kwargs[name.lstrip(prefix)] = value

    return kwargs

def main():
    if len(sys.argv) > 1:
        if '--help' in sys.argv:
            import inspect
            signature = inspect.signature(measure_performance)
            defaults = {param.name: param.default for param in signature.parameters.values() if param.default is not inspect.Parameter.empty}
            help_text = ' '.join([f'{key}={value}' for key, value in defaults.items()])
            help_text = ''
            for key, value in defaults.items():
                if isinstance(value, str):
                    value = f'\'{value}\''
                help_text += f'{key}={value} '


            print(help_text)
            return

        target_file = Path.cwd() / sys.argv[1]
        kwargs = convert_argv()
        result = measure_performance(target_file, **kwargs)


if __name__ == '__main__':
    main()
