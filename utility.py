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

