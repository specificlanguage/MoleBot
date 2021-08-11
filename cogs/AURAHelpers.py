def line_routed_direction(cur, prev, nex):
    start, end = 0, 0
    for i in range(len(cur.links)):
        l = cur.links[i]
        if l == prev:
            start = i
        if l == nex:
            end = i
    return start, end  # Returns two "strings" of start/end nodes