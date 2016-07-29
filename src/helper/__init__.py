from urllib import parse
from lxml import etree
from rdflib import Graph


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def print_triples(graph):
    for s, p, o in graph:
        print(s, "\t", p, "\t", o)


def read_rdf(path, g=Graph()):
    file = open(path, 'rb')
    return g.parse(file, format='turtle')


def write_rdf(path, graph):
    file = open(path, 'wb')
    file.write(graph.serialize(format='turtle'))
    print("Wrote graph into "+path)


def read_html(path):
    file = open(path, 'rb')
    return etree.parse(file)


def write_html(doc, path):
    file = open(path, 'wb')
    doc.write(file, pretty_print=True)
    print("Wrote HTML to " + path)


def quote_url_field(string):
    return parse.quote(string.replace(" ", "+"), safe='/+')


def quote_url_field_lax(string):
    return parse.quote(string.replace(" ", "+"), safe='/+?!()')


def get_tree_by_url(http, url):
    res = http.request('GET', url)
    # print(res.data)
    return etree.fromstring(res.data)