# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- structure for local data storage, with file paths specified in `constants.py`
- `models.Postcode`, to convert between
- `models.Address`, to unify different address formats as a `pl.Struct`.
- `models.PriceRecord`, Pydantic model to handle structuring, writing and reading of historical price records for different properties.
- `models.PropertyInfo`, Pydantic model to handle structuring, writing and reading of general property information.
- `constants.RecordType`, Enum to classify different historical price record types.
- `constants.PropertyType`, Enum to classify different property types.
- `constants.PropertyCondition`, as an abstract enum to classify condition.
- Several fixtures and pytests to validate all functionality.
- postcode file for Australia
- country name to country code mapping file.
