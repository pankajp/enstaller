from abc import ABCMeta, abstractmethod


class AbstractStore(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def connect(self, authentication=None):
        """Connect the client to the configured store

        Parameters
        ----------
        authentication: pair
            (username, password) pair
        """

    @property
    @abstractmethod
    def is_connected(self):
        """Return True if the store is connected, False otherwise."""

    @abstractmethod
    def info(self):
        """Return some info about the store (url, name, etc...)."""

    @abstractmethod
    def get(self, key):
        """Return both data and metadata of the given key.

        Parameters
        ----------
        key: str
            The key of the value to retrieve.
        """

    @abstractmethod
    def get_data(self, key):
        """Return the data associated to the given key."""

    @abstractmethod
    def get_metadata(self, key, select=None):
        """Return the data associated to the given key."""

    @abstractmethod
    def exists(self, key):
        """Returns True if the given key exists in the store."""

    @abstractmethod
    def query(self, select=None, **kwargs):
        """Query the store with the given parameters.

        Parameters
        -----------
        select:
        **kwargs:
            Pairs of (name, value) defining the query, e.g. {'type': 'egg'}
            will return all the values where metadata['type'] == 'egg'.

        Returns
        -------
        result: list, generator
            Iterator over pairs (key, metadata)
        """

    def query_keys(self, **kwargs):
        """Like query_keys, but returns only the keys."""
        return self.query(**kwargs).keys()
