from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import Literal


class Result(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor: str
    equiv_names: list[str] = Field(default_factory=list)
    application_id: str
    version: str
    equiv_releases: list[str] = Field(default_factory=list)
    doc_type: list[
        Literal[
            "LDO",
            "LAB",
            "RAD",
            "VPS",
            "RSA",
            "CERT_VACC",
            "SING_VACC",
            "LAB_TRASF",
            "PSS",
            "RAP",
        ]
    ]
    service: list[Literal["VALIDATION", "PUBLICATION"]]
    date: date
    gtw_version: Literal["1.0"]


class Results(BaseModel):
    results: list[Result]


if __name__ == "__main__":
    import json

    print(json.dumps(Results.model_json_schema(), indent=4))
