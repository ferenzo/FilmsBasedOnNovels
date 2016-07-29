from src.helper import read_html, write_html
from lxml import etree
from rdflib import namespace
import csv

HTML_PATH = "../result/"
DBP_NS = namespace.Namespace("http://dbpedia.org/property/")
DBR_NS = namespace.Namespace("http://dbpedia.org/resource/")
DBO_NS = namespace.Namespace("http://dbpedia.org/ontology/")
OMDB_NS = namespace.Namespace("http://www.frohde.de/ontology/omdb/")
GR_NS = namespace.Namespace("http://www.frohde.de/ontology/goodreads/")

MAX_IMDB_RATING = 10
MAX_GR_RATING = 5


def create_subelement(_parent, _tag, _text=None):
    result = etree.SubElement(_parent, _tag)
    result.text = _text
    return result


def open_csv(path):
    file = open(path, 'w', newline='')
    return csv.writer(file, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)


def better_books(g):
    g.bind("dbp", DBP_NS)
    g.bind("dbr", DBR_NS)
    g.bind("dbo", DBO_NS)
    g.bind("omdb", OMDB_NS)
    g.bind("gr", GR_NS)

    qres = g.query("""
        SELECT (COUNT(?film) as ?totalNum) (SUM(IF(?imdbNormed > ?novelNormed, 1, 0)) as ?betterBooks) (SUM(IF(?imdbNormed > ?novelNormed, 1, 0))/COUNT(?film) as ?perc)
        WHERE {
        ?film dbo:basedOn ?novel .
        ?film omdb:omdbID ?omdbFilm .
        ?omdbFilm omdb:imdbRating ?imdbRating .
        ?novel gr:bookID ?grBook .
        ?grBook gr:rating ?novelRating
        BIND ((?novelRating/"""+str(MAX_GR_RATING)+""") as ?novelNormed)
        BIND ((?imdbRating/"""+str(MAX_IMDB_RATING)+""") as ?imdbNormed)
        FILTER (?novelRating != "0.00")
        }
        """)
    for total, betterBooks, perc in qres:
        print(total, '\t', betterBooks, '\t', perc)


def DiffRatingByTime(g):
    g.bind("dbp", DBP_NS)
    g.bind("dbr", DBR_NS)
    g.bind("dbo", DBO_NS)
    g.bind("omdb", OMDB_NS)
    g.bind("gr", GR_NS)

    qres = g.query("""
        SELECT ?filmYear (AVG(?imdbNormed-?novelNormed) as ?diffRating)
        WHERE {
        ?film dbo:basedOn ?novel .
        ?film omdb:omdbID ?omdbFilm .
        ?omdbFilm omdb:imdbRating ?imdbRating .
        ?omdbFilm omdb:year ?filmDate .
        ?novel gr:bookID ?grBook .
        ?grBook gr:rating ?novelRating
        BIND (year(?filmDate) as ?filmYear)
        BIND ((?novelRating/"""+str(MAX_GR_RATING)+""") as ?novelNormed)
        BIND ((?imdbRating/"""+str(MAX_IMDB_RATING)+""") as ?imdbNormed)
        FILTER (?novelRating != "0.00")
        } GROUP BY ?filmYear
        ORDER BY ?filmYear
        """)
    csvwriter = open_csv("../results/diffRatingByTime.csv")
    csvwriter.writerow(["Jahr"] + ["Durchschnittliche Bewertungsdifferenz"])
    for year, diffRating in qres:
        csvwriter.writerow([year] + [round(float(diffRating), 3)])
        # print(year, '\t', diffRating)


def DiffRatingByTimeDiff(g):
    g.bind("dbp", DBP_NS)
    g.bind("dbr", DBR_NS)
    g.bind("dbo", DBO_NS)
    g.bind("omdb", OMDB_NS)
    g.bind("gr", GR_NS)

    qres = g.query("""
        SELECT ?yearDiff (AVG(?imdbNormed-?novelNormed) as ?diffRating)
        WHERE {
        ?film dbo:basedOn ?novel .
        ?film omdb:omdbID ?omdbFilm .
        ?omdbFilm omdb:imdbRating ?imdbRating .
        ?omdbFilm omdb:year ?filmDate .
        ?novel gr:bookID ?grBook .
        ?grBook gr:year ?novelDate .
        ?grBook gr:rating ?novelRating
        BIND ((year(?filmDate) - year(?novelDate)) as ?yearDiff)
        BIND ((?novelRating/"""+str(MAX_GR_RATING)+""") as ?novelNormed)
        BIND ((?imdbRating/"""+str(MAX_IMDB_RATING)+""") as ?imdbNormed)
        FILTER (?novelRating != "0.00")
        } GROUP BY ?yearDiff
        ORDER BY ?yearDiff
        """)
    csvwriter = open_csv("../results/diffRatingByTimeDiff.csv")
    csvwriter.writerow(["Jahresdifferenz"] + ["Durchschnittliche Bewertungsdifferenz"])
    for year, diffRating in qres:
        csvwriter.writerow([year] + [round(float(diffRating), 3)])
        #print(year, '\t', round(float(diffRating), 3))


