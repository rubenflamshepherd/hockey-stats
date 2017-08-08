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


class NHL_Draft:

    def __init__(self, year, team, draft_round, overall):
        self.year = year
        self.team = team
        self.round = draft_round
        self.overall = overall

    def __str__(self):
        return "NHL " + self.year + " " + self.team + " " + self.round + " " + self.overall

class CHL_Draft(NHL_Draft):

    def __init__(self, year, league, team, draft_round, overall):
        super().__init__(year, team, draft_round, overall)
        self.league = league


    def __str__(self):
        return self.league + " " + self.year + " " + self.team + " " + self.round + " " + self.overall

class PlayerPage:
    """Object representing a single player. season_type = '2' for regular season or '3' for playoffs
    """
    def __init__(self, id_, league, name, num, pos, height, weight, birthdate, birthplace, shoots, nhl_draft, chl_draft):
        self.id = id_
        self.league = league
        self.name = name
        self.num = num
        self.pos = pos
        self.height = height
        self.weight = weight
        self.birthdate = birthdate
        self.birthplace = birthplace
        self.shoots = shoots
        self.nhl_draft = nhl_draft
        self.chl_draft = chl_draft

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
    c.execute('DROP TABLE IF EXISTS chl_player_pages')
    c.execute('''CREATE TABLE chl_player_pages
                 (
                 id TEXT, league TEXT, name TEXT, num TEXT, pos TEXT, height REAL, weight REAL, birth_date TEXT,
                 birth_city TEXT, birth_state TEXT, birth_country TEXT, shoots TEXT,
                 nhl_draft_year TEXT, nhl_draft_team TEXT, nhl_draft_round TEXT, nhl_draft_overall TEXT,
                 chl_draft_year TEXT, chl_draft_league, chl_draft_team TEXT, chl_draft_round TEXT,
                 chl_draft_overall TEXT,
                 PRIMARY KEY (id, league)
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
        player_page.id, player_page.league, player_page.name, player_page.num, player_page.pos, player_page.height,
        player_page.weight, str(player_page.birth_date), player_page.birthplace.city, player_page.birthplace.state,
        player_page.birthplace.country, player_page.shoots,
        player_page.nhl_draft.year, player_page.nhl_draft.team, player_page.nhl_draft.round,
        player_page.nhl_draft.overall,
        player_page.chl_draft.year, player_page.chl_draft.league, player_page.chl_draft.team,
        player_page.chl_draft.round, player_page.chl_draft.overall
    )
    db_cursor.execute(
        'INSERT INTO chl_player_pages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        temp_player_page)
    print(" saved")


def _player_exists(db_cursor, player_id):
    """Return whether or not the given player has already been grabbed

    :param db_cursor: database cursor
    :param player_id:  int
    :return: bool
    """
    checker = db_cursor.execute(
        'SELECT * FROM chl_player_pages WHERE id=?',
        (player_id,))
    if len(checker.fetchmany()) == 0:
        return False
    else:  # len(checker) >= 1
        print(" already saved!")
        return True


def _ft_to_cm(ft, inches):
    total_inches = ft * 12 + inches
    total_cm = total_inches * 2.54
    return total_cm


def _parse_birthdate(birth_str_raw):
    birth_str_raw = birth_str_raw.strip()
    birth_str = birth_str_raw.split('-')
    year = int(birth_str[0])
    month = int(birth_str[1])
    day = int(birth_str[2])
    return datetime.date(year, month, day)


def _parse_birthplace(birthplace_str):
    state, country = None, None  # Default values
    birthplace_str = birthplace_str.strip()
    city, territory = birthplace_str.split(', ')
    if territory.isupper():
        state = territory
    else:
        country = territory
    return Birthplace(city, state, country)


def _parse_nums(str_with_nums):
    nums = ''
    for item in str_with_nums:
        if item.isdigit():
            nums += item
    return nums

def _parse_height(height_raw):
    """

    :param height_raw: str
    :return: str
    """
    feet_raw, inches_raw = height_raw.split('.')
    feet = int(feet_raw.strip())
    inches = int(inches_raw.strip())
    return feet, inches


def _parse_draft(draft_str, league=None):
    draft_list = draft_str.split()
    team = draft_list[2]
    year = draft_list[3].strip('(').strip(')')
    draft_round = draft_list[-2]
    overall = _parse_nums(draft_list[-1])
    if league == None:
        return NHL_Draft(year, team, draft_round, overall)
    else:
        return CHL_Draft(year, league, team, draft_round, overall)


def _parse_primary_element(primary_element):
    """
    :param primary_element: WebDriver
    :return: str, str, str
    """
    name = primary_element.find_element_by_class_name('player-profile-info__full-name')
    num_raw = primary_element.find_element_by_class_name('player-profile-info__number')
    num = _parse_nums(num_raw.text)
    pos = primary_element.find_element_by_class_name('player-profile-info__position')
    return name, num, pos

def _parse_secondary_element(secondary_element, league):
    """

    :param secondary_elements:
    :return: float, float, datetime, BirthPlace, str,
    """
    nhl_draft, chl_draft = NHL_Draft(None, None, None, None), CHL_Draft(None, None, None, None, None) #  Default values
    elements_raw = secondary_element.find_elements_by_class_name('player-profile-info')
    for item_raw in elements_raw:
        contents = item_raw.text.split(':')
        header, stat = contents[0], contents[1]
        print(header)
        if 'Shoots' in header:
            shoots = stat.strip()
        elif 'Height' in header:
            feet, inches = _parse_height(stat)
            height = _ft_to_cm(feet, inches)
        elif 'Weight' in header:
            weight_raw = stat.split(':')
            weight = int(stat[1].strip()) * 0.453592
        elif 'Birthdate' in header:
            birthdate = _parse_birthdate(stat)
        elif 'Hometown' in header:
            birthplace = _parse_birthplace(stat)
        elif 'NHL - ' in header:
            if nhl_draft.year == None:
                nhl_draft = _parse_draft(stat)
            else:
                assert False, "player with birthdate {} has more than 1 nhl draft".format(birthdate)
        elif 'CHL - ' in header:
            if chl_draft.year == None:
                chl_draft = _parse_draft(stat, league)
            else:
                assert False, "player with birthdate {} has more than 1 chl draft".format(birthdate)
    return height, weight, birthdate, birthplace, shoots, nhl_draft, chl_draft



def _parse_player_page(league, url_prefix, id_, driver):
    """ Given a WebDriver <driver>, point the driver to a player page at url_prefix with <id_> and return the
     PlayerPage object.

    :param id_:
    :param driver:
    :return: PlayerPage
    """
    url_complete = url_prefix + "/players/" + id_

    driver.get(url_complete)
    # Get WebDriver containing info
    primary_element = driver.find_element_by_class_name('player-profile-primary')
    secondary_element = driver.find_element_by_class_name('player-profile-secondary')

    name, num, pos = _parse_primary_element(primary_element)
    height, weight, birthdate, birthplace, shoots, nhl_draft, chl_draft =\
        _parse_secondary_element(secondary_element, league)

    return PlayerPage(id_, league, name, num, pos, height, weight, birthdate, birthplace, shoots, nhl_draft, chl_draft)


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
    #save_player_pages(2479)
    driver = webdriver.Chrome(executable_path=os.path.join(os.getcwd(), "driver\chromedriver.exe"))
    temp_player = _parse_player_page('OHL', 'http://ontariohockeyleague.com', '1906', driver)
    driver.close()

