import re
from multiprocessing import Pool, Value

import pandas as pd
from lxml import html
import time
from datetime import datetime
from typing import Dict, List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from elasticsearch import Elasticsearch

counter = None

def get_juridiction(juridiction) -> str:
    return re.match(r"\b.+?(?=\s-\s)\b", juridiction).group(0)


def get_numero(numero) -> str:
    return re.match(r"\b.+?:\s(.+)\b", numero).group(1)


def get_date(date) -> str:
    return re.match(r"\b.+?(\d+\s\w+\s\d+)\b", date).group(1)


def build_json(title, juridiction, rg_num, date, text, id) -> Dict:
    """
    Build the json for a jurisprudence.
    :param title:
    :param juridiction:
    :param rg_num:
    :param date:
    :param text:
    :param id:
    :return:
    """
    return \
    {
        "filename": "legifrance.parquet",
        "database": "legifrance",
        "loadedAt": datetime.now().strftime('%Y-%m-%d-%H'),
        "metadata": {
            "properties": {
                "id": id,
                "juridiction": get_juridiction(juridiction[0]) if len(juridiction) != 0 else None,
                "title": title[0] if len(title) != 0 else None,
                "number": get_numero(rg_num[0]) if len(rg_num) != 0 else None,
                "date": get_date(date[0]) if len(date) != 0 else None
            }
        },
        "text": ' '.join([str(elem) for elem in text])
    }


def get_source_code(url) -> str:
    """
    Using selenium, this function return the source code of a web page.
    :param url:
    :return:
    """
    options = Options()
    options.add_argument('--headless')
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        return driver.page_source
    except:
        driver.quit()
        print("\nWARNING: Scrapper stopped, launching again in 4 seconds...")
        time.sleep(range(2))
        driver = webdriver.Chrome(options=options)
        time.sleep(range(2))
        driver.get(url)
        return driver.page_source


def get_links(url) -> List[str]:
    """
    Get all the jurisprudence's links from a page
    :param url:
    :return:
    """
    tree = html.fromstring(str(get_source_code(url)))
    links = tree.xpath("//article/h2/a/@href")
    return links


def get_all_jurisprudence_urls(domaine) -> List[str]:
    """
    Get all the jurisprudence's links from the website
    :param domaine: nom de domaine du site
    :return:
    """
    links_current = []
    final_links = []
    paging = 1
    # Maximum page_size for legifrance is 100
    page_size = 100
    while links_current != [] or paging == 1:
        url = f"{domaine}/search/juri?tab_selection=juri&searchField=ALL&query=*&searchProximity" \
              f"=&searchType=ALL&isAdvancedResult=&isAdvancedResult=&dateDecision=01%2F06%2F2022+%3E+30%2F06%2F2022" \
              f"&pdcSearchArbo=&pdcSearchArboId=&typePagination=DEFAULT&sortValue=DATE_DESC&pageSize=" \
              f"{page_size}&page={paging}&tab_selection=juri "
        links_current = [domaine + link for link in get_links(url)]
        print(f"INFO: Number of urls on page n°{paging}: {len(links_current)}")
        final_links.extend(links_current)
        paging += 1
        print(f"INFO: Total of urls before the page({paging}) : {len(final_links)}")


def get_jurisprudence(url) -> Dict:
    """
    Get all the informations of a jurisprudence form the webpage and build the json.
    :param url:
    :return:
    """
    global counter
    source_code = get_source_code(url)
    tree = html.fromstring(source_code)
    title = tree.xpath("//div[@class='main-col']/h1[@class='main-title']/text()")
    juridiction = tree.xpath("//*[@id='main']/div/div/div[2]/div[1]/div[1]/h2/text()")
    rg_num = tree.xpath("//*[@id='main']/div/div/div[2]/div[1]/div[1]/ul/li[1]/text()")
    date = tree.xpath("//*[@id='main']/div/div/div[2]/div[1]/div[2]/div/text()")
    text = tree.xpath("//div[@class='content-page']/div[2]/text()")
    global counter
    with counter.get_lock():
        print(f"INFO: ID ({counter.value}) Current jurisprudence : {title}")
        counter.value += 1
        return build_json(title, juridiction, rg_num, date, text, counter.value)


def export_elasticsearch(documents) -> None:
    """
    Exporting a list of document to elasticsearch
    :param documents:
    :return:
    """
    print("INFO: Connection to Elasticsearch....")
    es = Elasticsearch(hosts=[{"host": "host.docker.internal", "port": 9200}])
    if not es.ping():
        print(f"INFO: Erreur de connexion")
        return 0
    print(f"INFO: Connected")
    print("INFO: Writting data to Elasticsearch, index: jurisprudence....")
    if not es.indices.exists("jurisprudence"):
        print("INFO: Index 'jurisprudence' not found.\nINFO: Creating index....")
        es.indices.create(index="jurisprudence")

    for doc in documents:
        es.index(index="jurisprudence", body=doc, id=doc['metadata']['properties']['id'])


def doit() -> None:
    """
    Main function
    :return:
    """
    domaine = "https://www.legifrance.gouv.fr"
    print("************************** STEP 1 **************************\n")
    print("INFO: Collecting all the urls....")
    links = get_all_jurisprudence_urls(domaine)
    print(f"\nINFO: Total number of urls: {len(links)}")

    print("\n\n\n************************** STEP 2 **************************\n")
    print("INFO: Collecting jurisprudence....")
    process = Pool(initargs=(counter, ))
    data = process.map(get_jurisprudence, links)
    process.close()
    process.join()
    print(f"\nINFO: Total number of jurisprudence : {len(data)}")
    print("\n\n\n************************** STEP 2 **************************\n")
    print(f"\nINFO: Exporting to parquet....")
    try:
        df = pd.DataFrame.from_records(data)
        df.to_parquet("./output/legifrance.parquet")
        print(f"\nINFO: Exporting to parquet.... OK")
    except:
        print("WARNING: ERROR, cannot write parquet.")
    print(f"\nINFO: Exporting to ElasticSearch....")
    try:
        export_elasticsearch(data)
        print(f"\nINFO: Exporting to ElasticSearch.... OK")
        print("To run ElasticSearch : http://localhost:9200")
        print("To run Kibana : http://localhost:5600")

    except:
        print("WARNING: ERROR, cannot export to Elasticsearch.")




if __name__ == '__main__':
    # Counter for documents id
    #counter = Value('i', 0)
    start = time.time()
    print(f"==============================================================================\n"
          f"||| Starting scrapping for legifrance\n"
          f"||| Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start))}\n"
          f"==============================================================================")
    doit()
    end_time = time.time()
    print(f"==============================================================================\n"
          f"||| Execution ended\n"
          f"||| End time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}\n"
          f"||| Total time: {end_time-start}\n"
          f"==============================================================================")
