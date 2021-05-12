import unittest

from bson.objectid import ObjectId

from table import OfferTables


class TestTables(unittest.TestCase):
    
    tables = OfferTables()

    offer_keys = ["id", "name"]
    offer_data = [
        (str(ObjectId()), "Tarjous 1"),
        (str(ObjectId()), "Tarjous 2"),
        (str(ObjectId()), "Testi tarjous"),
        (str(ObjectId()), "Uusi tarjous")
    ]
    group_keys = ["id", "offer_id", "name"]
    group_data = [
        (str(ObjectId()), offer_data[0][0], "Keittiö"),
        (str(ObjectId()), offer_data[0][0], "Kylpyhuone"),
        (str(ObjectId()), offer_data[1][0], "Keittiö"),
        (str(ObjectId()), offer_data[2][0], "Keittiö"),
        (str(ObjectId()), offer_data[3][0], "Keittiö"),
        (str(ObjectId()), offer_data[3][0], "...")
    ]
    opredef_keys = ["id", "group_id"]
    opredef_data = (str(ObjectId()), group_data[0][0])

    omaterial_keys = ["id", "group_id"]
    omaterial_data = (str(ObjectId()), group_data[0][0])

    oproduct_keys = ["id", "group_id", "width", "height", "depth"]
    oproduct_data = (str(ObjectId()), group_data[0][0], 1200, 2300, 620)

    opart_keys = ["id", "product_id"]
    opart_data = (str(ObjectId()), oproduct_data[0][0])

    material_keys = ["code"]
    material_data = ("MAT16",)

    product_keys = ["code", "width", "height", "depth"]
    product_data = ("kaappi", 1200, 2300, 620)
    product_data2 = ("tuote", 650, 300, 420)
    product_data3 = [("tuote1", 650, 300, 420), ("tuote2", 640, 310, 410)]

    part_keys = ["code", "product_code"]
    part_data = [
        ("hylly", "kaappi"),
        ("tausta", "kaappi"),
        ("ovi", "kaappi")
    ]

    def test_insert_offer(self):
        res = self.tables.insert("offers", self.offer_keys, self.offer_data[0])
        self.assertEqual(res, True)

    def test_insert_many_offers(self):
        res = self.tables.insert("offers", self.offer_keys, self.offer_data[1:], True)
        self.assertEqual(res, True)

    def test_insert_many_groups(self):
        res = self.tables.insert("offer_groups", self.group_keys, self.group_data, True)
        self.assertEqual(res, True)

    def test_insert_offer_predefs(self):
        res = self.tables.insert("offer_predefs", self.opredef_keys, self.opredef_data)
        self.assertEqual(res, True)

    def test_insert_offer_materials(self):
        res = self.tables.insert("offer_materials", self.omaterial_keys, self.omaterial_data)
        self.assertEqual(res, True)

    def test_insert_offer_products(self):
        res = self.tables.insert("offer_products", self.oproduct_keys, self.oproduct_data)
        self.assertEqual(res, True)

    def test_insert_offer_parts(self):
        res = self.tables.insert("offer_parts", self.opart_keys, self.opart_data)
        self.assertEqual(res, True)

    def test_insert_materials(self):
        res = self.tables.insert("materials", self.material_keys, self.material_data)
        self.assertEqual(res, True)

    def test_insert_products(self):
        res = self.tables.insert("products", self.product_keys, self.product_data)
        self.assertEqual(res, True)

    def test_insert_parts(self):
        res = self.tables.insert("parts", self.part_keys, self.part_data, True)
        self.assertEqual(res, True)

    def test_get(self):
        res = self.tables.insert("products", self.product_keys, self.product_data2)
        res = self.tables.get_one(
            "products",
            [self.product_keys[2]],
            [self.product_keys[0]],
            [self.product_data2[0]]
        )
        self.assertEqual(res[0], self.product_data2[2])

    def test_get(self):
        self.tables.insert("products", self.product_keys, self.product_data2)
        res = self.tables.get(
            "products",
            [self.product_keys[2]],
            [self.product_keys[0]],
            [self.product_data2[0]]
        )
        self.assertEqual(res[0], self.product_data2[2])

    def test_get_many(self):
        self.tables.insert("products", self.product_keys, self.product_data3, True)
        res = self.tables.get(
            "products",
            [self.product_keys[2]],
            [self.product_keys[0]],
            [self.product_data3[1][0]], True
        )
        self.assertEqual(res[0][0], self.product_data3[1][2])
