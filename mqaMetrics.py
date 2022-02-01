'''
YODA (Your Open DAta)
EU CEF Action 2019-ES-IA-0121
University of Cantabria
Developer: Johnny Choque (jchoque@tlmat.unican.es)
'''

import requests
from flask import abort
from rdflib import Graph
import os
import json

URL_EDP = 'https://data.europa.eu/api/mqa/shacl/validation/report'
HEADERS = {'content-type': 'application/rdf+xml'}
MACH_READ_FILE = os.path.join('edp-vocabularies', 'edp-machine-readable-format.rdf')
NON_PROP_FILE = os.path.join('edp-vocabularies', 'edp-non-proprietary-format.rdf')

def load_edp_vocabulary(file):
  g = Graph()
  g.parse(file, format="application/rdf+xml")
  voc = []
  for sub, pred, obj in g:
    voc.append(str(sub))
  return voc

def accessURL(urls):
  checked = True
  for url in urls:
    try:
      res = requests.head(url)
      if res.status_code in range(200, 399):
        checked = checked and True
      else:
        checked = checked and False
    except:
      checked = checked and False
  if checked:
    report = 'Validation of HTTP HEAD request is OK. Weight assigned 50'
    weight = 50
  else:
    report = 'Responded status code of HTTP HEAD request is not in the 200 or 300 range. No weight assigned'
    weight = 0
  return {'report': report, 'weight': weight}

def valResult(d):
  if 'sh:conforms' in d:
    return d['sh:conforms']
  for k in d:
    if isinstance(d[k], list):
      for i in d[k]:
        if 'sh:conforms' in i:
          return i['sh:conforms']
  
def edp_validator(dataset):
  try:
    r_edp = requests.post(URL_EDP, data=dataset, headers=HEADERS)
    r_edp.raise_for_status()
  except requests.exceptions.HTTPError as err:
    abort(err.response.status_code)
  detail = json.loads(r_edp.text)
  if valResult(detail):
    report = 'The metadata has successfully passed the EDP validator. Weight assigned 30'
    weight = 30
  else:
    report = "DCAT-AP errors found in metadata. No weight assigned"
    weight = 0
  return {'report': report, 'weight': weight}

def downloadURL(urls):
  checked = True
  report = 'The property is set. Weight assigned 20'
  weight = 20
  for url in urls:
    try:
      res = requests.head(url)
      if res.status_code in range(200, 399):
        checked = checked and True
      else:
        checked = checked and False
    except:
      checked = checked and False
  if checked:
    report = report + '. Validation of HTTP HEAD request is OK. Additional weight assigned 30'
    weight = weight + 30
  else:
    report = report + '. Responded status code of HTTP HEAD request is not in the 200 or 300 range. No additional weight assigned'
  return {'report': report, 'weight': weight}

def keyword():
  weight = 30
  report = 'The property is set. Weight assigned 30'
  return {'report': report, 'weight': weight}

def theme():
  weight = 30
  report = 'The property is set. Weight assigned 30'
  return {'report': report, 'weight': weight}

def spatial():
  weight = 20
  report = 'The property is set. Weight assigned 20'
  return {'report': report, 'weight': weight}

def temporal():
  weight = 20
  report = 'The property is set. Weight assigned 20'
  return {'report': report, 'weight': weight}

def format(urls):
  mach_read_voc = []
  non_prop_voc = []  
  mach_read_voc = load_edp_vocabulary(MACH_READ_FILE)
  non_prop_voc = load_edp_vocabulary(NON_PROP_FILE)
  mach_read_checked = True
  non_prop_checked = True
  found_checked = True
  report = 'The property is set. Weight assigned 20'
  weight = 20
  for url in urls:
    if str(url) in mach_read_voc:
      mach_read_checked = mach_read_checked and True
    else:
      mach_read_checked = mach_read_checked and False
    if str(url) in non_prop_voc:
      non_prop_checked = non_prop_checked and True
    else:
      non_prop_checked = non_prop_checked and False
    g = Graph()
    g.parse(url, format="application/rdf+xml")
    if (url, None, None) in g:
      found_checked = found_checked and True
    else:
      found_checked = found_checked and False
  if mach_read_checked:
    report = report + '. The property is machine-readable. Additional weight assigned 20'
    weight = weight + 20
  else:
    report = report + 'The property is not machine-readable. No additional weight assigned'
  if non_prop_checked:
    report = report + '. The property is non-propietary. Weight assigned 20'
    weight = weight + 20
  else:
    report = report + '. The property is not non-propietary. No additional weight assigned'
  if found_checked:
    result = True
  else:
    result = False
  return {'report': report, 'weight': weight, 'result': result}

def license(urls):
  checked = True
  weight = 20
  report = 'The property is set. Weight assigned 20'
  for url in urls:
    g = Graph()
    g.parse(url, format="application/rdf+xml")
    if (url, None, None) in g:
      checked = checked and True
    else:
      checked = checked and False
  if checked:
    weight = weight + 10
    report = report + 'The property provides the correct license information. Additional weight assigned 10'
  else:
    report = report + 'The license is incorrect-' + str(url) + '. No additional weight assigned'
  return {'report': report, 'weight': weight}

def contactpoint():
  weight = 20
  report = 'The property is set. Weight assigned 20'
  return {'report': report, 'weight': weight}

def mediatype(urls):
  checked = True
  weight = 10
  report = 'The property is set. Weight assigned 10'
  for url in urls:
    res = requests.head(str(url))
    if res.status_code != 404:
      checked = checked and True
    else:
      checked = checked and False
  if checked:
    result = True
  else:
    result = False
  return {'report': report, 'weight': weight, 'result': result}

def publisher():
  weight = 10
  report = 'The property is set. Weight assigned 10'
  return {'report': report, 'weight': weight}

def accessrights(urls):
  checked = True
  weight = 10
  report = 'The property is set. Weight assigned 10'
  for url in urls:
    g = Graph()
    g.parse(url, format="application/rdf+xml")
    if (url, None, None) in g:
      checked = checked and True
    else:
      checked = checked and False
  if checked:
    weight = weight + 5
    report = report + 'The property uses a controlled vocabulary. Additional weight assigned 5'
  else:
    report = report + 'The license is incorrect-' + str(url) + '. No additional weight assigned'
  return {'report': report, 'weight': weight}

def issued():
  weight = 5
  report = 'The property is set. Weight assigned 5'
  return {'report': report, 'weight': weight}

def modified():
  weight = 5
  report = 'The property is set. Weight assigned 5'
  return {'report': report, 'weight': weight}

def rights():
  weight = 5
  report = 'The property is set. Weight assigned 5'
  return {'report': report, 'weight': weight}

def byteSize():
  weight = 5
  report = 'The property is set. Weight assigned 5'
  return {'report': report, 'weight': weight}

def format_mediatype(f_resp, m_resp):
  if f_resp and m_resp:
    weight = 10
    report = 'The properties belong to a controlled vocabulary. Weight assigned 10'
  else:
    weight = 0
    report = 'The properties do not belong to a controlled vocabulary'
  return {'report': report, 'weight': weight}