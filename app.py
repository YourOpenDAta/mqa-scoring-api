#!/usr/bin/env python3
'''
YODA (Your Open DAta)
EU CEF Action 2019-ES-IA-0121
University of Cantabria
Developer: Johnny Choque (jchoque@tlmat.unican.es)
'''

from flask import Flask, request, abort, jsonify
from rdflib import Graph
import mqaMetrics as mqa
from functools import wraps
from werkzeug.exceptions import HTTPException

MAX_LENGTH = 3*1024*1024

app = Flask(__name__)

def get_metrics(g):
  metrics = {}
  for sub, pred, obj in g:
    if pred not in metrics.keys():
      metrics[pred] = None
  for pred in metrics.keys():
    obj_list=[]
    for obj in g.objects(predicate=pred):
      obj_list.append(obj)
    metrics[pred] = obj_list
  return metrics

def str_metric(val, g):
  valStr=str(val)
  for prefix, ns in g.namespaces():
    if val.find(ns) != -1:
      metStr = valStr.replace(ns,prefix+":")
      return metStr

def otherCases(pred, objs, g):
  for obj in objs:
    met = str_metric(obj, g)
    if met == None:
      val = str_metric(pred, g)
    else:
      val = str(met)
  return val

def get_mqa_summary(mqa_values):
  w = []
  for k, v in mqa_values.items():
    for k1, v1 in v.items():
      if k1 == 'weight':
        w.append(v1)
  score = sum(w)
  if score in range(121):
    rate = 'Bad'
  elif score in range(121,221):
    rate = 'Sufficient'
  elif score in range(221,351):
    rate = 'Good'
  elif score in range(351,406):
    rate = 'Excellent'
  else:
    rate = 'Error'

  return {'score': score, 'rate': rate}

def check_payload_limit(max_length):
  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      cl = request.content_length
      if cl is not None and cl > max_length:
          abort(413)
      return func(*args, **kwargs)
    return wrapper
  return decorator

@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify(error=str(e)), code

@app.route('/mqavalues', methods=['POST'])
@check_payload_limit(MAX_LENGTH)
def mqavalues():
  mqa_values = {}
  dataset = request.get_data().decode("utf-8")
  edp = mqa.edp_validator(dataset)
  mqa_values['edp'] = edp
  g = Graph()
  g.parse(data=dataset, format="application/rdf+xml")
  metrics = get_metrics(g)

  others = {}
  others['report'] = 'Not included in MQA'
  others['values'] = []
  others['weight'] = 0

  for pred in metrics.keys():
    met = str_metric(pred, g)
    objs = metrics[pred]
    if met == "dcat:accessURL":
      mqa_values['accessurl'] = mqa.accessURL(objs)
    elif met == "dcat:downloadURL":
      mqa_values['downloadurl'] = mqa.downloadURL(objs)
    elif met == "dcat:keyword":
      mqa_values['keyword'] = mqa.keyword()
    elif met == "dcat:theme":
      mqa_values['theme'] = mqa.theme()
    elif met == "dct:spatial":
      mqa_values['spatial'] = mqa.spatial()
    elif met == "dct:temporal":
      mqa_values['temporal'] = mqa.temporal()
    elif met == "dct:format":
      mqa_values['format'] = mqa.format(objs)
    elif met == "dct:license":
      mqa_values['license'] = mqa.license(objs)
    elif met == "dcat:contactPoint":
      mqa_values['contactpoint'] = mqa.contactpoint()
    elif met == "dcat:mediaType":
      mqa_values['mediatype'] = mqa.mediatype(objs)
    elif met == "dct:publisher":
      mqa_values['publisher'] = mqa.publisher()
    elif met == "dct:accessRights":
      mqa_values['accessrights'] = mqa.accessrights(objs)
    elif met == "dct:issued":
      mqa_values['issued'] = mqa.issued()
    elif met == "dct:modified":
      mqa_values['modified'] = mqa.modified()
    elif met == "dct:rights":
      mqa_values['rights'] = mqa.rights()
    elif met == "dcat:byteSize":
      mqa_values['bytesize'] = mqa.byteSize()
    else:
      others['values'].append(otherCases(pred, objs, g))

  mqa_values['others'] = others

  if ('format' in mqa_values) and ('mediatype' in mqa_values):
    mqa_values['format_mediatype'] = mqa.format_mediatype(mqa_values['format']['result'], mqa_values['mediatype']['result'])

  result = {}
  result['values'] = mqa_values
  result['summary'] = get_mqa_summary(mqa_values)

  return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

