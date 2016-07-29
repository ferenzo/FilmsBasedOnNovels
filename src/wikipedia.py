import urllib3
import certifi
import re
from datetime import datetime
from rdflib import Graph, namespace, URIRef, Literal, XSD
from SPARQLWrapper import SPARQLWrapper, JSON, TURTLE
import mwparserfromhell
from src.helper import print_triples, write_rdf, read_rdf, get_tree_by_url, quote_url_field_lax

DBP_NS = namespace.Namespace("http://dbpedia.org/property/")
DBR_NS = namespace.Namespace("http://dbpedia.org/resource/")
DBO_NS = namespace.Namespace("http://dbpedia.org/ontology/")

WPAPI_BASE = "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&rvsection=0&format=xml&titles="
DATA_PATH = "../data/"


def getFilmsBasedOnNovels(g):
    g.bind("dbp", DBP_NS)
    g.bind("dbr", DBR_NS)

    sparql = SPARQLWrapper("http://live.dbpedia.org/sparql")
    sparql.setQuery("""
        SELECT ?film
        WHERE {
              ?film rdf:type dbo:Film .
              ?class skos:broader* dbc:Films_based_on_novels .
              ?film dct:subject ?class .
              ?film dbp:wikiPageUsesTemplate dbt:Based_on
        } GROUP BY ?film
    """)
    sparql.setReturnFormat(JSON)

    try:
        films = sparql.query().convert()
    except:
        return ConnectionError

    for film in films["results"]["bindings"]:
        uri = film["film"]["value"]
        urlparts = uri.split("/")
        title = urlparts[len(urlparts)-1]
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setQuery("""
            SELECT ?filmtitle ?filmyear
            WHERE {
                <"""+uri+"""> dbp:name ?filmtitle.
                OPTIONAL{<"""+uri+"""> dbp:released ?filmyear}
                filter(langMatches(lang(?filmtitle),'en'))
            }
            LIMIT 1
        """)
        sparql.setReturnFormat(JSON)
        qres = sparql.query().convert()
        for result in qres["results"]["bindings"]:
            print(uri, '\t', result["filmtitle"]["value"])
            g.add((URIRef(uri), DBP_NS.name, Literal(result["filmtitle"]["value"])))
            if result.get("filmyear"):
                year = re.findall(r'([0-9]{4})', result["filmyear"]["value"])
                if len(year) > 0:
                    year = datetime(int(year[0]), 1, 1)
                    g.add((URIRef(uri), DBP_NS.released, Literal(year, datatype=XSD.dateTime)))
            else:
                year = re.findall(r'\(([0-9]{4})_film\)', title)
                print(title, '\t', year)
                if len(year) > 0:
                    year = datetime(int(year[0]), 1, 1)
                    g.add((URIRef(uri), DBP_NS.released, Literal(year, datatype=XSD.dateTime)))

    # g.parse(data=results, format='turtle')
    return g


def getBookFromInfobox(g):
    g.bind("dbp", DBP_NS)
    g.bind("dbr", DBR_NS)
    g.bind("dbo", DBO_NS)

    qres = g.query("""
        SELECT ?film
        WHERE {
            ?film dbp:name ?filmtitle
            }
        """)
    my_headers = {
        'User-Agent': 'Film-Book-Ratings-Comparision-Tool 1.0',
        'From': 'florens.rohde@stud.htwk-leipzig.de'
    }
    http = urllib3.PoolManager(headers=my_headers, cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    for film in qres:
        urlparts = film["film"].split("/")
        url = WPAPI_BASE+quote_url_field_lax(urlparts[len(urlparts)-1])
        print(url)
        doc = get_tree_by_url(http, url)
        infobox = doc.xpath('/api//revisions/rev/text()')
        if len(infobox) > 0:
            wikicode = mwparserfromhell.parse(infobox[0])
            templates = wikicode.filter_templates()
            for template in templates:
                if template.name.lower() == "based on":
                    s = str(template.params[0].value)
                    title = re.findall(r'\[\[([^\]\|]+)[^\]]*\]\]', s)
                    print(s, '\t', title)
                    if len(title) != 0:
                        title = str(DBR_NS) + title[0].replace(" ", "_")
                        print(title)
                        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
                        sparql.setQuery("""
                            SELECT ?noveltitle ?author ?authorname
                            WHERE {
                                  <""" + title + """> rdf:type dbo:Work .
                                  <""" + title + """> dbo:author ?author .
                                  <""" + title + """> dbp:name ?noveltitle .
                                  ?author dbp:name ?authorname
                            } LIMIT 1
                            """)
                        sparql.setReturnFormat(JSON)
                        qres2 = sparql.query().convert()
                        for result2 in qres2["results"]["bindings"]:
                            print(result2["noveltitle"]["value"], '\t', result2["author"]["value"], '\t', result2["authorname"]["value"])
                            g.add((URIRef(film["film"]), DBO_NS.basedOn, URIRef(title)))
                            g.add((URIRef(title), DBP_NS.name, Literal(result2["noveltitle"]["value"])))
                            g.add((URIRef(title), DBO_NS.author, URIRef(result2["author"]["value"])))
                            g.add((URIRef(result2["author"]["value"]), DBP_NS.name, Literal(result2["authorname"]["value"])))
                    break
        else:
            print("Infobox not found!")
    return g
