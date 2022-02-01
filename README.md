# mqa-scoring-api

The Metadata Quality Assurance (MQA) methodology is defined by the data.europa.eu consortium with the aim of improving the accessibility of datasets published on EU open data portals. It specifies several indicators that help to improve the quality of the metadata harvested by the data.europa.eu portal.

mqa-scoring-api is a flask-based service that calculates the score a metadata obtains according to the MQA indicators. The service also verifies that the requirements specified by the MQA for each indicator are met.

## Installation

- Create a python virtual environment (venv) and activate it  
`mqa-scoring-api$ python3.6 -m venv mqavenv`
`mqa-scoring-api$ source mqavenv/bin/activate`

- Install the required packages  
`(mqavenv):~/mqa-scoring-api$ pip install -r requirements.txt`

- Deactivate the virtual environment  
`(mqavenv):~/mqa-scoring-api$ deactivate`

- Create systemd Unit File  
Modify the paths included in mqa-scoring-api.service file according to the directories where you have installed the service and copy it to the systemd.  
`mqa-scoring-api$ sudo cp mqa-scoring-api.service /etc/systemd/system/`

- Enable and start the new service  
`mqa-scoring-api$ sudo systemctl enable mqa-scoring-api.service`
`mqa-scoring-api$ sudo systemctl start mqa-scoring-api.service`

- Check the status of the service  
`mqa-scoring-api$ sudo systemctl status mqa-scoring-api.service`

- Configuring Apache2 as a Reverse Proxy  
Create the Apache host configuration file, enable it and reload the Apache2 service


## Usage

`curl --location --request POST 'https://<server>/mqavalues' --data-raw <rdf-file>`

## Example of response

The main results are in the `summary` dictionary.

The `score` key correspond to the overall scoring of the dataset according to the MQA parameters.

The `rate` key correspond to the MQA rating category according to score obtained.

```json
{
    "summary": {
        "rate": "Bad",
        "score": 30
    },
    "values": {
        "edp": {
            "report": "DCAT-AP errors found in metadata. No weight assigned",
            "weight": 0
        },
        "format": {
            "report": "The property is not set",
            "result": false,
            "weight": 0
        },
        "format_mediatype": {
            "report": "The properties do not belong to a controlled vocabulary",
            "weight": 0
        },
        "mediatype": {
            "report": "The property is not set",
            "result": false,
            "weight": 0
        },
        "others": {
            "report": "Not included in MQA",
            "values": [
                "dct:description",
                "dcat:Dataset",
                "dct:title"
            ],
            "weight": 0
        },
        "theme": {
            "report": "The property is set. Weight assigned 30",
            "weight": 30
        }
    }
}
```
