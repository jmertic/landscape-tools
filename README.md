# Landscape Tools

[![License](https://img.shields.io/github/license/jmertic/landscape-tools)](LICENSE)
[![CI](https://github.com/jmertic/landscape-tools/workflows/CI/badge.svg)](https://github.com/jmertic/landscape-tools/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/jmertic/landscape-tools/graph/badge.svg?token=A05TDQO69V)](https://codecov.io/gh/jmertic/landscape-tools)
[![CodeQL](https://github.com/jmertic/landscape-tools/actions/workflows/codeql.yml/badge.svg)](https://github.com/jmertic/landscape-tools/actions/workflows/codeql.yml)

This project contains some tools for making it easier to build and maintain a [landscape](https://github.com/cncf/landscapeapp).

Current tools are:

- [landscapemembers.py](landscapemembers.py) - Creates a new landscape.yml or updates an existing landscape.yml file with members populated. Leverages LF SFDC as the primary data source for members include, and uses Crunchbase and [other landscapes](https://github.com/cncf/landscapeapp/blob/master/landscapes.yml) as secondary data sources for data enrichment.
- [makememberprojectlogos.sh](makememberprojectlogos.sh) - Creates uniform project/product logos for an organization where they don't have a specific logo to use.
- [downloadcrunchbasedata.sh](downloadcrunchbasedata.sh) - Fetches the latest CSV dump of organizations from crunchbase
- [buildimages.sh](buildimages.sh) - Creates images for all the projects of a given company, using the given image as base and adds the project name underneath.

## Installation

```bash
git clone https://github.com/jmertic/landscape-tools
cd landscape-tools
pip install -r requirements.txt
```

If you wish to use crunchbase as a data source, add this command.

```bash
./downloadcrunchbasedata.sh 
```

## Configuration

All of the Python scripts depend on a `config.yaml` file being present in the same directory as the script to provide any configuration variables, or passing a `-c` option to the script with a path to the config file. Settings are below.

```yaml
landscapeName: # short name of your landscape - matches entry at https://github.com/cncf/landscapeapp/blob/master/landscapes.yml
landscapeMemberClasses: # classes of membership; name matches how it's listed in LF SFDC, and category how it will be listed in the landscape. Example below...
   - name: Associate Membership
     category: Associate
   - name: Gold Membership
     category: Gold
   - name: Platinum Membership
     category: Platinum
   - name: Silver Membership
     category: Silver
project: # project slug
landscapeMemberCategory: # category name of the members section in the landscape.yml file
landscapefile: # filename to use for the outputted landscape.yml file
missingcsvfile: # filename to use for the list of entries with missing parts ( such as a logo, website, or crunchbase entry )
```

### Environment variables

This depends on `CRUNCHBASE_KEY` being set to a valid key if you wish to use that as a data source ( required by [downloadcrunchbasedata.sh](downloadcrunchbasedata.sh) ).

## Contributing

Feel free to send [issues](/issues) or [pull requests](/pulls) ( with a DCO signoff of course :-) ) in accordance with the [contribution guidelines](CONTRIBUTING.md)
