class IdConverter:
    regex = "\d{1,4}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return str(value)