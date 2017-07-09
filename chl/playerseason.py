import sqlite3
import os
import time
import pickle

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


class PlayerSeason:
    """Object representing a single players season. season_type = '2' for regular season or '3' for playoffs
    """

    def __init__(
            self, league, id_, num, active, rookie, name, year, season_name, team, pos, gp, goals, assists,
            points, plus_minus, pim, ppg, ppa, shg, sha, s,
            gwg, otg, first_g, insurance_g,
            sho_gp, sho_g, sho_att, sho_wg, sho_per,
            fo_att, fow, fow_per, p_g, pim_g):
        self.league = league
        self.id = id_
        self.num = num
        self.active = active
        self.rookie = rookie
        self.name = name  # Of player
        self.year = year
        self.season_name = season_name  # now a str because many types exist between ohl, whl, qmjhl
        self.team = team
        self.pos = pos
        self.gp = gp
        self.goals = goals
        self.assists = assists
        self.points = points
        self.plus_minus = plus_minus
        self.pim = pim
        self.ppg = ppg
        self.ppa = ppa
        self.shg = shg
        self.sha = sha
        self.s = s
        self.gwg = gwg
        self.otg = otg
        self.first_g = first_g
        self.insurance_g = insurance_g
        self.sho_gp = sho_gp
        self.sho_g = sho_g
        self.sho_att = sho_att
        self.sho_wg = sho_wg  # shootout winning goals
        self.sho_per = sho_per
        self.fo_att = fo_att
        self.fow = fow
        self.fow_per = fow_per
        self.p_g = p_g  # points per game
        self.pim_g = pim_g  # penalties in minutes per game

    def __str__(self):
        return "{:<25}".format("|Name " + self.name) + \
               "{:<15}".format("|ID " + self.id) + \
               "{:<10}".format("|" + self.season_name) + \
               "{:<15}".format("|Team " + self.team) + \
               "{:<10}".format("|Pos " + self.pos) + \
               "{:<10}".format("|GP " + str(self.gp))


def _parse_player(league, season_year, season_name, stats_list):
    """ Return a PlayerSeason object given a list of WebDrivers (stats_list) representing of their statistics

    :param season_year: str
    :param season_name: str
    :param stats_list: [WebDriver]
    :return: PlayerSeason
    """
    pos = stats_list[1].text
    num = stats_list[2].text
    active = stats_list[3].text
    if stats_list[4].text == '*':
        rookie = True
    else:
        rookie = False
    name_raw = stats_list[5].text.split(',')
    name = name_raw[1] + " " + name_raw[0]
    id_ = _parse_id(stats_list[5])
    team = stats_list[6].text

    try:
        gp = int(stats_list[7].text)
    except ValueError:
        gp = None
    try:
        goals = int(stats_list[8].text)
    except ValueError:
        goals = None
    try:
        assists = int(stats_list[9].text)
    except ValueError:
        assists = None
    try:
        points = int(stats_list[10].text)
    except ValueError:
        points = None
    try:
        plus_minus = int(stats_list[11].text)
    except ValueError:
        plus_minus = None
    try:
        pim = int(stats_list[12].text)
    except ValueError:
        pim = None
    try:
        ppg = int(stats_list[13].text)
    except ValueError:
        ppg = None
    try:
        ppa = int(stats_list[14].text)
    except ValueError:
        ppa = None
    try:
        shg = int(stats_list[15].text)
    except ValueError:
        shg = None
    try:
        sha = int(stats_list[16].text)
    except ValueError:
        sha = None
    try:
        s = int(stats_list[17].text)
    except ValueError:
        s = None
    try:
        gwg = int(stats_list[18].text)
    except ValueError:
        gwg = None
    try:
        otg = int(stats_list[19].text)
    except ValueError:
        otg = None
    try:
        first_g = int(stats_list[20].text)
    except ValueError:
        first_g = None
    try:
        insurance_g = int(stats_list[21].text)
    except ValueError:
        insurance_g = None
    try:
        sho_gp = int(stats_list[22].text)
    except ValueError:
        sho_gp = None
    try:
        sho_g = int(stats_list[23].text)
    except ValueError:
        sho_g = None
    try:
        sho_att = int(stats_list[24].text)
    except ValueError:
        sho_att = None
    try:
        sho_wg = int(stats_list[25].text)
    except ValueError:
        sho_wg = None
    try:
        sho_per = float(stats_list[26].text)
    except ValueError:
        sho_per = None
    try:
        fo_att = int(stats_list[27].text)
    except ValueError:
        fo_att = None
    try:
        fow = int(stats_list[28].text)
    except ValueError:
        fow = None
    try:
        fow_per = float(stats_list[29].text)
    except ValueError:
        fow_per = None
    try:
        p_g = float(stats_list[30].text)
    except ValueError:
        p_g = None
    try:
        pim_g = float(stats_list[31].text)
    except ValueError:
        pim_g = None
    return PlayerSeason(
        league, id_, num, active, rookie, name, season_year, season_name, team, pos, gp, goals, assists,
        points, plus_minus, pim, ppg, ppa, shg, sha, s,
        gwg, otg, first_g, insurance_g,
        sho_gp, sho_g, sho_att, sho_wg, sho_per,
        fo_att, fow, fow_per, p_g, pim_g
    )


