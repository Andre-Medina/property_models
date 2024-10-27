# Property Models

## Install

Installing is easy with [pixi](https://pixi.sh/latest/). Once installed use the following commands:

```sh
pixi install
pixi global install pre-commit
pre-commit install
```

You can get the `python.exe` file by:
```sh
pixi r which python
```


## Testing

pytests will run with pre-commit, to run manually use:
```sh
pixi run tests
```



## Backend

### Data storage

```
 - data
 |- processed
  |- country
   |- suburb_to_postcode.csv
   |- state
    |- suburb
     |- records.csv
     |- properties.json
```

#### suburb_to_postcode.csv

|suburb|postcode|
|-|-|
|str|int|

#### records.csv

|unit_number|street_number|street_name|date|record_type|price|
|-|-|-|-|-|-|
|int (nullable)|int|str|date|RecordType (str)| int|

#### properties.json

```
[
    {
        address: {
            unit_number: int
            street_number: int
            ...
        },
        bed: int | None,
        bath: int | None,
        ...
    }
]
```

#### properties.json
