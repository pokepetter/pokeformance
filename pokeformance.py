import sys
import ast
import astor
from time import perf_counter
from textwrap import dedent
from inspect import getframeinfo, stack
from pathlib import Path


class TimingTransformer(ast.NodeTransformer):
    """AST Transformer to insert timing measurements before and after each statement."""

    def add_timing(self, node):
        start_time = ast.parse(f'counters[{node.lineno}] = perf_counter()').body[0]
        end_time = ast.parse(dedent(f'''\
            num_times_run[{node.lineno}] = num_times_run.get({node.lineno}, 0) + 1
            durations[{node.lineno}] = durations.get({node.lineno}, 0) + (perf_counter() - counters[{node.lineno}])
            ''')).body
        return [start_time, node, *end_time]

    def visit_FunctionDef(self, node):
        node.body = sum([self.add_timing(stmt) for stmt in node.body], [])
        return self.generic_visit(node)

    def visit(self, node):
        if isinstance(node, self.node_types_to_time):
            return self.add_timing(self.generic_visit(node))
        return self.generic_visit(node)


def measure_performance(file:Path, imports_only=False, min_limit=.001, num_decimals=4, max_width=None, sort_by_time=True, suppress_print=True, skip_lines_containing='', print_modified_code=False, print_links=False):

    with file.open('r') as f:
        source_code = f.read()

    execute_and_time(source_code, file=file, imports_only=imports_only, min_limit=min_limit, num_decimals=num_decimals, max_width=max_width, sort_by_time=sort_by_time, suppress_print=suppress_print, skip_lines_containing=skip_lines_containing, print_modified_code=print_modified_code, print_links=print_links)


def execute_and_time(source_code, file:Path=None, imports_only=False, min_limit=.001, num_decimals=4, max_width=None, sort_by_time=True, suppress_print=True, skip_lines_containing='', print_modified_code=False, print_links=False):
    global_vars = {
        'perf_counter': perf_counter,
        'counters': dict(),
        'durations': dict(),
        'num_times_run': dict(),
        '__file__': str(file),
        '__name__': '__main__',

    }
    print('code with timings:DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD', print_modified_code)
    # if print_modified_code:

    if suppress_print:
        def suppressed_print(*args, **kwargs):
            return
        global_vars['print'] = suppressed_print

    if skip_lines_containing:
        source_code = '\n'.join([line if skip_lines_containing not in line else '' for line in source_code.splitlines()])

    original_lines = source_code.splitlines()

    # add timing code
    tree = ast.parse(source_code)  # Parse code into AST
    timing_transformer = TimingTransformer()

    # ast.For, ast.While, ast.If,
    timing_transformer.node_types_to_time = (ast.Assign, ast.Expr, ast.Import, ast.ImportFrom)
    if imports_only:
        timing_transformer.node_types_to_time = (ast.Import, ast.ImportFrom)

    transformed_tree = timing_transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)  # Ensure correct AST structure
    instrumented_code = astor.to_source(transformed_tree)
    if print_modified_code:
        print('code with timings:')
        print(instrumented_code)

    original_sysargv_zero = sys.argv[0]
    try:
        sys.argv[0] = str(file)
        start_time = perf_counter()
        exec(instrumented_code, global_vars)
        total_duration = perf_counter() - start_time
    except Exception as e:
        sys.argv[0] = original_sysargv_zero
        print(f'\n⚠️ Error while executing instrumented code: {e}')
        return

    sys.argv[0] = original_sysargv_zero

    print('\n⏳ Execution Times:')
    print('duration | lno |   n | source')
    print('------------------------------')
    durations = global_vars['durations']
    if sort_by_time:
        durations = dict(sorted(durations.items(), key=lambda item: item[1]))

    execution_count_render_width = len(str(max(global_vars['num_times_run'].values())))

    for lineno, duration in durations.items():
        if duration < min_limit:
            continue
        execution_count = global_vars['num_times_run'].get(lineno, 0)
        original_line = original_lines[lineno-1]
        clickable_link = '' if (file is None or not print_links) else f' | \033[90m{file}:{lineno}:\033[0m'
        avg_time_per_execution = duration / execution_count if execution_count > 0 else 0
        source_line = original_line[:max_width] if max_width is not None else original_line

        print(f'{duration:.{num_decimals}f} | {lineno:03d} | {execution_count:>{execution_count_render_width}}{clickable_link}| {source_line}')

    print('total duration:', total_duration)


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


# if __name__ == '__main__':
#     example_code = dedent("""\
#         from ursina import Array2D, string_to_2d_list, hsv, chunk_list
#         import time
#         air_colors = [hsv(0,0,1), ]
#         spriteshape_colors = [hsv(0,0,0),] + [hsv(i,.75,.2) for i in range(300, 50, -50)]
#         spriteshape_palette = {name : color_pair for name, color_pair in
#             zip(
#                 ('terrain', 'buildings', 'terrain_2'),
#                 chunk_list(spriteshape_colors, 2)
#                 )
#             }

#         print('AAAAAAAAAAA! ignore this print!')

#         from ursina import *
#         app = Ursina()
#         app.run() # make sure to ignore this line so it doesn't start the while loop

#         l = []
#         for i in range(4):
#             time.sleep(.1)
#             l.append((i*i*i))

#         """)

#     # print('\nprofiling code:')
#     # execute_and_time(example_code, skip_lines_containing='app.run()')

#     # print('\nprofiling imports only:')
#     # execute_and_time(example_code, skip_lines_containing='app.run()', imports_only=True)

#     print('\nprofiling file:')
#     measure_performance(Path('.') / 'example_script_to_profile.py', min_limit=0)

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
