# CPG - Crypto Payments Gateway
---
### Requirements
* MongoDB 4.0
* python 3.7
* Pipenv

Also, ElectrumX server required for correct work

### Instalation
###### Prepare Mongo
Run `mongo` and execute this script wich creates user and gives him permissions
```
use cpg
db.createUser(
    {
        user: "cpg_user",
        pwd: "read_manual",
        roles: [ { role: "readWrite", db: "cpg" },
                 { role: "readWrite", db: "cpg_test" }
               ]
    }
)
```
###### Install dependencies
Activate pipenv
```
pipenv shell
```
Install dependencies
```
pipenv install
```
You can provide key `-d` to install development dependencies

###### Configuration
Default configuration stores in `confg/cpg_configuration_default.yml`. You should create custom config file in `config/cpg_configuration.yml` or set path to config file in `CPG_CONFIG_PATH` env variabale which will be merged with default configuration.

### Running
###### Start app
```
python -m gateway
```

Run tests
```
pytest
```

Run linter
```
pylint gateway
```

Run PEP8 checker
```
flake8
```
