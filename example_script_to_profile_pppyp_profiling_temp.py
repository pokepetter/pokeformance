from time import perf_counter; num_lines=2; durations = [0 for i in range(num_lines+1)]; num_times_run = [0 for i in range(num_lines+1)]; min_limit = 0; rounding = 4; skip_fast_lines = False; show_line_numbers = True; sort_by_time = False; a = 5
t=perf_counter(); b = [i*i for i in range(1000)]; dur=perf_counter()-t; durations[1]+=dur; num_times_run[1]+=1;


# print results
lines=['a = 5\n', 'b = [i*i for i in range(1000)]\n']

results = [[i, durations[i], num_times_run[i], lines[i]] for i in range(num_lines)]
if sort_by_time: results.sort(key=lambda x: x[2])
for res in results:
    i, duration, n, text = res
    if skip_fast_lines and duration < min_limit: continue
    duration_text = f'{round(duration,rounding)}' if duration >= min_limit else ''
    num_times_run_text = n if n > 0 else ''
    line_number = i if show_line_numbers else ''
    print(f'{duration_text:<7}|{num_times_run_text:>3} |{line_number:>4}|{text.rstrip()}')