def NovelsWithMultipleAdaptations(g):
    g.bind("dbp", DBP_NS)
    g.bind("dbr", DBR_NS)
    g.bind("dbo", DBO_NS)
    g.bind("omdb", OMDB_NS)
    g.bind("gr", GR_NS)

    qres = g.query("""
        SELECT (COUNT(?film) as ?adaptationsNum) ?novelTitle ?novelAuthor
        WHERE {
        ?film dbo:basedOn ?novel .
        ?novel gr:bookID ?grBook .
        ?novel dbo:author ?author .
        ?grBook gr:title ?novelTitle .
        ?author dbp:name ?novelAuthor
        } GROUP BY ?novel
        HAVING (COUNT(?film) > 1)
        ORDER BY DESC(?adaptationsNum)
        """)
    csvwriter = open_csv("../results/NovelsWithMultipleAdaptations.csv")
    csvwriter.writerow(["Anzahl Adapationen"] + ["Titel"] + ["Autor"])
    for adaptationsNum, novelTitle, novelAuthor in qres:
        csvwriter.writerow([adaptationsNum] + [novelTitle] + [novelAuthor])
        #print(adaptationsNum, '\t', novelTitle, '\t', novelAuthor)


def generate_html_results(g):
    g.bind("dbp", DBP_NS)
    g.bind("dbr", DBR_NS)
    g.bind("dbo", DBO_NS)
    g.bind("omdb", OMDB_NS)
    g.bind("gr", GR_NS)

    qres = g.query("""
        SELECT ?filmTitle ?filmYear ?imdbNormed ?novelTitle ?novelAuthor ?novelNormed ?novelYear
        WHERE {
        ?film dbo:basedOn ?novel .
        ?film omdb:omdbID ?omdbFilm .
        ?omdbFilm omdb:imdbRating ?imdbRating .
        ?omdbFilm omdb:title ?filmTitle .
        ?omdbFilm omdb:year ?filmDate .
        ?novel gr:bookID ?grBook .
        ?grBook gr:title ?novelTitle .
        ?grBook gr:year ?novelDate .
        ?novel dbo:author ?author .
        ?author dbp:name ?novelAuthor .
        ?grBook gr:rating ?novelRating
        BIND (year(?filmDate) as ?filmYear)
        BIND (year(?novelDate) as ?novelYear)
        BIND ((?novelRating/"""+str(MAX_GR_RATING)+""") as ?novelNormed)
        BIND ((?imdbRating/"""+str(MAX_IMDB_RATING)+""") as ?imdbNormed)
        FILTER (?novelRating != "0.00")
        } ORDER BY ?filmYear
        """)

    doc = read_html(HTML_PATH + "base.html")
    body = doc.xpath('//body')[0]
    table = etree.SubElement(body, 'table')
    # Head Row
    row = etree.SubElement(table, 'tr')
    create_subelement(row, 'th', _text="Filmtitel")
    create_subelement(row, 'th', _text="Jahr")
    create_subelement(row, 'th', _text="IMDB-Rating")
    create_subelement(row, 'th', _text="Romantitel")
    create_subelement(row, 'th', _text="Autor")
    create_subelement(row, 'th', _text="Jahr")
    create_subelement(row, 'th', _text="Rating")

    for filmTitle, filmYear, imdbRating, novelTitle, novelAuthor, novelRating, novelYear in qres:

        row = etree.SubElement(table, 'tr')
        create_subelement(row, 'td', _text=filmTitle)
        create_subelement(row, 'td', _text=filmYear)
        create_subelement(row, 'td', _text=imdbRating)
        create_subelement(row, 'td', _text=novelTitle)
        create_subelement(row, 'td', _text=novelAuthor)
        create_subelement(row, 'td', _text=novelYear)
        create_subelement(row, 'td', _text=novelRating)

    write_html(doc, HTML_PATH+"table.html")


def list_films(g):

    qres = g.query("""
        select ?film ?title where {
          ?film dbp:name ?title
        }
        """)
    for film, title in qres:
        print(film, '\t', title)


def list_pairs(g):

    qres = g.query("""
        select ?film ?novel where {
          ?film dbp:name ?novel
        }
        """)
    for film, novel in qres:
        print(film, '\t', novel)