def _parse_id(element):
    """Given an WebDriver <element> containing a url to a player page, parse and return the player id

    :param element:
    :return:
    """
    raw_element = element.find_element_by_tag_name('a')
    raw_id_ = raw_element.get_attribute('href').split('/')
    id_ = raw_id_[-1]
    return id_


def _create_player_seasons_table():
    """Utility function for creating/initializing the player_seasons table

    :return:
    """
    conn = sqlite3.connect('hockey-stats.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS chl_player_seasons')
    c.execute('''CREATE TABLE chl_player_seasons
                 (
                 league TEXT, id TEXT, num INTEGER, active TEXT, rookie BOOLEAN, name TEXT, year TEXT, season_name TEXT, team TEXT,
                 pos TEXT, gp INTEGER, goals INTEGER, assists INTEGER, points INTEGER, plus_minus INTEGER,
                 pim INTEGER, ppg INTEGER, ppa INTEGER, shg INTEGER, sha INTEGER, s INTEGER, gwg INTEGER, otg INTEGER,
                 first_g INTEGER, insurance_g INTEGER, sho_gp INTEGER, sho_g INTEGER, sho_att INTEGER,
                 sho_wg INTEGER, sho_per REAL, fo_att INTEGER, fow INTEGER, fow_per REAL, p_g REAL, pim_g REAL,
                 PRIMARY KEY (id, season_name)
                 )''')
    conn.commit()
    conn.close()


def _grab_single_page(league, season_year, season_type, driver):
    """Given a WebDriver <driver> that points to a nhl.com url with season statistics for players, parse and return a
      list of PlayerSeason objects representing the data on the single page.

    :param season_year: str
    :param season_type: str
    :param driver: WebDriver
    :return: [PlayerSeason}
    """
    player_seasons = []
    time.sleep(1)  # Let the user actually see something!
    test_element = driver.find_elements_by_class_name('standard-row')
    for temp_player in test_element:
        temp_stats = temp_player.find_elements_by_tag_name('td')
        temp_player_season = _parse_player(league, season_year, season_type, temp_stats)
        player_seasons.append(temp_player_season)
    return player_seasons


def _grab_player_seasons(season_year, season_type, driver):
    """ Given a WebDriver <driver>, point the driver to a nhl.com url with season statistics for players in
    year <season_year> and of <season_type> and navigate the driver to all possible pages and return the list of
     PlayerSeason objects representing the data from that season.

    :param season_year: str
    :param season_type: str
    :param driver: WebDriver
    :return: [PlayerSeason}
    """
    url_frag1 = "http://www.nhl.com/stats/player?aggregate=0&gameType="
    url_frag2 = "&report=skatersummary&pos=S&reportType=season&seasonFrom="
    url_frag3 = "&seasonTo="
    url_frag4 = "&filter=gamesPlayed,gte,1&sort=points,goals,gamesPlayed"
    url_complete = url_frag1 + season_type + url_frag2 + season_year + url_frag3 + season_year + url_frag4

    driver.get(url_complete)
    player_seasons = []
    curr_page = 1

    try:
        page_select_element = driver.find_element_by_class_name('pager-select')
        page_nums = page_select_element.text.split('\n')
        last_page = int(page_nums[-1])
        while curr_page <= last_page:
            player_seasons += _grab_single_page(season_year, season_type, driver)
            page_select_element.send_keys(Keys.ARROW_DOWN)
            curr_page += 1
    except selenium.common.exceptions.NoSuchElementException:  # Only 1 page of stats available
        player_seasons += _grab_single_page(season_year, season_type, driver)

    return player_seasons


def _season_exists(db_cursor, season_name):
    """Return whether or not the given season_year/season_type has already been grabbed

    :param db_cursor: database cursor
    :param season_year: str
    :param season_type:  '2' | '3' (regular season | playoffs)
    :return: bool
    """
    checker = db_cursor.execute(
        'SELECT * FROM chl_player_seasons WHERE season_type=?',
        (season_year, season_type))
    if len(checker.fetchmany()) == 0:
        return False
    else:  # len(checker) >= 1
        print(season_year + " season, type " + season_type + " already saved!")
        return True


def _parse_season_yr(season_yr_raw):
    """Given a season name, parse the year of the season and return it as YYYY-YYYY

    :param season_yr_raw: str
    :return: str
    """
    season_raw = season_yr_raw.split()[0]
    if len(season_raw)==4:
        previous_year_int = int(season_raw) - 1
    elif len(season_raw)==7:
        season_raw = season_raw.split('-')[0]
        previous_year_int = int(season_raw) - 1
    else:
        assert False, "Can not parse a season year from the {}".format(season_yr_raw)
    season_yr = str(previous_year_int) + "-" + season_raw
    return season_yr


