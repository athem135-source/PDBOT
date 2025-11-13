def get(ss, key, default=None):
    return ss[key] if key in ss else default


def set_flag(ss, key, value=True):
    ss[key] = value


def pop_flag(ss, key, default=None):
    return ss.pop(key, default)
