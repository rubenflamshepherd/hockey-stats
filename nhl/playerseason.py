import sqlite3
import os
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


class PlayerSeason:
    """Object representing a single players season. season_type = '2' for regular season or '3' for playoffs
    """

    def __init__(
            self, id_, name, year, season_type, team, pos, gp, goals, assists,
            points, plus_minus, pim, p_gp, ppg, ppp, shg,
            shp, gwg, otg, s, s_per, toi_gp, shifts_gp, fow_per):
        self.id = id_
        self.name = name
        self.year = year
        self.type = season_type  # '2' = regular season, '3' = playoffs
        self.team = team
        self.pos = pos
        self.gp = gp
        self.goals = goals
        self.assists = assists
        self.points = points
        self.plus_minus = plus_minus
        self.pim = pim
        self.p_gp = p_gp
        self.ppg = ppg
        self.ppp = ppp
        self.shg = shg
        self.shp = shp
        self.gwg = gwg
        self.otg = otg
        self.s = s
        self.s_per = s_per
        self.toi_gp = toi_gp
        self.shifts_gp = shifts_gp
        self.fow_per = fow_per

    def __str__(self):
        return "{:<25}".format("|Name " + self.name) + \
               "{:<15}".format("|ID " + self.id) + \
               "|Season " + self.year + \
               "{:<10}".format(", Type " + self.type) + \
               "{:<15}".format("|Team " + self.team) + \
               "{:<10}".format("|Pos " + self.pos) + \
               "{:<10}".format("|GP " + str(self.gp))


def _parse_player(season_year, season_type, stats_list):
    """ Return a PlayerSeason object given a list of WebDrivers (stats_list) representing of their statistics

    :param season_year: str
    :param season_type: str
    :param stats_list: [WebDriver]
    :return: PlayerSeason
    """
    name = stats_list[1].text
    id_ = _parse_id(stats_list[1])
    team = stats_list[3].text
    pos = stats_list[4].text
    try:
        gp = int(stats_list[5].text)
    except ValueError:
        gp = None
    try:
        goals = int(stats_list[6].text)
    except ValueError:
        goals = None
    try:
        assists = int(stats_list[7].text)
    except ValueError:
        assists = None
    try:
        points = int(stats_list[8].text)
    except ValueError:
        points = None
    try:
        plus_minus = int(stats_list[9].text)
    except ValueError:
        plus_minus = None
    try:
        pim = int(stats_list[10].text)
    except ValueError:
        pim = None
    try:
        p_gp = float(stats_list[11].text)
    except ValueError:
        p_gp = None
    try:
        ppg = int(stats_list[12].text)
    except ValueError:
        ppg = None
    try:
        ppp = int(stats_list[13].text)
    except ValueError:
        ppp = None
    try:
        shg = int(stats_list[14].text)
    except ValueError:
        shg = None
    try:
        shp = int(stats_list[15].text)
    except ValueError:
        shp = None
    try:
        gwg = int(stats_list[16].text)
    except ValueError:
        gwg = None
    try:
        otg = int(stats_list[17].text)
    except ValueError:
        otg = None
    try:
        s = int(stats_list[18].text)
    except ValueError:
        s = None
    try:
        s_per = float(stats_list[19].text)
    except ValueError:
        s_per = None
    if stats_list[20].text == '':
        toi_gp = None
    else:
        toi_gp = stats_list[20].text
    try:
        shifts_gp = float(stats_list[21].text)
    except ValueError:
        shifts_gp = None
    try:
        fow_per = float(stats_list[22].text)
    except ValueError:
        fow_per = None
    return PlayerSeason(
        id_, name, season_year, season_type, team, pos, gp, goals, assists, points, plus_minus, pim, p_gp, ppg, ppp,
        shg, shp, gwg, otg, s, s_per, toi_gp, shifts_gp, fow_per
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
    c.execute('DROP TABLE IF EXISTS player_seasons')
    c.execute('''CREATE TABLE player_seasons
                 (
                 id text, name text, year text, season_type text, team text,
                 pos text, gp integer, goals integer, assists integer, points integer, plus_minus integer,
                 pim integer, p_gp real, ppg integer, ppp integer, shg integer, shp integer, otg integer,
                 s integer, s_per real, toi_gp text, shifts_gp real, fow_per real,
                 PRIMARY KEY (id, year, season_type)
                 )''')
    conn.commit()
    conn.close()


def _create_seasons_list(start_year, end_year):
    """Return a list of strings representing season years between start_year and end_year.

    For example, if start_year = 1999 and end_year = 2000, [19992000, 20002001] returned

    :param start_year: int
    :param end_year: int
    :return: [str]
    """
    curr_year = start_year
    seasons_list = []

    while curr_year <= end_year:
        season_str = str(curr_year) + str(curr_year + 1)
        seasons_list.append(season_str)
        curr_year += 1

    return seasons_list


def _grab_single_page(season_year, season_type, driver):
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
        temp_player_season = _parse_player(season_year, season_type, temp_stats)
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


def _season_exists(db_cursor, season_year, season_type):
    """Return whether or not the given season_year/season_type has already been grabbed

    :param db_cursor: database cursor
    :param season_year: str
    :param season_type:  '2' | '3' (regular season | playoffs)
    :return: bool
    """
    checker = db_cursor.execute(
        'SELECT * FROM player_seasons WHERE year=? and season_type=?',
        (season_year, season_type))
    if len(checker.fetchmany()) == 0:
        return False
    else:  # len(checker) >= 1
        print(season_year + " season, type " + season_type + " already saved!")
        return True


def save_player_seasons(start_year, end_year):
    """Visit nhl.com, grab player season statistics from start_year to end_year, and save them in a database

    :param start_year:
    :param end_year:
    :return:
    """
    driver = webdriver.Chrome(executable_path=os.path.join(os.getcwd(), "driver\chromedriver.exe"))
    conn = sqlite3.connect('hockey-stats.db')
    c = conn.cursor()

    start_time = time.time()
    season_counter = 0

    year_list = _create_seasons_list(start_year, end_year)
    for year in year_list:
        if not _season_exists(c, year, '2'):
            temp_reg_seasons = _grab_player_seasons(year, '2', driver)
            _save_single_player_seasons(c, temp_reg_seasons)
            season_counter += 1
            conn.commit()
        if not _season_exists(c, year, '3'):
            temp_playoff_seasons = _grab_player_seasons(year, '3', driver)
            _save_single_player_seasons(c, temp_playoff_seasons)
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


def _save_single_player_seasons(c, player_seasons):
    """ Save a list of PlayerSeason objects to a database

    :param c: database cursor
    :param player_seasons: [PlayerSeason]
    :return:
    """
    for player_season in player_seasons:
        temp_player = (
            player_season.id, player_season.name, player_season.year, player_season.type, player_season.team,
            player_season.pos, player_season.gp, player_season.goals, player_season.assists, player_season.points,
            player_season.plus_minus, player_season.pim, player_season.p_gp, player_season.ppg, player_season.ppp,
            player_season.shg, player_season.shp, player_season.otg, player_season.s, player_season.s_per,
            player_season.toi_gp, player_season.shifts_gp, player_season.fow_per
        )
        c.execute(
            'INSERT INTO player_seasons VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            temp_player)
    print(player_season.year + " season, type " + player_season.type + " saved")


if __name__ == "__main__":
    save_player_seasons(1917, 2016)
