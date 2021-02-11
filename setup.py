# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 23:43:38 2018

@author: felipe
"""
import argparse
import sqlite3
import json

def create_tables(conn):
    # creating general table:
    tblgeneral = "CREATE TABLE IF NOT EXISTS general (id INTEGER PRIMARY KEY AUTOINCREMENT, action integer, user integer, category integer, subcategory integer, value REAL, date text, FOREIGN KEY (action) REFERENCES action(id) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY (user) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY (category) REFERENCES category(id) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY (subcategory) REFERENCES subcategory(id) ON DELETE CASCADE ON UPDATE CASCADE);"
    conn.execute(tblgeneral)
    Indxgeneral = "CREATE INDEX indiceForeignKeys ON general (action, user, category, subcategory);"
    conn.execute(Indxgeneral)
    conn.commit()

    # creating users table:
    tblurs = "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user text, chat text, active integer);"
    conn.execute(tblurs)
    conn.commit()

    # creating action table:
    tblaction = "CREATE TABLE IF NOT EXISTS action (id INTEGER PRIMARY KEY AUTOINCREMENT, action text);"
    conn.execute(tblaction)
    conn.execute("insert into action(action) values ('Expenses');")
    conn.execute("insert into action(action) values ('Income');")
    conn.commit()

    # creating category table:
    tblcategory = "CREATE TABLE IF NOT EXISTS category (id INTEGER PRIMARY KEY AUTOINCREMENT, category text);"
    conn.execute(tblcategory)
    conn.commit()
    
    # creating subcategory table:
    tblscategory = "CREATE TABLE IF NOT EXISTS subcategory (id INTEGER PRIMARY KEY AUTOINCREMENT, catid integer, subcategory text, FOREIGN KEY (catid) REFERENCES category(id) ON DELETE CASCADE ON UPDATE CASCADE);"
    conn.execute(tblscategory)
    conn.commit()

    # Creating views with complete tables:
    conn.execute("CREATE VIEW IF NOT EXISTS view_general AS SELECT action.action, users.user, category.category, subcategory.subcategory, general.value , substr(date, 6, 2) as month, substr(date, 1, 4) as year FROM general INNER JOIN action on action.id = general.action INNER JOIN users on users.id = general.user INNER JOIN category on category.id = general.category INNER JOIN subcategory on subcategory.id = general.subcategory;")
    conn.execute("CREATE VIEW IF NOT EXISTS view_catsummary AS SELECT category.category, sum(general.value) as total, substr(date, 6, 2) as month, substr(date, 1, 4) as year FROM general INNER JOIN category on category.id = general.category WHERE general.action = (SELECT id from action where action = 'gastos') GROUP BY general.category, month, year;")
    conn.execute("CREATE VIEW IF NOT EXISTS view_scatsummary AS SELECT category.category, subcategory.subcategory, sum(general.value) as total, substr(date, 6, 2) as month, substr(date, 1, 4) as year FROM general INNER JOIN category on category.id = general.category INNER JOIN subcategory on subcategory.id = general.subcategory WHERE general.action = (SELECT id from action where action = 'gastos') GROUP BY general.category, general.subcategory, month, year;")
    conn.execute("CREATE VIEW IF NOT EXISTS view_usersummary AS SELECT users.user, sum(general.value) as total, substr(date, 6, 2) as month, substr(date, 1, 4) as year FROM general INNER JOIN users on users.id = general.user WHERE general.action = (SELECT id from action where action = 'gastos') GROUP BY general.user, month, year;")
    conn.execute("CREATE VIEW IF NOT EXISTS view_action as SELECT action.action, sum(general.value ) as total, substr(date, 6, 2) as month, substr(date, 1, 4) as year FROM general INNER JOIN action on action.id = general.action group by action.action, month, year ORDER BY year, month;")
    conn.commit()
    return True

def add_category(conn, cat):
    conn.execute("INSERT INTO category(category) VALUES ('{}');".format(cat))
    conn.commit()
    res = conn.execute("SELECT id FROM category where category = '{}'".format(cat))
    return res.fetchone()[0]

def add_subcategory(conn, catid, subcat):
    conn.execute("INSERT INTO subcategory(catid, subcategory) VALUES "
                 "({ci}, '{sc}');".format(ci=catid, sc=subcat))
    conn.commit()
    res = conn.execute("SELECT id FROM subcategory where subcategory = '{}'".format(subcat))
    return res.fetchone()[0]

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
    conn = sqlite3.connect(args.database)
    create_tables(conn)

    if args.settings:
        with open(args.settings) as f:
            cats = json.load(f)
        for k, vals in cats.items():
            cid = add_category(conn, k)
            print("Category {myu} get ID {myi}".format(myu=k, myi=cid))
            for v in vals:
                sid = add_subcategory(conn, cid, v)
                print("Subcategory {myu} get ID {myi}".format(myu=v, myi=sid))
    print("All done")
    
if __name__ == "__main__":
    main()
    