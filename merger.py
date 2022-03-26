def merge(destination, source):
    if isinstance(destination, list):
        for key, value in source.items():
            if isinstance(value, dict):
                ik = int(key)
                while len(destination) <= ik:
                    destination.append({})
                merge(destination[int(key)], value)
            else:
                destination[int(key)] = value
    elif isinstance(destination, dict):
        for key, value in source.items():
            if isinstance(value, dict):
                merge(destination.setdefault(key, {}), value)
            else:
                destination[key] = value

    return destination
