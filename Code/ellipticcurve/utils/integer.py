import urandom


class RandomInteger:

    @classmethod
    def between(cls, min, max):
        """
        Return integer x in the range: min <= x <= max

        :param min: minimum value of the integer
        :param max: maximum value of the integer
        :return:
        """

        return urandom.randint(min, max + 1)
