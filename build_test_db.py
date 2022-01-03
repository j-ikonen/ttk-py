"""Rebuild a database 'test.db' for testing the app."""
import os

from db.database import Database


def build_test_db():
    """(Re)build a test db with some values."""

    try:
        os.remove("test")
    except FileNotFoundError:
        pass

    data = Database('test', True, True, True)

    data.offers.insert([
        ["First Quote", "FName", "LName", "Comp", "0123", "a.b@c.d",
        "asd 123", "456", "qwe", "zxc"],
        ["Second", "FName", "LName", "Comp", "0123", "a.b@c.d",
        "asd 123", "456", "qwe", "zxc"],
        ["Third", "FName", "LName", "Comp", "0123", "a.b@c.d",
        "asd 123", "456", "qwe", "zxc"]],
        True)
    data.groups.insert([1, "First Group"])
    data.groups.insert([1, "Keittiö"])
    data.groups.insert([1, "Kylpyhuone"])

    data.groups.insert([2, "Kylpyhuone"])
    data.groups.insert([3, "..."])


if __name__ == '__main__':
    build_test_db()
