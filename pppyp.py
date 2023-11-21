import ast
import re
import sys

MIN_LIMIT = .01
ROUNDING = 4
SKIP_FAST_LINES = True
SORT_BY_TIME = True
SHOW_LINE_NUMBERS = True
MAX_WIDTH = 80

if len(sys.argv) > 1:
    target_file = sys.argv[1]
    with open(target_file, 'r') as f:
        lines = f.readlines()[:-1]

        result = measure_performance_line_by_line(lines)
        print(result)


def measure_performance_line_by_line(lines):
    # add timing code
    code = 'from time import perf_counter;'

    single_line_statement = None
    prev_line_continues = None

    previous_line_valid = False
    durations = [0 for i in range(len(lines)+1)]
    num_times_run = [0 for i in range(len(lines)+1)]

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

    exec(code)


    # get stats
    resulting_lines = []
    for i, line in enumerate(code.split('\n')):
        original_line = line.replace('t=perf_counter(); ', '').split('; dur=perf_counter()-t;')[0]
        # duration_text = f"{round(durations[i],4)}" if durations[i]>.01 else ""
        # += f'{duration_text:<7}|{i}|{original_line} \n'
        resulting_lines.append([original_line, i, durations[i], num_times_run[i]])
        # print(i, original_line)

    result = ''

    if SORT_BY_TIME:
        resulting_lines.sort(key=lambda x: x[2])

    # render stats
    for line in resulting_lines:
        code, line_number, duration, num_times_run = line
        if SKIP_FAST_LINES and duration < MIN_LIMIT:
            continue

        line_number = line_number if SHOW_LINE_NUMBERS else ''

        duration_text = f"{round(duration,ROUNDING)}" if duration > MIN_LIMIT else ""
        num_times_run_text = num_times_run if num_times_run > 0 else ''

        if MAX_WIDTH is not None:
            code = code[:MAX_WIDTH]

        result += f'{duration_text:<7}|{num_times_run_text:>3} |{line_number:>4}|{code} \n'
        # print(f'{duration_text:<7}|{i}|{original_line})
    total_time = sum([line[2] for line in resulting_lines])
    result += f'total time: {total_time}'

    return



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
