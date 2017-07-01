import sqlite3
import os
import time
import datetime

from random import randint
from selenium import webdriver


class Birthplace:

    def __init__(self, city, state, country):
        self.city = city
        self.state = state
        self.country = country

    def __str__(self):
        return self.city + " " + str(self.state) + " " + self.country


class Draft:

    def __init__(self, year, team, draft_round, overall):
        self.year = year
        self.team = team
        self.round = draft_round
        self.overall = overall

    def __str__(self):
        return self.year + " " + self.team + " " + self.round + " " + self.overall


class PlayerPage:
    """Object representing a single player. season_type = '2' for regular season or '3' for playoffs
    """
    def __init__(self, id_, name, num, pos, height, weight, birth_date, birthplace, shoots, draft):
        self.id = id_
        self.name = name
        self.num = num
        self.pos = pos
        self.height = height
        self.weight = weight
        self.birth_date = birth_date
        self.birthplace = birthplace
        self.shoots = shoots
        self.draft = draft

    def __str__(self):
        return "{:<25}".format("|Name " + self.name) + \
               "{:<15}".format("|ID " + self.id) + \
               "{:<10}".format("|Pos " + self.pos) + \
               "{:<10}".format("|Born in  " + str(self.birthplace))


def _create_player_pages_table():
    """Utility function for creating/initializing the player_page table

    :return:
    """
    conn = sqlite3.connect('hockey-stats.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS player_pages')
    c.execute('''CREATE TABLE player_pages
                 (
                 id text PRIMARY KEY, name text, num text, pos text, height real, weight real, birth_date text,
                 birth_city text, birth_state text, birth_country text, shoots text,
                 draft_year text, draft_team text, draft_round text, draft_overall text
                 )
                 ''')
    conn.commit()
    conn.close()


