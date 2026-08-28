from abc import ABC, abstractmethod


from scripts.cat.cats import Cat


class BaseCatFactory(ABC):
    @abstractmethod
    def create_cat(self, **kwargs) -> Cat:
        pass