def _grab_single_season(league, season_name, url_frag, chl_url, driver):
    """Visit a page of a chl city representing a single season and grab and return the data

    :param season_name: str
    :param url_frag: str
    :param chl_url: str
    :param driver: WebDriver
    :return: [PlayerSeason]
    """
    player_seasons = []
    url_complete = chl_url + '/stats/players/' + url_frag
    driver.get(url_complete)
    time.sleep(1)  # Let the user actually see something!
    # Expand view of player seasons until no more seasons are revealed
    button_load_element = driver.find_element_by_class_name('button-load')
    player_seasons_driver = driver.find_elements_by_class_name('table__tr')
    prev_num_players = 0
    curr_num_players = len(player_seasons_driver)
    while curr_num_players != prev_num_players:
        button_load_element.click()
        time.sleep(2)
        player_seasons_driver = driver.find_elements_by_class_name('table__tr')
        prev_num_players = curr_num_players
        curr_num_players = len(player_seasons_driver)
    player_seasons_driver = iter(player_seasons_driver)
    next(player_seasons_driver)  # Skip header row
    season_year = _parse_season_yr(season_name)
    # Parse player statistics and save create PlayerSeason objects
    for temp_row in player_seasons_driver:
        temp_stats = temp_row.find_elements_by_tag_name('td')
        temp_player_season = _parse_player(league, season_year, season_name, temp_stats)
        player_seasons.append(temp_player_season)
        print(temp_player_season)
    return player_seasons


def _get_seasons_attr(url, driver):
    '''List of tuples where the first element of each tuple if the name of the season, and the second is the url
    fragment required to visit that seasons stat page.

    :param url: string
    :param driver: WebDriver
    :return: [(str, str)}
    '''
    seasons_attr = []
    url_complete = url + '/stats/players/'
    driver.get(url_complete)
    season_types_menu = driver.find_element_by_class_name('full-scores__dropdown--season-select')
    season_types_raw = season_types_menu.find_elements_by_class_name('filter-group__dropdown-option')
    for item in season_types_raw:
        url_frag_raw = item.get_attribute('data-reactid')
        url_frag = url_frag_raw.split('$')[1]
        season_name = item.text
        seasons_attr.append((season_name, url_frag))
    return seasons_attr


def save_league_seasons(league, chl_url):
    """Visit chl url, grab player season statistics from every season, and save them in a database

    :param start_year:
    :param end_year:
    :return:
    """
    driver = webdriver.Chrome(executable_path=os.path.join(os.getcwd(), "driver\chromedriver.exe"))
    conn = sqlite3.connect('hockey-stats.db')
    c = conn.cursor()

    start_time = time.time()
    season_counter = 0

    seasons_attr = _get_seasons_attr(chl_url, driver)  # [(season name, url frag)]

    for item in seasons_attr:
        season_name, url_frag = item
        if not _season_exists(c, season_name):
            temp_single_season = _grab_single_season(league, season_name, url_frag, chl_url, driver)
            _save_player_seasons(c, temp_single_season)
            season_counter += 1
            conn.commit()
    driver.close()

    total_time = time.time() - start_time
    if season_counter == 0:
        time_per_season = 0
    else:
        time_per_season = total_time/season_counter
    print("That took " + str(total_time) + " seconds")
    print(str(season_counter) + " seasons saved. " + str(time_per_season) + " seconds per season")
    conn.commit()
    conn.close()


def _save_player_seasons(c, player_seasons):
    """ Save a list of PlayerSeason objects to a database

    :param c: database cursor
    :param player_seasons: [PlayerSeason]
    :return:
    """
    for player_season in player_seasons:
        temp_player = (
            player_season.league, player_season.id, player_season.num, player_season.active, player_season.rookie,
            player_season.name, player_season.year, player_season.season_name, player_season.team,
            player_season.pos, player_season.gp, player_season.goals, player_season.assists,
            player_season.points, player_season.plus_minus, player_season.pim, player_season.ppg, player_season.ppa,
            player_season.shg, player_season.sha, player_season.s, player_season.gwg, player_season.otg, player_season.first_g,
            player_season.insurance_g, player_season.sho_gp, player_season.sho_g, player_season.sho_att,
            player_season.sho_wg, player_season.sho_per, player_season.fo_att, player_season.fow,
            player_season.fow_per, player_season.p_g, player_season.pim_g
        )
        c.execute(
            'INSERT INTO chl_player_seasons VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            temp_player)
    print(player_season.season_name + " saved")


if __name__ == "__main__":
    # save_league_seasons("OHL", 'http://ontariohockeyleague.com')

    _create_player_seasons_table()

    driver = webdriver.Chrome(executable_path=os.path.join(os.getcwd(), "driver\chromedriver.exe"))
    temp_single_season = _grab_single_season('OHL', '2017 Playoffs', '58', 'http://ontariohockeyleague.com', driver)
    pickle.dump(temp_single_season, open("save.p", "wb"))
    driver.close()
    conn = sqlite3.connect('hockey-stats.db')
    c = conn.cursor()
    temp_single_season = pickle.load(open("save.p", "rb"))
    _save_player_seasons(c, temp_single_season)
    conn.commit()
    conn.close()
    