# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 23:43:38 2018

@author: felipe
"""
import argparse
import json
from dbZeroEuro import DBHelper

def main():
    parser = argparse.ArgumentParser(description="Setup database for DomesticEconomy")
    parser.add_argument("-d", "--database", type=str,
                        default="domestic_economy.sqlite",
                        help="DomesticEconomy database name (default %(default)s)",
    )
    parser.add_argument("-s", "--settings", type=str,
                        help="Path to a json file with category and subcategory")
    args = parser.parse_args()

    #connect to db
    db = DBHelper()

    if args.settings:
        with open(args.settings) as f:
            cats = json.load(f)
        for k, vals in cats.items():
            cid = db.add_category(k)
            print("Category {myu} get ID {myi}".format(myu=k, myi=cid))
            for v in vals:
                sid = db.add_subcategory(cid, v)
                print("Subcategory {myu} get ID {myi}".format(myu=v, myi=sid))
    print("All done")

if __name__ == "__main__":
    main()
