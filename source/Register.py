class Register(object):
    def __init__(self):
        self._status = 0 # 1 means waiting to be written, 0 means idle or reading
        self._realVal = 0.0 # the current value stored in register
        self._bypassVal = 0.0 # the value achieved by bypassing
        self._ready = 0 # at which clock cylce will it be ready
        self._written = 0 # at which clock cycle will it be written

    @property
    def status(self):
        return self._status
    @status.setter
    def status(self, value):
        self._status = value

    @property
    def realVal(self):
        return self._realVal
    @realVal.setter
    def realVal(self, value):
        self._realVal = value

    @property
    def bypassVal(self):
        return self._bypassVal
    @bypassVal.setter
    def bypassVal(self, value):
        self._bypassVal = value

    @property
    def ready(self):
        return self._ready
    @ready.setter
    def ready(self, value):
        self._ready = value

    @property
    def written(self):
        return self._written
    @written.setter
    def written(self, value):
        self._written = value

