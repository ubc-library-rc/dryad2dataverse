'''Downloads dryad jsons and saves them'''
import pickle
import sqlite3
import zipfile
import urllib.parse
import json
from bs4 import BeautifulSoup as bs
import requests

DBASE = '/Users/paul/Documents/Work/Projects/dryad2dataverse/analysis/dryadInfo.db'

def get_dois(dump, numpages=9):
    '''
    dump : str
        path to pickle holding DOI list
    Harvests dryad DOIs and dumps them into a pickle
    for future reference.
    '''
    doilist = []
    for i in range(1, numpages+1): #number of pages, in this case 9
        #Dryad URL search page
        dry1 = 'https://datadryad.org/search?f%5Bdryad_author_affiliation_name_sm\
                %5D%5B%5D=University+of+British+Columbia&page='.replace(' ', '')
        dry2 = '&per_page=1000&sort=solr_year_i+desc%2C+\
                dc_title_sort+asc'.replace(' ', '')
        url = dry1 + str(i) + dry2
        html = requests.get(url)
        if html.status_code == 404:
            break
        soup = bs(html.text, 'html.parser')
        dois = [x['href'] for x in soup.find_all('a') if 'doi' in x['href']]
        dois = [x[x.find('doi'):] for x in dois]
        doilist += dois
    with open(dump, 'wb') as f:
        pickle.dump(doilist, f)
    return dump


def load(dump):
    '''
    dump : str
        complete path to pickle containing dump
    load dois from pickle
    '''
    with open(dump, 'rb') as f:
        dois = pickle.load(f)
    return dois

def make_db(*args):
    '''Create a database to hold the data and download it'''
    conn = sqlite3.Connection(DBASE)
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS dryadjson (doi TEXT \
                    PRIMARY KEY, json TEXT);')
    conn.commit()

    #Download all the JSONS
    headers = {'accept':'application/json', 'Content-Type':'application/json'}
    for doi in args:
        doiclean = urllib.parse.quote(doi, safe='')
        resp = requests.get(f'https://datadryad.org/api/v2/datasets/{doiclean}',
                            headers=headers, timeout=45)
        resp.raise_for_status()
        cursor.execute('INSERT INTO dryadjson (doi, json) VALUES (?, ?)',
                       (doi, json.dumps(resp.json())))
        conn.commit()
    conn.close()

def make_zip(outfile, doi):
    '''Add the JSONs to a zip file if desired'''
    with zipfile.ZipFile(outfile, 'a', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        conn = sqlite3.Connection(DBASE)
        cursor = conn.cursor()
        cursor.execute('SELECT json FROM dryadjson WHERE\
                        doi = ?', (doi,))
        out = cursor.fetchone()[0]
        z.writestr(f'{doi}.json', out)
        conn.close()
        #z.close()

def make_nice_tables():
    '''get some actual info out
    all = cursor.execute('select json from dryadjson').fetchall()
    all2 =[json.loads(x[0]) for x in all]
    author_keys = set([y.keys() for x in all2 for y in x['authors']])
    all author keys: ['lastName', 'affiliation', 'orcid', 'affiliationROR', 'firstName', 'email']

    >>> all2[0].keys()
    dict_keys(['_links', 'identifier', 'id', 'storageSize', 'title', 'authors',
    'abstract', 'funders', 'keywords', 'methods', 'usageNotes', 'relatedWorks', 'versionNumber',
    'versionStatus', 'curationStatus', 'publicationDate', 'lastModificationDate', 'visibility',
    'sharingLink', 'userId', 'license'])
    '''
    conn = sqlite3.Connection(DBASE)
    cursor = conn.cursor()
    #Authors
    cursor.execute('CREATE TABLE IF NOT EXISTS authors \
                   (doi TEXT, lastName TEXT, firstName TEXT,\
                   affiliation TEXT, affiliationROR TEXT,\
                   orcid TEXT, \
                   FOREIGN KEY(doi) REFERENCES dryadjson(doi));')
    #Titles
    cursor.execute('CREATE TABLE IF NOT EXISTS title \
                   (doi TEXT, title text,\
                   FOREIGN KEY(doi) REFERENCES dryadjson(doi));')
    #Size
    cursor.execute('CREATE TABLE IF NOT EXISTS size \
                   (doi TEXT, sizeByte INT, sizeMb INT,\
                   FOREIGN KEY(doi) REFERENCES dryadjson(doi));')
    #versions
    cursor.execute('CREATE TABLE IF NOT EXISTS versions \
                   (doi TEXT, version REAL, \
                   FOREIGN KEY (doi) REFERENCES dryadjson(doi));')
    #license
    cursor.execute('CREATE TABLE IF NOT EXISTS license \
                   (doi TEXT, license TEXT, \
                   FOREIGN KEY(doi) REFERENCES dryadjson(doi));')
    #now fetch!
    alldata = [json.loads(x[0]) for x in cursor.execute('SELECT json from dryadjson').fetchall()]
    for i in alldata:
        #author_keys = set([y.keys() for x in alldata for y in x['authors']])
        for a in i['authors']:
            cursor.execute("INSERT INTO authors (doi, lastName, firstName, affiliation, \
                           affiliationROR, orcid) VALUES (?, ?, ?, ?, ?, ?);",
                           (i['identifier'], a['lastName'], a['firstName'], a.get('affiliation'),
                            a.get('affiliationROR'), a.get('orcid')))
        cursor.execute("INSERT INTO title (doi, title) VALUES (?, ?);",
                       (i['identifier'], i['title']))
        cursor.execute("INSERT INTO size (doi, sizeByte, sizeMb) VALUES \
                       (?, ?, ?);", (i['identifier'], int(i['storageSize']),
                                     int(i['storageSize'])/1024**2))
        cursor.execute("INSERT INTO versions (doi, version) VALUES (?, ?);",
                       (i['identifier'], i['versionNumber']))
        cursor.execute("INSERT INTO license (doi, license) VALUES (?, ?);",
                       (i['identifier'], i['license']))
    conn.commit()
    conn.close()

def clean_db():
    '''Remove everything but the downloaded JSONs'''

    conn = sqlite3.Connection(DBASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE tbl_name != 'dryadjson';")
    tables = [t[0] for t in cursor.fetchall()]
    for drop in tables:
        cursor.execute(f'DROP TABLE IF EXISTS {drop};')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    DOIFILE = get_dois('/Users/paul/Documents/Work/Projects/\
                      dryad2dataverse/analysis/dryadDois.pickle'.replace(' ', ''))
    DOIS = load(DOIFILE)
    make_db(*DOIS)
    for d in DOIS:
        make_zip('/Users/paul/Documents/Work/Projects/dryad2dataverse/analysis/dryadjson.zip', d)
    clean_db()
    make_nice_tables()
