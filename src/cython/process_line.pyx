import re
re_log_line = re.compile("(.*?),(.*?),(.*)\n")

cpdef int process_line(char *line):
    re_obj = re_log_line.search(line)
    try:
        elems = re_obj.groups()
    except:
        pass
    else:
        if elems[1] == "cpu_usage":
            return int(elems[2])

