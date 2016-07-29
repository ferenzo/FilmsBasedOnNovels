from rdflib import Graph, Namespace, URIRef, Literal, XSD
import urllib3
import certifi
from time import sleep
from datetime import datetime
import json
from lxml import etree
from src.helper import is_float, quote_url_field, get_tree_by_url

KEY_FILE = "../goodreads_key.json"
GR_BASE_URL = "https://www.goodreads.com/book/title.xml?"
GR_NS = Namespace("http://www.frohde.de/ontology/goodreads/")


def read_key():
    file = open(KEY_FILE, 'r')
    data = json.load(file)
    return data["key"]


def fix_name_switch(string):
    pos = string.find(",")
    if pos > 0:
        string = string[(pos+1):]+" "+string[:pos]
    return string.lstrip()


def string_part(string, variant):
    parts = string.split('+')
    if variant == "FirstAndLast":
        return parts[0]+"+"+parts[len(parts) - 1]
    elif variant == "OnlyLast":
        return parts[len(parts) - 1]
    else:
        return string


def get_ratingtriples(g_WP):
    qres = g_WP.query("""
        SELECT ?novel ?noveltitle ?authorname
        WHERE {
        ?film dbo:basedOn ?novel .
        ?novel dbo:author ?author .
        ?novel dbp:name ?noveltitle .
        ?author dbp:name ?authorname
        } GROUP BY ?novel
        """)

    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    g = Graph()
    g.bind("gr", GR_NS)

    key_string = "&key="+read_key()

    for novel, titleRaw, authorRaw in qres:
        author_full = quote_url_field(fix_name_switch(authorRaw))
        title = quote_url_field(titleRaw)
        doc = etree.Element("empty")

        i = 0
        doc_error = False
        while not(doc.xpath('boolean(/GoodreadsResponse)')):
            if i == 0:
                author = author_full
            elif i == 1:
                sleep(1.1)
                author = string_part(author_full, "FirstAndLast")
            elif i == 2:
                sleep(1.1)
                author = string_part(author_full, "OnlyLast")
            else:
                doc_error = True
                print("Book not found: "+titleRaw+" by "+authorRaw)
                break
            print(title, "--", author)
            url = GR_BASE_URL + "author=" + author + "&title=" + title + key_string
            # print(url)
            doc = get_tree_by_url(http, url)
            i += 1

        if not doc_error:
            gr_id = doc.xpath('/GoodreadsResponse/book/id/text()')
            if gr_id: # Not empty
                gr_id = GR_NS.bookID+"#"+gr_id[0]
            else:
                break
            gr_title = doc.xpath('/GoodreadsResponse/book/title/text()')
            if gr_title:  # Not empty
                gr_title = gr_title[0]
            else:
                break
            gr_rating = doc.xpath('/GoodreadsResponse/book/average_rating/text()')
            if gr_rating:  # Not empty
                gr_rating = gr_rating[0]
            else:
                break
            gr_originalyear = doc.xpath('/GoodreadsResponse/book/work/original_publication_year/text()')
            if gr_originalyear:  # Not empty
                gr_originalyear = gr_originalyear[0]
            else:
                gr_originalyear = "ABC"  # not decimal
            # print(gr_id, gr_title, gr_rating)

            g.add((URIRef(novel), GR_NS.bookID, URIRef(gr_id)))
            g.add((URIRef(gr_id), GR_NS.title, Literal(gr_title)))
            if is_float(gr_rating):
                g.add((URIRef(gr_id), GR_NS.rating, Literal(gr_rating, datatype=XSD.decimal)))
            if gr_originalyear.isdecimal():
                gr_originalyear = datetime(int(gr_originalyear), 1, 1)
                g.add((URIRef(gr_id), GR_NS.year, Literal(gr_originalyear, datatype=XSD.dateTime)))

        sleep(1.1)

    return g

