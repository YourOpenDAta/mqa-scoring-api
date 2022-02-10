# MQA scoring API

This document details how the `mqa-scoring-api` application has been implemented from the developer's point of view. 

The Metadata Quality Assessment (MQA) methodology defines a set of indicators on the basis of which the quality assessment of the dataset is carried out. Each indicator must meet a set of conditions based on the use of one or more properties of the DCAT-AP vocabulary (metrics). Each valid indicator is assigned a weight whose value is defined in the MQA methodology. 

The application uses RDFLib, which is a pure Python package for working with RDF. RDFLib has several functionalities to work with RDF, two of which will be mainly used:
- parsers and serializers for various RDF serialization formats (e.g. RDF/XML)
- an object called Graph which is a Python collection of RDF Subject, Predicate, Object Triples

For this application, the file containing all the metadata to be validated is called `dataset`. It is created in RDF/XML format as in the following example:

```xml
<?xml version="1.0" encoding="utf-8"?>
<rdf:RDF
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:dcat="http://www.w3.org/ns/dcat#"
  xmlns:dct="http://purl.org/dc/terms/"
>
<dcat:Dataset rdf:about="https://www.google.com/">
  <dcat:distribution>
    <dcat:Distribution rdf:about="https://www.google.com/">
      <dct:license>
        <dct:LicenseDocument rdf:about="http://publications.europa.eu/resource/authority/licence/CC_BY_4_0">
          <dct:type rdf:resource="http://purl.org/adms/licencetype/PublicDomain"/>
        </dct:LicenseDocument>
      </dct:license>
    </dcat:Distribution>
  </dcat:distribution>
</dcat:Dataset>
</rdf:RDF>
```

## The main module (app.py)

The app.py file contains the main algorithm of the application. Flask is used to expose the application's functionality via an API. Flask is a lightweight WSGI web application framework for Python. 

The Flask module is imported and an instance is created in the `app` variable. This variable is basically the REST application that would be invoked as an API.

The `mqavalues()` function contains the logic that implements the quality measures of the indicators specified in the MQA methodology.

The decorator `@app.route('/mqavalues', methods=['POST'])` binds this function to the endpoint `{servername}/mqavalues` and indicates that it only accepts POST requests.

Finally, in the `__main__` section, the `app.run()` function is called. This function starts the REST API on the server. Gunicorn and Apache2 are used to deploy the server in production mode.

The `mqavalues()` function extracts the DCAT-AP vocabulary properties that have been included in the dataset to be evaluated one by one. This is done by invoking the functions corresponding to each metric implemented in the `mqaMetrics` module. Each function of that module returns a JSON that includes mainly two keys: `report` and `weight`. The `report` key includes information about the validation process, e.g. whether a metric was valid, the weight assigned to it, the reason why it was invalid, etc. The `weight` key includes the total weight assigned to the metric. In some cases the same metric is included in several indicators, so the function that evaluates the metric sums the results of all of them. Finally, the JSON returned by the functions is included in the `mqa_values` dictionary by means of a key whose name is the same as the name of the function that performed the validation.  

By means of the `get_mqa_summary()` function, the overall scoring of the dataset is obtained by adding the weights of each metric. It also calculates the rating category to which the dataset belongs according to the range of values specified in the MQA methodology. These values are included in the `mqa_values` dictionary by means of the `score` and `rate` keys, respectively.

An example of the final result returned by the endpoint `{servername}/mqavalues` would be the following:

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
        "license": {
            "report": "The property is set. Weight assigned 20. The property provides the correct license information. Additional weight assigned 10",
            "weight": 30
        },
        "others": {
            "report": "Not included in MQA",
            "values": [
                "dcat:distribution",
                "dcat:Dataset",
                "dct:type"
            ],
            "weight": 0
        }
    }
}
```

## The metrics module (mqaMetrics.py)

The `mqaMetrics` module includes all the functions that allow to calculate the weights assigned to each indicator according to the MQA methodology. Each of these functions includes an algorithm based on the `checked` variable that allows to control the evaluation of all repeated metrics within a dataset. If an indicator metric appears multiple times in the dataset, the most restrictive condition is applied. This means that the weight of the indicator will be assigned only once and only if all instances of that metric meet the conditions of the MQA methodology.

The `edp_validator()` function allows to calculate the value of the `DCAT-AP compliance` indicator. The validation tool, provided by data.europa.eu, is used to verify that the dataset is DCAT-AP compliant. This function sends the dataset to the API of the validation tool and analyses the result returned with the `valResult` function. If the validation tool does not detect any issues, then it assigns a weight of 30 to the `DCAT-AP compliance` indicator.

The `load_edp_vocabulary()` function allows to load the vocabularies specified by `data.europa.eu`, which will be used during the evaluation of the `dct:format` property. These vocabularies have been cloned from the `https://gitlab.com/european-data-portal/edp-vocabularies` repository and stored inside the `edp-vocabularies` directory. The user must verify that the `edp-vocabularies` directory has an up-to-date version of these vocabularies.

