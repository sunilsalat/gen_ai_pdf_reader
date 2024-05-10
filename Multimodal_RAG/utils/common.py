
def remove_leading_dots(path):
    if path.startswith('.'):
        path_without_dot = path[2:]
    else:
        path_without_dot = path

    return path_without_dot


__all__ = ["remove_leading_dots"]