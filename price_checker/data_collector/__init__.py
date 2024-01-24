from abc import ABC, abstractmethod
from datetime import datetime

class Scrapper(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def collect_product_types(self):
        pass

    @abstractmethod
    def collect_product_list(self):
        pass

    @abstractmethod
    def save_stats(self):
        pass

    def datetimer(self):
        s = str(datetime.now())
        s = s.replace(' ', '_').replace(':', '')
        s = s[:-5]
        return s
