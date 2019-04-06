""" this are utils for process data """
widths = [
    (126,    1), (159,    0), (687,     1), (710,   0), (711,   1), 
    (727,    0), (733,    1), (879,     0), (1154,  1), (1161,  0), 
    (4347,   1), (4447,   2), (7467,    1), (7521,  0), (8369,  1), 
    (8426,   0), (9000,   1), (9002,    2), (11021, 1), (12350, 2), 
    (12351,  1), (12438,  2), (12442,   0), (19893, 2), (19967, 1),
    (55203,  2), (63743,  1), (64106,   2), (65039, 1), (65059, 0),
    (65131,  2), (65279,  1), (65376,   2), (65500, 1), (65510, 2),
    (120831, 1), (262141, 2), (1114109, 1),
]
 
def get_width( o ):
    """Return the screen column width for unicode ordinal o."""
    global widths
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if ord(o) <= num:
            return wid
    return 1


def get_str_width(s):
	"""Return the output length of string s."""
	ans = 0
	for i in s:
		ans += get_width(i)
	return ans

def lformat(s,length):
    """Return a string which has specified width."""
    ans = ""
    cur_len = 0
    for i in s:
        if cur_len >= length:
            ans += '\n'
            cur_len = 0
        cur_len += get_width(i)
        ans += i
    return ans


def rformat(s,length,screen_length):
    """Return a string which has specified width,
    s is origin string, length is the width what
    you want, screen_length is screen_length.
    """
    if screen_length < length:
        raise Exception("screen_length must greater than or equal to length")
    ans = ""
    cur_len = 0
    total_len = get_str_width(s)
    lines = total_len // length
    for i in s:
        if lines > 0 and cur_len == 0:
            ans += " "*(screen_length-length)
            lines -= 1
        elif lines == 0 and cur_len == 0:
            ans += " "*(screen_length - total_len % length)
        ans += i 
        cur_len += get_width(i)
        if cur_len >= length:
            ans += '\n'
            cur_len = 0
    return ans
