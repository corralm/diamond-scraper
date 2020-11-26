#!/usr/bin/env python
# coding: utf-8

import os
import re
from time import perf_counter, sleep

import pandas as pd
from gazpacho import Soup
from selenium.webdriver import Firefox
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options


# create project directories
os.makedirs('data', exist_ok=True)
os.makedirs('screenshots', exist_ok=True)

# set timestamp
timestamp = f"{pd.Timestamp('today'):%Y-%m-%d %I-%M-%S %p}"

# set price range
my_min = '1300'
my_max = '1799'

# creates headless Firefox WebDriver
options = Options()
options.headless = True
driver = Firefox(executable_path='/usr/local/bin/geckodriver', options=options)


def take_screenshot():
    """Saves a screenshot of the current window in the 'screenshots' directory."""
    path = ''.join((
        './screenshots/', 'screenshot ', timestamp, '.png')
    )
    driver.save_screenshot(path)


def make_soup():
    """Makes soup on raw html to enable parsing."""
    html = driver.page_source
    return Soup(html)


def load_url():
    """Navigates to Brilliant Earth's diamonds search page."""
    base = 'https://www.brilliantearth.com/'
    # natural_url = base + "/loose-diamonds/search/"
    lab_url = base + "lab-diamonds-search/"
    driver.get(lab_url)
    sleep(2)


def close_marketing_box():
    """Closes the marketing box when first loading the page."""
    button = driver.find_element_by_class_name('sailthru-overlay-close')
    button.click()
    sleep(1)


def get_shapes():
    """Returns a list of available shapes."""
    soup = make_soup()
    a = soup.find('div', {'class': 'ir246-product-shape-wrap'})
    b = a.find('a')
    return [shape.text for shape in b]


def select_shapes():
    """Selects diamond shapes – Cushion, Princess, Emerald."""

    # deselect Round (selected by default)
    driver.find_element_by_xpath('/html/body/div[6]/div[2]/div[1]/div[1]/div/div[2]/div/ul/li[1]/a/span').click()

    # Cushion
    driver.find_element_by_xpath('/html/body/div[6]/div[2]/div[1]/div[1]/div/div[2]/div/ul/li[3]/a/span').click()

    # Princess
    driver.find_element_by_xpath('/html/body/div[6]/div[2]/div[1]/div[1]/div/div[2]/div/ul/li[5]/a/span').click()

    # Emerald
    driver.find_element_by_xpath('/html/body/div[6]/div[2]/div[1]/div[1]/div/div[2]/div/ul/li[6]/a/span').click()


def set_price():
    """Filters diamond results by price range."""

    # find min and max price elements
    min_price = driver.find_element_by_id('min_price_display')
    max_price = driver.find_element_by_id('max_price_display')

    # replace current min price with my min price
    actions = ActionChains(driver)
    actions.move_to_element(min_price)
    actions.click()
    actions.send_keys(Keys.BACKSPACE * 4)
    actions.send_keys(my_min + Keys.RETURN)
    actions.perform()
    sleep(1)

    # click header
    header = driver.find_element_by_tag_name('h1')
    header.click()

    # replace current max price with my max price
    actions.move_to_element(max_price)
    actions.click()
    actions.send_keys(Keys.BACKSPACE * 6)
    actions.send_keys(my_max + Keys.RETURN)
    actions.perform()
    sleep(5)


def table_scroll():
    """Scrolls down the diamond data table."""
    # scroll to the bottom of the page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    base_script = "document.querySelector('#diamond_search_wrapper').scrollTop="
    
    for ix, _ in enumerate(range(12), start=2):
        if ix == 2:
            p = str(3000)
        else:
            p = str(ix * int(3000))
        
        scroll_by = ''.join((base_script, p))
        driver.execute_script(scroll_by)
        sleep(2)


def create_dataframe():
    """Returns pandas DataFrame from diamonds HTML page."""
    html = driver.page_source
    dfs = pd.read_html(html)

    # return the second table which contains target data
    return dfs[1]


def clean_diamonds_df(df):
    """"Returns clean diamonds pandas DataFrame."""
    assert df.shape[0] != 1001, "Max limit of rows met (1000). Try shortening price range."
    assert df.shape[1] == 10, "Number of columns needs to be 10."

    # rename columns
    df.columns = ['0', 'shape', 'price', 'carat', 'cut', 'color', 'clarity',
                  'report', 'compare', 'checkbox']
    
    # drop blank rows & useless columns
    df = (df.dropna(axis=0, how='all', thresh=3)
            .drop(columns=['0', 'compare', 'checkbox']))
    
    # remove '$' and commas, and convert float to int
    df['price'] = df['price'].replace({'\\$': '', ',': ''}, regex=True)
    df['price'] = pd.to_numeric(df['price'], downcast='integer')

    # add 'date_fetched' column
    df['date_fetched'] = timestamp

    return df


def get_url_list():
    """Returns list of html containing url sub-directories."""
    soup = make_soup()

    # find html with diamond url page and return it
    return soup.find('a', {'class': 'td-n2'})


def create_url_df():
    """Returns DataFrame with diamond id and individual diamond urls."""

    url_list = get_url_list()
    url_dict = {}
    base = 'https://www.brilliantearth.com/'

    # extract url sub-directory & id and add to dict
    for ix, i in enumerate(url_list[:-1], start=1):
        href = i.attrs.get('href')
        d_id = re.findall("([0-9]+)", href)[0]

        # add diamond id and url to dict
        url_dict[ix] = {'id': d_id, 'url': base + href}

    # construct pandas DataFrame from url_dict and return it
    return pd.DataFrame.from_dict(url_dict, orient='index')


def merge_dfs(left_df, right_df):
    """Merges 'df' and 'url_df' and returns merged DataFrame."""
    return pd.merge(left_df, right_df, left_index=True, right_index=True)


def to_csv(df):
    """Writes a CSV file in the 'data' directory."""
    path = ''.join(('./data/', timestamp, ' ', my_min, '-', my_max, '.csv'))
    df.to_csv(path, index=False)


def main():
    """Run script."""
    print('Initiating scraper. It should take less than 1 minute...')
    tic = perf_counter()

    try:
        load_url()
        close_marketing_box()
        select_shapes()
        set_price()
        table_scroll()
        diamonds_df = clean_diamonds_df(create_dataframe())
        url_df = create_url_df()
        final_df = merge_dfs(url_df, diamonds_df)
        to_csv(final_df)
    except Exception as e:
        print(e)
        take_screenshot()
    finally:
        driver.quit()
        toc = perf_counter()
        print(f"Finished in {toc - tic:0.1f} seconds")


if __name__ == '__main__':
    main()
