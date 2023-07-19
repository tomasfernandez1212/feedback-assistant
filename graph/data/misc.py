from enum import Enum, auto


class Rating(Enum):
    ONE = auto()
    TWO = auto()
    THREE = auto()
    FOUR = auto()
    FIVE = auto()


RATING_MAPPING = {
    1: Rating.ONE,
    2: Rating.TWO,
    3: Rating.THREE,
    4: Rating.FOUR,
    5: Rating.FIVE,
}
