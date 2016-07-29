from rdflib import Graph, Namespace, URIRef, Literal, XSD
import urllib3
import json
from datetime import datetime
from src.helper import is_float, quote_url_field

OMDB_BASE_URL = "http://www.omdbapi.com/?r=json&type=movie&tomatoes=true"
OMDB_NS = Namespace("http://www.frohde.de/ontology/omdb/")


def get_ratingtriples(g_WP):
    qres = g_WP.query("""
        SELECT ?film ?filmtitle (year(?date) as ?year)
        WHERE {
        ?film dbo:basedOn ?novel .
        ?film dbp:name ?filmtitle .
        OPTIONAL {?film dbp:released ?date}
        }
        """)

    http = urllib3.PoolManager()
    g = Graph()
    g.bind("omdb", OMDB_NS)

    for film, titleRaw, year in qres:
        title = quote_url_field(titleRaw)

        if not year:
            year = ""
        else:
            year = quote_url_field(year)
        url = OMDB_BASE_URL+"&y="+year+"&t="+title
        print(url)
        res = http.request('GET', url)
        res = json.loads(res.data.decode('utf-8'))
        if "Response" not in res or res["Response"] == "False":
            print("Film not found:", titleRaw, "(", year, ")")
            continue
        imdbID = OMDB_NS.omdbID+"#"+res["imdbID"]
        g.add((URIRef(film), OMDB_NS.omdbID, URIRef(imdbID)))
        g.add((URIRef(imdbID), OMDB_NS.title, Literal(res["Title"])))
        if is_float(res["imdbRating"]):
            g.add((URIRef(imdbID), OMDB_NS.imdbRating, Literal(res["imdbRating"], datatype=XSD.decimal)))
        if is_float(res["tomatoRating"]):
            g.add((URIRef(imdbID), OMDB_NS.tomatoRating, Literal(res["tomatoRating"], datatype=XSD.decimal)))
        if res["Year"].isdecimal():
            year = datetime(int(res["Year"]), 1, 1)
            g.add((URIRef(imdbID), OMDB_NS.year, Literal(year, datatype=XSD.dateTime)))
        if res.get("Country"):
            g.add((URIRef(imdbID), OMDB_NS.country, Literal(res["Country"])))
    return g
