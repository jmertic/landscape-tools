# Landscape Tools

![](https://github.com/jmertic/landscape-tools/workflows/CI/badge.svg)

This project contains some tools for making it easier to build and maintain a [landscape](https://github.com/cncf/landscapeapp).

Current tools are:

- [newlandscapemembers.py](newlandscapemembers.py) - Create a new landscape.yml file with members populated. Leverages LF SFDC as the primary data source for members include, and uses Crunchbase, the LF website, and [other landscapes](https://github.com/cncf/landscapeapp/blob/master/landscapes.yml) as secondary data sources for data enrichment.
- [updatelandscapemembers.py](updatelandscapemembers.py) - Updates an existing landscape.yml file with not included; does not update existing members. Leverages LF SFDC as the primary data source for members include, and uses Crunchbase, the LF website, and [other landscapes](https://github.com/cncf/landscapeapp/blob/master/landscapes.yml) as secondary data sources for data enrichment.

## Installation

```
git clone https://github.com/jmertic/landscape-tools
cd landscape-tools
chmod +x *.py
pip install -r requirements.txt
```

## Configuration

All of the scripts depend on a `config.yaml` file being present in the same directory as the script to provide any configuration variables. Settings are below...

```yaml
sf_username: # LF SFDC username
sf_password: # LF SFDC password
sf_token: # LF SFDC token ( instructions how to get one at https://help.salesforce.com/articleView?id=user_security_token.htm&type=5 )
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
project: # name of the project as listed in LF SFDC
landscapeMemberCategory: # category name of the members section in the landscape.yml file
landscapefile: # filename to use for the outputted landscape.yml file
missingcsvfile: # filename to use for the list of entries with missing parts ( such as a logo, website, or crunchbase entry )
```

In addition, this depends on `CRUNCHBASE_KEY` being set to a valid key.

## Contributing

Feel free to send [issues](/issues) or [pull requests](/pulls) ( with a DCO signoff of course :-) ) in accordance with the [contribution guidelines](CONTRIBUTING.md)