The `accessURL()` function allows to calculate the value of the `AccessURL accessibility` indicator. The accessibility of the URL specified by `dcat:accessURL` is checked by sending an HTTP HEAD request to the specified URL. If the status of the response is within the range of 200 or 300, then the indicator is validated and a value of 50 is assigned as the weight.

The `downloadURL()` function allows the value of the `DownloadURL` and `DownloadURL accessibility` indicators to be calculated. For the `DownloadURL` indicator, only the `dcat:downloadURL` property is checked. This is implicit when the `downloadURL()` function is called, so a weight of 20 is assigned. For the `DownloadURL accessibility` indicator, the same procedure used to evaluate the `AccessURL accessibility` indicator is performed. If the accessibility is positive, an additional weight of 30 is assigned.

The `publisher()`, `keyword()`, `theme()`, `spatial()`, `temporal()`, `issued()`, `modified()`, `rights()`, `byteSize()` and `contactpoint()` functions allow the value of the indicators `Publisher`, `Keyword usage`, `Categories`, `Geo search`, `Time based search`, `Date of issue`, `Modification date`, `Rights`, `File size` and `Contact point`, respectively, to be calculated. In all these cases, only the existence of the property corresponding to each indicator is checked, which is implicit during the function call. The weight assigned in each case depends on the indicator.

The `format()` function allows to calculate the value of the `Format`, `Non-proprietary` and `Machine readable` indicators. For the `Format` indicator, only the `dct:format` property is checked, which is implicit during the function call. For the `Non-proprietary` indicator it is checked that the URL specified within the `dct:format` property is included in the `edp-non-proprietary-format.rdf` vocabulary. This vocabulary is loaded into the system via the `load_edp_vocabulary` function. The `Machine readable` indicator is evaluated in a similar way, only in this case it is checked against the `edp-machine-readable-format.rdf` vocabulary. In both cases, if the indicator is valid, a weight of 20 is assigned. Additionally, together with the `dcat:mediaType` property, it also allows the evaluation of the `Format / Media type from vocabulary` indicator. In this case it is checked that the URL specified by the `dct:format` property is valid. This is done by parsing the RDF indicated by the URL and verifying that the same URL is included in the returned rdflib.Graph() triple. The status of this check is controlled by the `found_checked` variable. The final status of this check is returned to the system via the `result` key, which will be used in the `format_mediatype()` function to evaluate the weight of the `Format / Media type from vocabulary` indicator.

The `license()` function allows to calculate the value of the indicators `License information` and `License vocabulary`. For the `License information` indicator, only the `dct:license` property is checked. Since this is implicit during the function call, a default weight of 20 is assigned. For the `License vocabulary` indicator, the URL specified by `dct:license` is checked to ensure that it is valid. This is done by parsing the RDF indicated by the URL and verifying that the same URL is included in the returned rdflib.Graph() triple. If the check is successful, an additional weight of 10 is assigned.

The `mediatype()` function mainly allows to calculate the value of the `Media type` indicator by checking that the `dcat:mediaType` property exists. Since this is implicit during the function call, a default weight of 10 is assigned. Additionally, together with the `dct:format` property, it also allows the evaluation of the `Format / Media type from vocabulary` indicator. In this case it is checked that the URL specified by the `dcat:mediaType` property is valid. This is done by parsing the RDF indicated by the URL and verifying that the same URL is included in the returned rdflib.Graph() triple. The status of this check is controlled by the `checked` variable. The final status of this check is returned to the system via the `result` key, which will be used in the `format_mediatype()` function to evaluate the weight of the `Format / Media type from vocabulary` indicator.

The `accessrights()` function allows to calculate the value of the indicators `Access restrictions` and `Access restrictions vocabulary`. For the `Access restrictions` indicator, only the `dct:accessRights` property is checked. Since this is implicit during the function call, a default weight of 10 is assigned. With respect to the `Access restrictions vocabulary` indicator, we check that the URL specified by `dct:accessRights` is valid. First we check that the URL is of type URI, to avoid BNode values. Then we parse the RDF indicated by the URL and verify that the same URL is included in the returned rdflib.Graph() triple. If the check is correct, an additional weight of 5 is assigned.

The `format_mediatype()` function mainly allows to calculate the value of the `Format / Media type from vocabulary` indicator. This indicator uses the `dct:format` and `dcat:mediaType` properties, which are evaluated in the `format()` and `mediatype()` functions, respectively. The `format_mediatype()` function uses the results of those two previous functions, in particular those that verify that the URLs of those properties belong to the vocabularies specified by the MQA methodology.  If both checks are correct, a weight of 10 is assigned.

