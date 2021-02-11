# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 13:14:01 2018

@author: felipe
"""
import sqlite3
import shutil
import time
import os
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
from API import email, password, database

class DBHelper:
    def __init__(self, dbname=database):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def create_tables(conn):
        # creating general table:
        tblgeneral = "CREATE TABLE IF NOT EXISTS general (id INTEGER PRIMARY "\
                     "KEY AUTOINCREMENT, action integer, user integer, category"\
                     " integer, subcategory integer, value REAL, date text, " \
                     "FOREIGN KEY (action) REFERENCES action(id) ON DELETE " \
                     "CASCADE ON UPDATE CASCADE, FOREIGN KEY (user) REFERENCES"\
                     " users(id) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN"\
                     " KEY (category) REFERENCES category(id) ON DELETE "\
                     "CASCADE ON UPDATE CASCADE, FOREIGN KEY (subcategory) "\
                     "REFERENCES subcategory(id) ON DELETE CASCADE ON UPDATE CASCADE);"
        conn.execute(tblgeneral)
        Indxgeneral = "CREATE INDEX indiceForeignKeys ON general (action, " \
                      "user, category, subcategory);"
        conn.execute(Indxgeneral)
        conn.commit()

        # creating users table:
        tblurs = "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY " \
                 "AUTOINCREMENT, user text, chat text, active integer);"
        conn.execute(tblurs)
        conn.commit()

        # creating action table:
        tblaction = "CREATE TABLE IF NOT EXISTS action (id INTEGER PRIMARY " \
                    "KEY AUTOINCREMENT, action text);"
        conn.execute(tblaction)
        conn.execute("insert into action(action) values ('Expenses');")
        conn.execute("insert into action(action) values ('Income');")
        conn.commit()

        # creating category table:
        tblcategory = "CREATE TABLE IF NOT EXISTS category (id INTEGER " \
                      "PRIMARY KEY AUTOINCREMENT, category text);"
        conn.execute(tblcategory)
        conn.commit()

        # creating subcategory table:
        tblscategory = "CREATE TABLE IF NOT EXISTS subcategory (id INTEGER " \
                       "PRIMARY KEY AUTOINCREMENT, catid integer, subcategory" \
                       " text, FOREIGN KEY (catid) REFERENCES category(id) " \
                       "ON DELETE CASCADE ON UPDATE CASCADE);"
        conn.execute(tblscategory)
        conn.commit()

        # Creating views with complete tables:
        conn.execute("CREATE VIEW IF NOT EXISTS view_general AS SELECT "
                     "action.action, users.user, category.category, "
                     "subcategory.subcategory, general.value , substr(date, 6,"
                     " 2) as month, substr(date, 1, 4) as year FROM general "
                     "INNER JOIN action on action.id = general.action INNER "
                     "JOIN users on users.id = general.user INNER JOIN "
                     "category on category.id = general.category INNER JOIN "
                     "subcategory on subcategory.id = general.subcategory;")
        conn.execute("CREATE VIEW IF NOT EXISTS view_catsummary AS SELECT "
                     "category.category, sum(general.value) as total, "
                     "substr(date, 6, 2) as month, substr(date, 1, 4) as year"
                     " FROM general INNER JOIN category on category.id = "
                     "general.category WHERE general.action = (SELECT id from"
                     " action where action = 'Expenses') GROUP BY general.category,"
                     " month, year;")
        conn.execute("CREATE VIEW IF NOT EXISTS view_scatsummary AS SELECT "
                     "category.category, subcategory.subcategory, sum("
                     "general.value) as total, substr(date, 6, 2) as month, "
                     "substr(date, 1, 4) as year FROM general INNER JOIN "
                     "category on category.id = general.category INNER JOIN "
                     "subcategory on subcategory.id = general.subcategory WHERE"
                     " general.action = (SELECT id from action where action ="
                     " 'Expenses') GROUP BY general.category, general.subcategory,"
                     " month, year;")
        conn.execute("CREATE VIEW IF NOT EXISTS view_usersummary AS SELECT "
                     "users.user, sum(general.value) as total, "
                     "substr(date, 6, 2) as month, substr(date, 1, 4) as year"
                     " FROM general INNER JOIN users on users.id = general.user"
                     " WHERE general.action = (SELECT id from action where "
                     "action = 'Expenses') GROUP BY general.user, month, year;")
        conn.execute("CREATE VIEW IF NOT EXISTS view_action as SELECT "
                     "action.action, sum(general.value ) as total, "
                     "substr(date, 6, 2) as month, substr(date, 1, 4) as year"
                     " FROM general INNER JOIN action on action.id = "
                     "general.action group by action.action, month, year "
                     "ORDER BY year, month;")
        conn.commit()
        return True

    def insertuser(self, user, chat):
        self.conn.execute("insert into users(user, chat) values (?, ?);", (user,
                                                                           chat))
        self.conn.commit()

    def add_category(self, cat):
        self.conn.execute("INSERT INTO category(category) VALUES ('{}');".format(cat))
        self.conn.commit()
        res = self.conn.execute("SELECT id FROM category where category = "
                                "'{}'".format(cat))
        return res.fetchone()[0]

    def add_subcategory(self, catid, subcat):
        self.conn.execute("INSERT INTO subcategory(catid, subcategory) VALUES "
                     "({ci}, '{sc}');".format(ci=catid, sc=subcat))
        self.conn.commit()
        res = self.conn.execute("SELECT id FROM subcategory where subcategory"
                                " = '{}'".format(subcat))
        return res.fetchone()[0]

    def get_action(self):
        stmt = "SELECT distinct(action) FROM action"
        return [x[0] for x in self.conn.execute(stmt)]

    def get_users(self):
        stmt = "SELECT distinct(user) FROM users"
        return [x[0] for x in self.conn.execute(stmt)]

    def get_active_chatid(self):
        stmt = "SELECT distinct(chatid) FROM users WHERE active = 1"
        return [x[0] for x in self.conn.execute(stmt)]

    def get_category(self):
        stmt = "SELECT distinct(category) FROM category"
        return [x[0] for x in self.conn.execute(stmt)]

    def get_subcategory(self, cat = None):
        if cat:
            stmt = "SELECT distinct(subcategory) FROM subcategory WHERE catid" \
                   " = (SELECT id from category where category = (?));"
            args = (cat,)
            return [x[0] for x in self.conn.execute(stmt, args)]
        else:
            stmt = "SELECT distinct(subcategory) FROM subcategory"
            return [x[0] for x in self.conn.execute(stmt)]

    def insertExpenses(self, owner, category, subcategory, value, date):
        stmt = "INSERT INTO general(action, user, category, subcategory, " \
               "value, date) VALUES ((SELECT id from action where action = " \
               "'Expenses'), (select id from users where user = (?)), (select" \
               " id from category where category = (?)), (select id from " \
               "subcategory where subcategory = (?)), (?), (?));"
        args = (owner, category, subcategory, value, date)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def insertIncome(self, owner, value, date):
        stmt = "INSERT INTO general(action, user, value, date) VALUES ((SELECT" \
               " id from action where action = 'receita'), (select id from " \
               "users where user = (?)), (?), (?));"
        args = (owner, value, date)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_summary(self, param = None, month = None, year = None):
        if param == 'category':
            stmt = "SELECT category, total from view_catsummary where month " \
                   "= '{}' and year = '{}' ORDER BY 2 DESC".format(month, year)
            results = self.conn.execute(stmt).fetchall()
            results = pd.DataFrame(results, columns = ('*Category*', '*Total*'))
            return results
        elif param == 'subcategory':
            stmt = "SELECT category, subcategory, total from view_scatsummary" \
                   " where month = '{}' and year = '{}' ORDER BY 2 DESC".format(month, year)
            results = self.conn.execute(stmt).fetchall()
            results = pd.DataFrame(results, columns = ('*Category*',
                                                       '*Subcategory*',
                                                       '*Total*'))
            return results
        elif param == 'user':
            stmt = "SELECT user, total from view_usersummary where month = " \
                   "'{}' and year = '{}' ORDER BY 2 DESC".format(month, year)
            results = self.conn.execute(stmt).fetchall()
            results = pd.DataFrame(results, columns = ('*User*', '*Total*'))
            return results
        elif param == 'balance':
            stmt = "SELECT action, total from view_action where month = '{}'" \
                   " and year = '{}' ORDER BY 2 DESC".format(month, year)
            results = self.conn.execute(stmt).fetchall()
            results = pd.DataFrame(results, columns = ('*Movimento*', '*Total*'))
            return results
        else:
            msg = ["Not found: {}".format(param)]
            return msg

    def get_plots(self, param = None, month = None, year = None):
        # Few configs
        plt.style.use('ggplot')
        # plt.style.use('fivethirtyeight')
        plotwd = "plots"
        plt.rcParams.update({'figure.autolayout': True})
        if not os.path.exists(plotwd):
            os.makedirs(plotwd)
        if param == 'category':
            CatPlot = pd.read_sql("SELECT category, total from view_catsummary"
                                  " WHERE month = '{}' AND year = '{}' ORDER "
                                  "BY 2 DESC".format(month, year), self.conn)
            CatPlot.plot.bar(x="category", y="total", legend = False, rot=7)
            path = os.path.join(os.getcwd(), plotwd) + '/Category_plot.png'
            plt.savefig(path)  # save the figure to file
            plt.close()
            return str(path)
        elif param == 'subcategory':
            SubCatPlot = pd.read_sql("SELECT category, subcategory, total FROM"
                                     " view_scatsummary WHERE month = '{}' AND"
                                     " year = '{}' ORDER BY 3 DESC".format(month, year), self.conn)
            SubCatPlot["SubCategorias"] = SubCatPlot.category + " " + SubCatPlot.subcategory
            SubCatPlot.plot.bar(x = "SubCategorias", y = "total", legend = False, rot=90)
            path = os.path.join(os.getcwd(), plotwd) + '/SubCategory_plot.png'
            plt.savefig(path)  # save the figure to file
            plt.close()
            return str(path)
        elif param == 'user':
            UserPlot = pd.read_sql("SELECT user, total from view_usersummary "
                                   "WHERE month = '{}' and year = '{}' ORDER "
                                   "BY 2 DESC".format(month, year), self.conn)
            UserPlot.pivot_table(columns="user").plot.bar(legend = True, rot=0)
            path = os.path.join(os.getcwd(), plotwd) + '/User_plot.png'
            plt.savefig(path)  # save the figure to file
            plt.close()
            return str(path)
        elif param == 'historico':
            # Retrieving data
            df_general = pd.read_sql("SELECT general.id, action.action, "
                                     "users.user, category.category, "
                                     "subcategory.subcategory, general.value,"
                                     " date  FROM general INNER JOIN action "
                                     "on action.id = general.action INNER JOIN"
                                     " users on users.id = general.user INNER"
                                     " JOIN category on category.id = "
                                     "general.category INNER JOIN subcategory "
                                     "on subcategory.id = general.subcategory;",
                                     self.conn)
            df_receitas = pd.read_sql("SELECT general.id, action.action, "
                                      "users.user, general.category, "
                                      "general.subcategory, general.value, "
                                      "date  FROM general JOIN action on "
                                      "action.id = general.action JOIN users "
                                      "on users.id = general.user WHERE "
                                      "action.action = 'receita'", self.conn)
            df_completo = df_general.append(df_receitas)

            # organizing data
            df_completo["date"] = pd.to_datetime(df_completo["date"])
            df_general["date"] = pd.to_datetime(df_general["date"])
            df_completo['year'] = pd.DatetimeIndex(df_completo['date']).year
            df_general['year'] = pd.DatetimeIndex(df_general['date']).year
            df_completo['month'] = pd.DatetimeIndex(df_completo['date']).month
            df_general['month'] = pd.DatetimeIndex(df_general['date']).month
            df_completo.set_index(["date"], inplace=True)
            df_general.set_index(["date"], inplace=True)

            # Domestic Balance
            action_Month = df_completo[["action", "month", "value"]]
            action_Month = action_Month.groupby(by=["action", "month"], as_index=False).sum()
            action_Month = action_Month.pivot_table(index="month",
                                                    columns="action",
                                                    values="value").fillna(value=0)
            action_Month.plot()
            plt.legend(loc=2, ncol=2).get_frame().set_alpha(0)
            Balanco_path = os.path.join(os.getcwd(), plotwd) + '/balanco.png'
            plt.savefig(Balanco_path)  # save the figure to file
            plt.close()

            # Category/month
            cat_Month = df_general[["category", "month", "value"]]
            cat_Month = cat_Month.groupby(by=["category", "month"], as_index=False).sum()
            cat_Month = cat_Month.pivot_table(index="month", columns="category",
                                              values="value").fillna(value=0)
            cat_Month.plot()
            plt.legend(loc=2, ncol=3).get_frame().set_alpha(0)
            CatMonth_path = os.path.join(os.getcwd(), plotwd) + '/CatMonth.png'
            plt.savefig(CatMonth_path)  # save the figure to file
            plt.close()

            # user/month
            user_Month = df_general[["user", "month", "value"]]
            user_Month = user_Month.groupby(by=["user", "month"], as_index=False).sum()
            user_Month = user_Month.pivot_table(index="month", columns="user",
                                                values="value").fillna(value=0)
            user_Month.plot()
            plt.legend(loc=2, ncol=2).get_frame().set_alpha(0)
            UsrMonth_path = os.path.join(os.getcwd(), plotwd) + '/UsrMonth_path.png'
            plt.savefig(UsrMonth_path)  # save the figure to file
            plt.close()
            return [Balanco_path, CatMonth_path, UsrMonth_path]
        else:
            path = "Not found: {}".format(param)
            return str(path)

    # Function to mannage SQL from message
    def sql(self, sql):
        if sql.upper().startswith("ALTER TABLE"):
            msg = "ALTER TABLE NOT ALLOWED BY MSG"
            return msg
        elif sql.upper().startswith("DROP"):
            msg = "DROP [TABLE/VIEW] NOT ALLOWED BY MSG"
            return msg
        elif sql.upper().startswith("SELECT"):
            res = self.conn.execute(sql).fetchall()
            res = pd.DataFrame(res)
            return res
        else:
            self.conn.execute(sql)
            self.conn.commit()
            msg = 'All done!'
            return msg

    # Database Backup function
    def sqlite3_backup(self, dbfile=database, backupdir='./backup', use_tls=True):

        # Create backupdir if not exist
        if not os.path.isdir(backupdir):
            os.makedirs(backupdir)
        # Create timestamped database copy
        backup_file = os.path.join(backupdir, os.path.basename(dbfile) + time.strftime("-%Y%m%d-%H%M%S"))

        # Lock database before making a backup
        #cursor.execute('begin immediate')
        # Make new backup file
        shutil.copyfile(dbfile, backup_file)
        print ("\nCreating {}...".format(backup_file))
        # Unlock database
        #connection.rollback()
        #backupMail.send_mail(send_from = yauser, send_to = dba, text = backup_file, files = backup_file)
        #import backupMail  # function to send backup by email
        # Clean old backup function

        #sending backup by email
        send_from = email
        send_to = email
        subject = 'BACKUP_'+os.path.basename(backup_file)
        files = [backup_file]
        server = 'smtp.gmail.com'
        port = 587
        message = backup_file
        """Compose and send email with provided info and attachments.

        Args:
            send_from (str): from name
            send_to (str): to name
            subject (str): message title
            message (str): message body
            files (list[str]): list of file paths to be attached to email
            server (str): mail server host name
            port (int): port number
            username (str): server auth username
            password (str): server auth password
            use_tls (bool): use TLS mode
            src: https://stackoverflow.com/questions/3362600/how-to-send-email-attachments
        """
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = email
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject

        msg.attach(MIMEText(message))

        for path in files:
            part = MIMEBase('application', "octet-stream")
            with open(path, 'rb') as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            'attachment; filename="{}"'.format(os.path.basename(path)))
            msg.attach(part)

        smtp = smtplib.SMTP(server, port)
        if use_tls:
            smtp.starttls()
        smtp.login(email, password)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.quit()

    # Function to remove old backupfiles
    def clean_data(slef, backup_dir = './backup', NO_OF_DAYS = 7):
        """Delete files older than NO_OF_DAYS days"""

        print ("\n------------------------------")
        print ("Cleaning up old backups")

        for filename in os.listdir(backup_dir):
            backup_file = os.path.join(backup_dir, filename)
            if os.path.isfile(backup_file):
                if os.stat(backup_file).st_ctime < (time.time() - NO_OF_DAYS * 86400):
                    os.remove(backup_file)
                    print ("Deleting {}...".format(backup_file))