def _save_player_page(db_cursor, player_page):
    """ Save a list of PlayerSeason objects to a database

    :param c: database cursor
    :param player_page: PlayerPage
    :return: None
    """
    temp_player_page = (
        player_page.id, player_page.name, player_page.num, player_page.pos, player_page.height, player_page.weight,
        str(player_page.birth_date), player_page.birthplace.city, player_page.birthplace.state,
        player_page.birthplace.country, player_page.shoots,
        player_page.draft.year, player_page.draft.team, player_page.draft.round, player_page.draft.overall
    )
    db_cursor.execute(
        'INSERT INTO player_pages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        temp_player_page)
    print(" saved")


def _player_exists(db_cursor, player_id):
    """Return whether or not the given player has already been grabbed

    :param db_cursor: database cursor
    :param player_id:  int
    :return: bool
    """
    checker = db_cursor.execute(
        'SELECT * FROM player_pages WHERE id=?',
        (player_id,))
    if len(checker.fetchmany()) == 0:
        return False
    else:  # len(checker) >= 1
        print(" already saved!")
        return True


def _ft_to_cm(item):
    feet_index = item.find("'")
    feet = int(item[feet_index-1])
    inches_index = item.find('"')
    inches = int(item[inches_index - 1])
    total_inches = feet*12 + inches
    total_cm = total_inches * 2.54
    return total_cm


def _parse_birth_date(birth_str_raw):
    month_to_int = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 'July': 7,
        'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    birth_str = birth_str_raw.split()
    month = month_to_int[birth_str[1]]
    day = int(birth_str[2].strip(","))
    year = int(birth_str[3])
    return datetime.date(year, month, day)


def _parse_birthplace(birthplace_str):
    label_removed = birthplace_str.split(':')
    birthplace_list = label_removed[1].split(',')
    city = birthplace_list[0].strip()
    country = birthplace_list[-1].strip()
    if len(birthplace_list) > 2:
        state = birthplace_list[1].strip(',')
    else:  # No state provided
        state = None
    return Birthplace(city, state, country)


def _parse_nums(str_with_nums):
    nums = ''
    for item in str_with_nums:
        if item.isdigit():
            nums += item
    return nums


def _parse_draft(draft_str):
    draft_list = draft_str.split()
    year = draft_list[1]
    team = draft_list[2].strip(',')
    draft_round = _parse_nums(draft_list[3])
    overall = _parse_nums(draft_list[-2])
    return Draft(year, team, draft_round, overall)


def _parse_player_page(id_, driver):
    """ Given a WebDriver <driver>, point the driver to a player page at nhl.com url with <id_> and return the
     PlayerPage object.

    :param id_:
    :param driver:
    :return: PlayerPage
    """
    url_frag = "https://www.nhl.com/player/"
    url_complete = url_frag + id_

    driver.get(url_complete)
    # Get WebDriver containing info
    name_num_element = driver.find_element_by_class_name('player-jumbotron-vitals__name-num')
    attributes_element = driver.find_element_by_class_name('player-jumbotron-vitals__attributes')
    bio_element = driver.find_elements_by_class_name('player-bio__item')

    # Parse info
    name_num_raw = name_num_element.text.split("|")
    name = name_num_raw[0].strip()
    try:
        num = name_num_raw[1].strip().strip("#")
    except IndexError:
        num = None

    height, pos, weight = None, None, None  # Default values
    attributes_raw = attributes_element.text.split(' | ')
    for item in attributes_raw:
        if item in ['C', 'D', 'LW', 'RW']:
            pos = item
        elif 'lb' in item:
            weight_raw = item.strip('lb').strip()
            weight = int(weight_raw) * 0.453592  # Convert to kgs
        elif "'" and '"' in item:
            height = _ft_to_cm(item)

    # Default values
    birth_date, shoots, = None, None
    birthplace = Birthplace(None, None, None)
    draft = Draft(None, None, None, None)

    for item in bio_element:
        if "Born:" in item.text:
            birth_date = _parse_birth_date(item.text)
        elif "Birthplace:" in item.text:
            birthplace = _parse_birthplace(item.text)
        elif "Shoots:" in item.text:
            shoots_raw = item.text.split()
            shoots = shoots_raw[1].strip()
        elif "Draft" in item.text:
            draft = _parse_draft(item.text)

    return PlayerPage(id_, name, num, pos, height, weight, birth_date, birthplace, shoots, draft)


def save_player_pages(cap):
    driver = webdriver.Chrome(executable_path=os.path.join(os.getcwd(), "driver\chromedriver.exe"))
    conn = sqlite3.connect('hockey-stats.db')
    c = conn.cursor()
    c.execute(
        'SELECT * FROM player_seasons')
    all_seasons = c.fetchall()
    num_seasons = len(all_seasons)

    start_time = time.time()
    page_counter = 0

    counter = 0
    while counter < cap and counter < num_seasons:
        curr_player_season = all_seasons[counter]
        curr_player_id = curr_player_season[0]
        curr_player_name = curr_player_season[1]
        '{0: <.40}'.format('Examining ' + curr_player_id + " " + curr_player_name)
        print('{0:.<40}'.format('Examining ' + curr_player_id + " " + curr_player_name), end='')
        if not _player_exists(c, curr_player_id):
            temp_player_page = _parse_player_page(curr_player_id, driver)
            _save_player_page(c, temp_player_page)
            page_counter += 1
            conn.commit()
            time.sleep(randint(1, 5))
        counter += 1


    total_time = time.time() - start_time
    if page_counter == 0:
        time_per_page = 0
    else:
        time_per_page = total_time/page_counter
    print("That took " + str(total_time) + " seconds")
    print(str(page_counter) + " pages saved. " + str(time_per_page) + " seconds per page")

    driver.close()
    conn.close()

if __name__ == '__main__':
    '''
    driver = webdriver.Chrome(executable_path=os.path.join(os.getcwd(), "driver\chromedriver.exe"))
    conn = sqlite3.connect('hockey-stats.db')
    c = conn.cursor()
    temp_player = _parse_player_page('8471215', driver)
    _save_player_page(c, temp_player)
    conn.commit()
    conn.close()
    driver.close()
    '''
    #_create_player_pages_table()
    save_player_pages(65000)
