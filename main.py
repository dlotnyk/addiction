from bs4 import BeautifulSoup as BS
import requests
import sys
from datetime import datetime
from cryptography.fernet import Fernet
from typing import List, Tuple, Union, Sequence, Optional
sys.path.insert(0, 'e:\\PycharmProjects\\')
from addc import login

Date_Str = Union[datetime, bool]
Uncomp = Sequence[List]


def date_conv(date1: str, time1: str) -> datetime:
    """
    convert to datetime from two strings
    :param date1:
    :param time1:
    :return: datetime obj
    """
    date_str = date1 + " " + time1
    dd = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
    return dd


def date_extractor(tren_str: str) -> Date_Str:
    """
    extract date from a traning string if any. returns False otherwise
    :param tren_str:
    :return:
    """
    if tren_str.find("(") != -1:
        b1 = tren_str.split("(")[1]
        b2 = b1.split(")")[0]
        date_t = datetime.strptime(b2, "%d.%m.%Y %H:%M")
        return date_t
    else:
        return False


def neg_bal(data1: Tuple, balance: float, rev_list1: List) -> float:
    """
    Calculate a real balance
    :param data1: current date stats as tuple
    :param balance: current balance
    :param rev_list: the last days activity
    :return: real balance
    """
    rev_list = rev_list1.copy()
    if data1[1] <= 0:
        rev_list.append(data1)
    for item in rev_list:
        a_date = date_extractor(item[2])
        if a_date and compare_days(data1[0], a_date):  # type: ignore
            balance -= item[1]
    return balance


def compare_days(date1: datetime, date2: datetime) -> bool:
    """
    Compares two dates the current date and assigning date
    :param date1: current date
    :param date2: assigning date
    :return: date1 < date 2
    """
    return date1.date() < date2.date()


def url_parse(url: str) -> List[Tuple[datetime, float, str, str]]:
    """
    Parsing addiction club url
    :param url:
    :return: data
    """
    with open("key2.key", "rb") as f:
        key = f.read()
    ff = Fernet(key)
    password = ff.decrypt(login["pwd"])
    try:
        with requests.Session() as sess:
            sess.auth = (login["name"], password.decode())
            # sess.auth = (login["name"], "XXX")
            resp = sess.get(url)
    except requests.exceptions.TooManyRedirects:
        print("===============Wrong login or a password==================")
        raise
    else:
        soup = BS(resp.content, "html.parser")
        tbody = soup.find_all('tbody')
        tr = tbody[0].find_all('tr')
        data: List[Tuple[datetime, float, str, str]] = list()
        for item in tr:
            td = item.find_all('td')
            dd = date_conv(td[0].text, td[1].text)
            data.append((dd, float(td[2].text), td[3].text, td[4].text))
        return data


def uncompensate(m_list: List[Tuple[datetime, float, str, str]]) -> Uncomp:
    """
    try to find uncompensate training by MS card
    :param m_list:
    :return: list of trainings
    """
    u_list: List = list()
    idx = 0
    for item in reversed(m_list):
        a_date = date_extractor(item[2])
        if a_date:
            for item_2 in reversed(m_list):
                if (item_2[0].date() == a_date.date()) and (item_2[1] > 0): # type: ignore
                    print("{:3d}  {:50} is compensated".format(idx+1, item[2]))
                    idx += 1
                    break
            else:
                u_list.append(item[2])
                print("{:3d}  {:50} IS NOT COMPENSATED!!!!".format(idx+1, item[2]))
                idx += 1
    return u_list


if __name__ == "__main__":
    print("=======================================")
    print("Whole history of trainings is below:")
    print()
    url = "https://trening.addictionclub.sk/historia-pohybov"
    data = url_parse(url)
    balance: float = 0
    hypo: float = 0
    comp_list: List = list()
    print("{:20s} {:12s} {:12s} {:12s} {:10s}".format("Date", "Balance", "Sum", "act", "Item"))
    for item in reversed(data):
        balance += item[1]
        if comp_list:
            hypo = neg_bal(item, balance, comp_list)
        print("{:20s} {:10.2f} {:10.2f} {:10.2f} \'{}\'".format(str(item[0]), balance, hypo, item[1], item[2]))
        comp_list.append(item)
    print("=============================")
    print("Uncompensated trainings: ")
    print()
    u_list = uncompensate(data)
