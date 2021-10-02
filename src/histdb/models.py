import json
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, List, Optional

import click
from click.testing import CliRunner
from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import registry, relationship, sessionmaker
from sqlalchemy.sql.expression import func
from sqlalchemy.sql.sqltypes import NullType

mapper_registry = registry()
metadata = mapper_registry.metadata


@mapper_registry.mapped
@dataclass
class Commands:
    __tablename__ = "commands"
    __sa_dataclass_metadata_key__ = "sa"

    id: int = field(init=False, metadata={"sa": Column(Integer, primary_key=True)})
    argv: Optional[str] = field(
        default=None, metadata={"sa": Column(Text, unique=True)}
    )

    history: List = field(
        default_factory=list,
        metadata={"sa": relationship("History", back_populates="command")},
    )


@mapper_registry.mapped
@dataclass
class Places:
    __tablename__ = "places"
    __table_args__ = (UniqueConstraint("host", "dir"),)
    __sa_dataclass_metadata_key__ = "sa"

    id: int = field(init=False, metadata={"sa": Column(Integer, primary_key=True)})
    host: Optional[str] = field(default=None, metadata={"sa": Column(Text, index=True)})
    dir: Optional[str] = field(default=None, metadata={"sa": Column(Text, index=True)})

    history: List = field(
        default_factory=list,
        metadata={"sa": relationship("History", back_populates="place")},
    )


t_sqlite_sequence = Table(
    "sqlite_sequence", metadata, Column("name", NullType), Column("seq", NullType)
)


@mapper_registry.mapped
@dataclass
class History:
    __tablename__ = "history"
    __table_args__ = (Index("history_command_place", "command_id", "place_id"),)
    __sa_dataclass_metadata_key__ = "sa"

    id: int = field(init=False, metadata={"sa": Column(Integer, primary_key=True)})
    session: Optional[int] = field(default=None, metadata={"sa": Column(Integer)})
    command_id: Optional[int] = field(
        default=None, metadata={"sa": Column(ForeignKey("commands.id"))}
    )
    place_id: Optional[int] = field(
        default=None, metadata={"sa": Column(ForeignKey("places.id"))}
    )
    exit_status: Optional[int] = field(default=None, metadata={"sa": Column(Integer)})
    start_time: Optional[int] = field(
        default=None, metadata={"sa": Column(Integer, index=True)}
    )
    duration: Optional[int] = field(default=None, metadata={"sa": Column(Integer)})

    command: Optional[Commands] = field(
        default=None,
        metadata={"sa": relationship("Commands", back_populates="history")},
    )
    place: Optional[Places] = field(
        default=None, metadata={"sa": relationship("Places", back_populates="history")}
    )
