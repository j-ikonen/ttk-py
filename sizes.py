class Sizes:
    is_scaled = False
    xs = 2
    s = 5
    m = 8
    l = 12
    frame_w = 1200
    frame_h = 600

    @classmethod
    def scale(cls, source):
        if not cls.is_scaled:
            cls.xs = source.FromDIP(cls.xs)
            cls.s = source.FromDIP(cls.s)
            cls.m = source.FromDIP(cls.m)
            cls.l = source.FromDIP(cls.l)
            cls.frame_w = source.FromDIP(cls.frame_w)
            cls.frame_h = source.FromDIP(cls.frame_h)
            cls.is_scaled = True