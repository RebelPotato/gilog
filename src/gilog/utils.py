def toHex(s):
    return "".join([hex(ord(c))[2:].zfill(2) for c in s])


def sdbm_hash(s):
    """Return a 512 bit sdbm hash of the string s."""
    h = 0
    for c in s:
        h = ord(c) + (h << 6) + (h << 16) - h
        h = h & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

    return h


def combine(*args):
    """Combine the argument hash values into a single hash value."""
    return sdbm_hash("".join([sdbm_hash(toHex(arg)) for arg in args]))
