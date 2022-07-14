from os import path

# for auto closing cursors
from contextlib import closing

import sqlite3 as sql

import requests


class FlaskMetrics():
    
    def __init__(self,database_name="database.db",rows=["IP_ADDR","URL","BROWSER","ACCEPT_LANGUAGES"],max_rows=10000,ignore_ips=[]) -> None:
        
        self.max_rows = max_rows
        self.ignore_ips = ignore_ips
        self.rows = rows
        if not path.exists(database_name):
            # init database writer
            self.connector = sql.connect(database_name,check_same_thread=False)
            self.connector.row_factory = sql.Row
            self.__init_db()
            
            
        if not self.__table_exists(database_name):
            self.__init_db()
            
            
        # init database writer
        self.connector = sql.connect(database_name,check_same_thread=False)
        self.connector.row_factory = sql.Row
        
            
    def __init_db(self) -> None:
        """create a table named METRICS with all rows specified in constructor
        each row is of type TEXT because it's easier
        """
        
        with closing(self.connector.cursor()) as cursor:
            
            cmd = "CREATE TABLE METRICS ("
            
            for row in self.rows:
                cmd += f"{row} TEXT,"       
                           
            cmd += "DATE TEXT DEFAULT CURRENT_DATE,TIME TEXT DEFAULT CURRENT_TIME )"
            
            print(cmd)
            cursor.execute(cmd)
            self.connector.commit()
            
    
    
    def store_visit_d(self,request):
        """decorator that serves the same purpose as store_vist().
        Don't work on Flask as it produces a :
        "RuntimeError: Working outside of request context."
        at startup

        Args:
            request (_type_): the request object
        """
        
        def new_function(original_function):
            
            if request != None:
                self.store_visit(request)
            
            return original_function
        
        
        return new_function



    def store_visit(self,request):
        
        """
        call that method to store a request, 
        a dict will be built from the request variable by the build_dict method
        that you may have overriden
        at the creation of the metrics database.
        """
        
        #building dict
        
        request = self.build_dict(request)
        
        
        with closing(self.connector.cursor()) as cursor:
            
            rows = dict(cursor.execute("SELECT COUNT(*) rows_number FROM METRICS").fetchone())["rows_number"]
            
            
            if rows > self.max_rows:
                self.__clear_db()
                
            del rows
            
            cmd = "INSERT INTO METRICS ("
            for row in request.keys():
                cmd += f"{row},"
                
            cmd = cmd[0:-1] + ") VALUES("
            
            
            for _ in request.values():
                
                cmd += f"?,"
                
                
            cmd = cmd[0:-1] + ")"
                
            cursor.execute(cmd,[str(val) for val in request.values()]) # passer le contenu du dictionnaire
            
            
            self.connector.commit()
    
    
    def __clear_db(self):
        
        with closing(self.connector.cursor()) as cursor:
            
            cursor.execute("DELETE FROM METRICS")
            self.connector.commit()
            
            
    def __table_exists(self,database_name:str) -> bool:
        self.connector = sql.connect(database_name,check_same_thread=False)
        self.connector.row_factory = sql.Row
        
        with closing(self.connector.cursor()) as cursor:
            
            try:
                cursor.execute("SELECT * FROM METRICS").fetchall()
                return True
            except:
                return False        
        
        
    def get_visits_count(self,days=1,distinct=False)->int:
        
        with closing(self.connector.cursor()) as cursor:
            distinct = "GROUP BY IP_ADDR" if distinct else ""
            return len(cursor.execute(f"SELECT * FROM METRICS WHERE DATE>=date('now','-{days} days') AND URL='/' {distinct}").fetchall())
    
    
    
    def build_dict(request)->dict:
        """override this method with a function building
        a dictionnary from the flask/(any web server) resquest variable
        in order to pass it to store_visit()

        Args:
            request (_type_): any type of request variable that you can take from your web server

        Returns:
            dict: the dictionnary built
        """
        
        r = {}
    
        r["URL"] = request.path
        r["BROWSER"] = request.user_agent.browser
        r["ACCEPT_LANGUAGES"] = request.accept_languages
        r["IP_ADDR"] = request.remote_addr
        
        
        return r
    

    
    