class DictAccess:

    @staticmethod
    def get(func):
        def inside(inst, key):
            data = func(inst, key)
            return data[key] if key in data else None

        return inside

    @staticmethod
    def set(func):
        def inside(inst, key, val):
            data = func(inst, key, val)
            data[key] = val

        return inside


class URL:
    @staticmethod
    def is_url(string_url):
        import re
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(regex, string_url) is not None
