from enum import Enum


class SourceType(str, Enum):
    NEWS = "NEWS"
    DISCLOSURE = "DISCLOSURE"
    REPORT = "REPORT"
    TWITTER = "TWITTER"
