import os
import re
from time import perf_counter, sleep

import pandas as pd
from gazpacho import Soup
from selenium.webdriver import Firefox
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# from selenium.webdriver.firefox.options import Options

# create project directories
os.makedirs('data', exist_ok=True)
os.makedirs('screenshots', exist_ok=True)

# set timestamp
timestamp = f"{pd.Timestamp('today'):%Y-%m-%d %I-%M-%S %p}"

# create headless Firefox WebDriver instance
# driver = Firefox(executable_path='/usr/local/bin/geckodriver')


def create_webdriver():
    """Creates headless Firefox WebDriver instance."""
    # creates headless Firefox WebDriver
    # options = Options()
    # options.headless = True
    return Firefox(executable_path='/usr/local/bin/geckodriver')  # options=options)


def take_screenshot(driver):
    """Saves a screenshot of the current window in the 'screenshots' directory."""
    path = ''.join((
        './screenshots/', 'screenshot ', timestamp, '.png')
    )
    driver.save_screenshot(path)


def make_soup(driver):
    """Makes soup on raw html to enable parsing."""
    html = driver.page_source
    return Soup(html)


def load_url(driver, diamond_type: str):
    """Navigates to Brilliant Earth's diamonds search page."""
    base = 'https://www.brilliantearth.com/'
    natural_url = base + "/loose-diamonds/search/"
    lab_url = base + "lab-diamonds-search/"
    if diamond_type == 'natural':
        driver.get(natural_url)
    else:
        driver.get(lab_url)
    sleep(2)


def close_marketing_box(driver):
    """Closes the marketing box when first loading the page."""
    button = driver.find_element_by_class_name('sailthru-overlay-close')
    button.click()
    sleep(1)


def get_shapes(driver):
    """Returns a list of available shapes."""
    soup = make_soup(driver)
    a = soup.find('div', {'class': 'ir246-product-shape-wrap'})
    b = a.find('a')
    return [shape.text.lower() for shape in b]


def select_shapes(driver, ix: int):
    """Selects diamond shapes on the first pass."""
    if ix == 0:
        shapes = get_shapes(driver)
        for shape in shapes:
            shape_element = '-'.join((shape, 'details'))
            driver.find_element_by_class_name(shape_element).click()
        sleep(3)
    else:
        pass


def perform_actions(driver, element: str, box_input: str):
    """Takes actions on input box elements."""
    # find element
    driver.find_element_by_id(element)

    actions = ActionChains(driver)
    actions.move_to_element(element)
    actions.click()
    actions.send_keys(Keys.BACKSPACE * 8)
    actions.send_keys(box_input + Keys.RETURN)
    actions.perform()
    sleep(1)

    # click header
    header = driver.find_element_by_tag_name('h1')
    header.click()


def set_max_price(driver):
    """Re-adjusts the max price box in the results table."""
    perform_actions(driver, 'max_price_display', '50000')


def set_max_carat(driver):
    """Re-adjusts the carat box in the results table."""
    return perform_actions(driver, 'max_carat_display', '50')


def table_scroll(driver):
    """Scrolls down the diamond data table."""
    base_script = "document.querySelector('#diamond_search_wrapper').scrollTop="

    # scroll by 3000 pixels, 12 times
    n_scroll = 12
    for ix, _ in enumerate(range(n_scroll), start=1):
        if ix == 1:
            p = str(3000)
        else:
            p = str(ix * int(3000))

        scroll_by = ''.join((base_script, p))
        driver.execute_script(scroll_by)
        sleep(2)


def create_dataframe(driver):
    """Returns pandas DataFrame from diamonds HTML page."""
    html = driver.page_source
    dfs = pd.read_html(html)

    # return the second table which contains target data
    return dfs[1]


def clean_diamonds_df(df):
    """"Returns clean diamonds pandas DataFrame."""
    # assert df.shape[1] == 10, "Number of columns needs to be 10."

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


def get_url_list(driver):
    """Returns list of html containing url sub-directories."""
    soup = make_soup(driver)

    # find html with diamond url page and return it
    return soup.find('a', {'class': 'td-n2'})


def create_url_df(driver):
    """Returns DataFrame with diamond id and individual diamond urls."""

    url_list = get_url_list(driver)
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


def set_price(driver, max_price):
    """Filters diamonds results based on price range."""
    return perform_actions(driver, 'min_price_display', max_price)


def to_csv(df, diamond_type=''):
    """Writes a CSV file in the 'data' directory."""
    path = ''.join(('./data/', timestamp, ' ', diamond_type, '.csv'))
    df.to_csv(path, index=False)


def get_max_price(df):
    """Returns the max 'price' in the DataFrame."""
    return df['price'].max()


def get_last_id(df):
    """Returns the 'id' of the last row in the DataFrame."""
    return df['id'].iloc[-1]


def main():
    """Run script."""
    print('Attempting to scrape diamonds data. This could take a while...')
    tic = perf_counter()
    driver = create_webdriver()
    driver.maximize_window()  # temp
    diamond_type = ['natural', 'lab']
    final_df = pd.DataFrame()

    try:
        for ix, dt in enumerate(diamond_type):
            # first scrape attempt
            load_url(driver, dt)
            close_marketing_box(driver)
            select_shapes(driver, ix)
            set_max_price(driver)
            table_scroll(driver)

            # create and clean DataFrame to append to
            diamonds_df = clean_diamonds_df(create_dataframe(driver))
            url_df = create_url_df(driver)
            df1 = merge_dfs(url_df, diamonds_df)

            # get max price & id from the DataFrame to filter diamonds for next scrape
            prev_max_price = get_max_price(df1)
            prev_last_id = get_last_id(df1)

            # scrape remaining rows by iterating the price range
            while True:
                # scrape diamonds table
                set_price(driver, prev_max_price)
                table_scroll(driver)

                # create and clean DataFrame, and append to 'df1' (created in first pass)
                diamonds_df = clean_diamonds_df(create_dataframe(driver))
                url_df = create_url_df(driver)
                merged_df = merge_dfs(url_df, diamonds_df)
                df1 = df1.append(merged_df)

                # set current max price & id using the last row scraped
                current_max_price = get_max_price(df1)
                current_last_id = get_last_id(df1)

                # check if price and id of the last row have been scraped
                if current_max_price != prev_max_price and \
                        current_last_id != prev_last_id:
                    prev_max_price = current_max_price
                    prev_last_id = current_last_id

                # else there are no new diamond results, export DataFrame
                else:
                    df1['type'] = dt
                    final_df = final_df.append(df1)
                    to_csv(final_df, dt)
                    break
        else:
            # to_csv(final_df)
            pass
    except Exception as e:
        print(e)
        take_screenshot(driver)
        # driver.quit()
    finally:
        # driver.quit()
        toc = perf_counter()
        duration = (toc - tic) / 60
        print(f"Finished in {duration:0.1f} minutes")


if __name__ == '__main__':
    main()
