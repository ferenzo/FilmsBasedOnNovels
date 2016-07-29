from rdflib import Graph
from src import wikipedia
from src import omdb
from src import goodreads
from src import sparql
from src.helper import read_rdf, write_rdf
DATA_PATH = "../data/"

# Where to start processing
step = 1

if step <= 1:
    g_WP = Graph()
    wikipedia.getFilmsBasedOnNovels(g_WP)
    write_rdf(DATA_PATH+"films.rdf", g_WP)
    step += 1

if step <= 2:
    g_WP = read_rdf(DATA_PATH+"films.rdf")
    wikipedia.getBookFromInfobox(g_WP)
    write_rdf(DATA_PATH+"wikipedia.rdf", g_WP)
    step += 1

if step <= 3:
    g_WP = read_rdf(DATA_PATH+"wikipedia.rdf")
    g_OMDB = omdb.get_ratingtriples(g_WP)
    write_rdf(DATA_PATH+"omdb.rdf", g_OMDB)
    step += 1

if step <= 4:
    g_WP = read_rdf(DATA_PATH+"wikipedia.rdf")
    g_GR = goodreads.get_ratingtriples(g_WP)
    write_rdf(DATA_PATH+"gr.rdf", g_GR)
    step += 1

if step <= 5:
    g = read_rdf(DATA_PATH+"wikipedia.rdf")
    g = read_rdf(DATA_PATH+"omdb.rdf", g)
    g = read_rdf(DATA_PATH+"gr.rdf", g)
    write_rdf(DATA_PATH + "g.rdf", g)
    step += 1

if step <= 6:
    sparql.DiffRatingByTime(g)
    sparql.DiffRatingByTimeDiff(g)
    sparql.NovelsWithMultipleAdaptations(g)
    sparql.better_books(g)
    sparql.generate_html_results(g)
