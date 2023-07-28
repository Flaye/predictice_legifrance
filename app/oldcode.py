def get_source_code(url: str) -> str:
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