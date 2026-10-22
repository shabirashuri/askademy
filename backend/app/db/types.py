import enum

from sqlalchemy import Enum


def pg_enum(enum_class: type[enum.Enum], name: str) -> Enum:
    """Postgres enum that stores member values ("teacher"), matching the migrations."""
    return Enum(enum_class, name=name, values_callable=lambda e: [m.value for m in e])
