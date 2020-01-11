from bs4 import BeautifulSoup as BS
import requests
import sys
import enum
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from typing import List, Tuple, Union, Sequence, Optional, Dict
sys.path.insert(0, 'e:\\PycharmProjects\\')
from addc import login

Date_Str = Union[datetime, bool]
Uncomp = Sequence[List]
# zapis = "zápis na tréning."
zapis = "zápis"
p_multi = "multi"
p_other = "other"
multi = "uplatnenie multisport"
odpis = "odpis"
pump = "pump"
attack = "attack"
grit = "grit"
cx = "cx"
combat = "combat"
kruhac = "kruh"
# odpis = "odpis z tréningu."


class Months(enum.Enum):
    January = 1
    February = 2
    March = 3
    April = 4
    May = 5
    June = 6
    July = 7
    August = 8
    September = 9
    October = 10
    November = 11
    December = 12


class DataOrg:
    """
    Data organized by List[Dict]
    """
    def __init__(self, sign: List[Dict], mult: List[Dict],
                 puss: List[Dict], other: List[Dict]) -> None:
        self.sign_dict = sign
        self.mult_dict = mult
        self.puss_dict = puss
        self.oth_dict = other
        self.find_multi_compens(self.sign_dict, self.mult_dict)
        self.find_multi_compens(self.sign_dict, self.puss_dict)

    @staticmethod
    def is_datebetween(date1, sign_date, hour_n1, hour_n2):
        """
        Checks if date1 is in range at least 1 hour before sign date
        :param date1: date pipped at reception
        :param sign_date: date of training
        :return: True, False or None if there is no sigh date
        """
        num = 1  # number of hours
        if sign_date is not None:
            h1 = sign_date.hour
            date2 = sign_date
            date2 -= timedelta(hours=hour_n1)
            date3 = sign_date
            date3 += timedelta(hours=hour_n2)
            if date2 <= date1 <= date3:
                return True
            else:
                return False
        else:
            return None

    def find_multi_compens(self, sign, diff):
        """
        Find multisport compenstation in sign_dict.
        If found change compensation to normal, in mult dict change item to ignored: True
        """
        counter = 0
        for item_s in sign:
            for item_m in diff:
                if (not item_m["ignored"]) and (item_s["compensated"] is None) and \
                   (item_m["tr_type"] == item_s["tr_type"]):
                    if item_m["pay"] == p_multi:
                        if self.is_datebetween(item_m["date"], item_s["assign_date"], 5, 48):
                            item_s["compensated"] = "normal"
                            item_m["ignored"] = True
                            item_m["assign_date"] = item_s["assign_date"]
                            counter += 1
                    elif item_m["pay"] == odpis:
                        if self.is_datebetween(item_m["date"], item_s["assign_date"], 100, 1):
                            item_s["compensated"] = "pussy"
                            item_m["ignored"] = True
                            item_m["assign_date"] = item_s["assign_date"]
                            counter += 1
        print(f"All found? {len(diff)} == {counter}")

    def print_status(self):
        """
        printing the current status of the trainings
        """
        print("=============================")
        print("Trainings statistics: ")
        print()
        sum_overall = 0.0
        sum_month = 0.0
        counter_month = 0
        counter_all = 0
        for idx, item in enumerate(reversed(self.sign_dict)):
            if idx == 0:
                print(Months(item["assign_date"].month).name)
                old_m = Months(item["assign_date"].month)
            else:
                if self.check_month(Months(item["assign_date"].month), old_m):
                    print(f"Summary for {old_m.name}: number of trainings {counter_month}, "
                          f"money spend {round(abs(sum_month), 2)}")
                    print()
                    print(Months(item["assign_date"].month).name)
                    sum_month = 0
                    counter_month = 0
                old_m = Months(item["assign_date"].month)
            stat = ""
            mon_str = ""
            if item["compensated"] == "normal":
                stat = "trained"
                sum_overall += item["money"]
                sum_month += item["money"]
                mon_str = str(item["money"])
                counter_month += 1
                counter_all += 1
            elif item["compensated"] == "pussy":
                stat = "pussied away"
            else:
                stat = "UNCOMPANSATED"
                mon_str = str(item["money"])
            print("{:3d}   {:25} {:10} {:15} {:7}".format(idx + 1, str(item["assign_date"]),
                                                     item["tr_type"], stat, mon_str))

        print(f"Summary for {old_m.name} so far: number of trainings {counter_month}, "
              f"money spend {round(abs(sum_month), 2)}")
        print(f"Overall Summary: number of trainings {counter_all}, "
              f"money spend {round(abs(sum_overall), 2)}")

    @staticmethod
    def check_month(new, old):
        """
        Checks if month changed. Prints it if yes
        """
        if new != old:
            return True
        else:
            return False


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


def ex_identifier(train: str) -> str:
    """
    makes a training string
    :param train:
    :return:
    """
    res = ""
    if pump in train:
        res += pump
    if attack in train:
        res += attack
    if grit in train:
        res += grit
    if kruhac in train:
        res += "kruhac"
    if cx in train:
        res += cx
    if combat in train:
        res += combat
    return res


def url_parse(url: str) -> Tuple[List[Tuple[datetime, float, str, str]], List[Dict]]:
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
        data_dict: List[Dict] = list()
        for item in tr:
            td = item.find_all('td')
            dd = date_conv(td[0].text, td[1].text)
            data.append((dd, float(td[2].text), td[3].text, td[4].text))
            data_dict.append({"date": dd, "money": float(td[2].text), "tr_type": td[3].text.lower(),
                              "mark": td[4].text.lower(), "compensated": None, "assign_date": None,
                              "ignored": False, "pay": None})
        return data, data_dict


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


def trainings(data_dict: List[Dict]) -> DataOrg:
    """
    Selects only Zapis on trening items and returns list. It also deletes these items from the original List{Dict}
    :param data_dict: All activities in the Addiction
    :return: Only assign to trening
    """
    sign_dict: List[Dict] = list()
    multi_dict: List[Dict] = list()
    puss_dict: List[Dict] = list()
    other_dict: List[Dict] = list()
    for idx, item in enumerate(data_dict):
        # if zap in item["mark"]:
        if zapis in item["mark"]:
            item["assign_date"] = date_extractor(item["tr_type"])
            sign_dict.append(item)
        elif item["mark"] == multi:
            item["pay"] = p_multi
            multi_dict.append(item)
        elif odpis in item["mark"]:
            item["pay"] = odpis
            puss_dict.append(item)
        else:
            item["pay"] = p_other
            other_dict.append(item)
        item["tr_type"] = ex_identifier(item["tr_type"])
            # data_dict.remove(item)
    cl_dict = DataOrg(sign_dict, multi_dict, puss_dict, other_dict)
    print(f"Signs = {len(sign_dict)}; multi = {len(multi_dict)}; puss = {len(puss_dict)}; other = {len(other_dict)}")
    return cl_dict


def find_compens(data_dict: List[Dict], sign_dict: List[Dict]) -> None:
    """
    Updates the signing list with the parameter whatever the training was compensated
    :param sign_dict:
    :return:
    """
    for item in sign_dict:
        if item:
            pass


if __name__ == "__main__":
    print("=======================================")
    print("Whole history of trainings is below:")
    print()
    url = "https://trening.addictionclub.sk/historia-pohybov"
    data, data_dict = url_parse(url)
    cl_dict = trainings(data_dict)
    print(Months(1).name)
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
    # print("=============================")
    # print("Uncompensated trainings: ")
    # print()
    # u_list = uncompensate(data)
    cl_dict.print_status()
    input("input any key to quit: ")
