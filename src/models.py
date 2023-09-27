from typing import NamedTuple


class Vuz(NamedTuple):
    Abbr: str
    Name: str
    City: str


class Specialization(NamedTuple):
    VuzAbbr: str
    Code: str
    Name: str
    Direction: str
    Url: str


class Program(NamedTuple):
    VuzAbbr: str
    SpecCode: str
    Name: str
    Level: str
    IsPayment: bool
    Cost: int
    PaymentPlaces: str
    FreePlaces: str
    Form: str
    DurationInMonths: int
    Subjects: list[str]
    Url: str


class ProgramHeader(NamedTuple):
    Cost: int
    FreePlaces: int
    PaymentPlaces: int
    DurationInMonths: int


class ProgramDetails(NamedTuple):
    Level: str
    Form: str