import ast
import re
import sys
import traceback
from pathlib import Path

# durations = []
# num_times_run = []
# durations = [0 for i in range(9999)]
# num_times_run = [0 for i in range(9999)]

def measure_performance_line_by_line(lines, min_limit=.01, rounding=4, skip_fast_lines=False, show_line_numbers=True, sort_by_time=False, max_width=None, file_path=None):
    # global durations, num_times_run
    # add timing code
    code = f'from time import perf_counter;'

    single_line_statement = None
    prev_line_continues = None

    # durations = [0 for i in range(len(lines)+1)]
    # num_times_run = [0 for i in range(len(lines)+1)]
    previous_line_valid = False

    for i, line in enumerate(lines):
        line = remove_comments_from_line(line)
        current_line_valid = is_valid_single_line_statement(line)
        new_line = ''
        prev_line = ''
        if i > 0:
            prev_line = lines[i-1]

        if (previous_line_valid or prev_line == '\n') and current_line_valid:   # consecutive valid lines
            indentation = len(line) - len(line.lstrip())
            # new_line = f'{" "*indentation}t=perf_counter(); {line.strip()}; dur=perf_counter()-t; print("{i}", "{lines[i].strip()}", dur if dur > .01 else "")'
            new_line = f'{" "*indentation}t=perf_counter(); {line.strip()}; dur=perf_counter()-t; durations[{i}]+=dur; num_times_run[{i}]+=1;'
        elif current_line_valid:
            new_line = line.rstrip()    # valid line
        else:
            new_line = line.rstrip()    # invalid line

        previous_line_valid = current_line_valid

        code += new_line + '\n'
        # code += new_line + f'# valid: {current_line_valid}\n'
    try:
        durations = [0 for i in range(len(lines)+1)]
        num_times_run = [0 for i in range(len(lines)+1)]
        vars = {
            '__name__': '__main__',
            'durations' : durations,
            'num_times_run' : num_times_run,
            }
        if file_path:
            vars['__file__'] = file_path

        # print('code------------\n', code)
        exec(code, vars)
        print('-- exec done')

    except Exception:
        print('\n'.join([f'{i:>3} {l}' for i, l in enumerate(code.split('\n'))]))
        print(traceback.format_exc())


    # get stats
    results = []
    for i, line in enumerate(code.split('\n')):
        original_line = line.replace('t=perf_counter(); ', '').split('; dur=perf_counter()-t;')[0]
        # print('oooo', original_line)
        # if not original_line:
        #     continue
        # duration_text = f"{round(durations[i],4)}" if durations[i]>.01 else ""
        # += f'{duration_text:<7}|{i}|{original_line} \n'
        results.append([original_line, i, durations[i], num_times_run[i]])
        # print(i, original_line)

    result = ''

    if sort_by_time:
        results.sort(key=lambda x: x[2])

    # render stats
    for line in results:
        code, line_number, duration, num_times_run = line
        if skip_fast_lines and duration < min_limit:
            continue

        line_number = line_number if show_line_numbers else ''

        duration_text = f"{round(duration,rounding)}" if duration >= min_limit else ""
        num_times_run_text = num_times_run if num_times_run > 0 else ''

        if max_width is not None:
            code = code[:max_width]

        result += f'{duration_text:<7}|{num_times_run_text:>3} |{line_number:>4}|{code} \n'
        # print(f'{duration_text:<7}|{i}|{original_line})
    total_time = sum([line[2] for line in results])
    result += f'total time: {total_time}'

    return result



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


def detect_consecutive_single_line_statements(lines):
    previous_line_valid = False

    for line in lines:
        current_line_valid = is_valid_single_line_statement(line)

        if previous_line_valid and current_line_valid:
            print(f"Consecutive valid lines: {line}")
        elif current_line_valid:
            print(f"Valid line: {line}")
        else:
            print(f"Invalid line: {line}")

        previous_line_valid = current_line_valid


def remove_comments_from_line(line):
    # Use regular expression to remove comments but not within strings
    line_without_comments = re.sub(r'(#.*)|(\'[^\']*\'|\"[^\"]*\")', lambda match: match.group(2) or '', line)
    return line_without_comments



def convert_argv(prefix='--'):
    kwargs = {}
    for arg in sys.argv:
        if '=' in arg:
            name, value = arg.split('=')
            print('ggggggggggggg', name, value)
            if value == 'True':
                value = True
            if value == 'False':
                value = False
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


if __name__ == '__main__':

    if len(sys.argv) > 1:
        target_file = Path.cwd() / sys.argv[1]
        print('profiling script:', target_file)
        kwargs = convert_argv()

        with open(target_file, 'r') as f:
            lines = f.readlines()[:-1]

            print('input args:', 'file_path=', target_file, kwargs.items())
            result = measure_performance_line_by_line(lines, file_path=target_file, **kwargs)
            print(result)

    else:
        from textwrap import dedent
        test_code = dedent('''
            a = 5
            b = [i*i for i in range(1000)]
            '''[1:]).split('\n')
        # print(test_code)

        print(measure_performance_line_by_line(test_code, min_limit=0))
