import pdb

import rdflib
from rdflib import Graph, Namespace, RDF, RDFS, OWL

BRICK_VERSION = '1.0.3'

BRICK = Namespace('https://brickschema.org/schema/{0}/Brick#'
                  .format(BRICK_VERSION))
BRICK_USE = Namespace('https://brickschema.org/schema/{0}/BrickUse#'
                      .format(BRICK_VERSION))
BF = Namespace('https://brickschema.org/schema/{0}/BrickFrame#'
               .format(BRICK_VERSION))
BRICK_TAG = Namespace('https://brickschema.org/schema/{0}/BrickTag#'
                      .format(BRICK_VERSION))
BASE = Namespace('http://example.com/')
IOT = Namespace('https://iotschema.org/')

sparql_prefix = """
prefix brick: <{0}>
prefix rdf: <{1}>
prefix rdfs: <{2}>
prefix base: <{3}>
prefix bf: <{4}>
prefix owl: <{5}>
""".format(str(BRICK), RDF, RDFS, BASE, str(BF), OWL)

g = Graph()
g.bind('rdf', RDF)
g.bind('rdfs', RDFS)
g.bind('brick', BRICK)
g.bind('bf', BF)
g.bind('base', BASE)
brick_file = 'http://brickschema.org/schema/{0}/Brick.ttl'.format(
    BRICK_VERSION)
g.parse(brick_file, format='turtle')

def get_all_measurements(tagsets, remove_postfix=True):
    qstr = """
    select ?point where {{
        {{?point rdfs:subClassOf ?tagset.}}
        values ?tagset {{ {0} }}
    }}
    """.format(' '.join(['brick:' + tagset for tagset in tagsets]))
    points = [row['point'] for row in g.query(sparql_prefix + qstr).bindings]
    measures = []
    for point in points:
        if point.split('_')[-1] not in tagsets:
            continue
        measure = point.split('#')[-1]
        if remove_postfix:
            measure = '_'.join(measure.split('_')[0:-1])
        measures.append(measure)
    return measures

actions = get_all_measurements(['Command'])
events = get_all_measurements(['Alarm'], remove_postfix=False)
props = get_all_measurements(['Sensor', 'Setpoint'])
props += get_all_measurements(['Status'], remove_postfix=False)

# Create iotschemaorg
iot = Graph()
iot.bind('brick', BRICK)
iot.bind('bf', BF)
iot.bind('iot', IOT)

def add_subclass(child, parent):
    iot.add((child, RDFS.subClassOf, parent))
    iot.add((child, RDF.type, RDFS.Class))

add_subclass(BRICK['Sensor'], IOT['Capability'])
add_subclass(BRICK['Command'], IOT['Capability'])
add_subclass(BRICK['Setpoint'], IOT['Capability'])
add_subclass(BRICK['Alarm'], IOT['Capability'])
add_subclass(BRICK['Status'], IOT['Capability'])
for prop in props:
    add_subclass(BRICK[prop], IOT['Property'])
for action in actions:
    add_subclass(BRICK[action], IOT['Action'])
for event in events:
    add_subclass(BRICK[event], IOT['Event'])

context = {'iot': str(IOT),
           'rdf': str(RDF),
           'rdfs': str(RDFS),
           'brick': str(BRICK),
           }
iot.serialize('brick2iotschemaorg.jsonld', format='json-ld',
              context=context, indent=2)


