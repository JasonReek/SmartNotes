"""
Copyright (c) 2020 Jason Reek

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sqlite3
import os 
from enum import Enum


class SQLTypes(Enum):
    """Enumerated SQL data types."""
    NULL = 0
    BOOL = 1
    INTEGER = 2
    TEXT = 3
    REAL = 4
    BLOB = 5

class SQLiteLib:
    """ 
        An SQL wrapper library for abstracting away SQL complexity in exchange
        for python methods. 
    """
    def __init__(self, database_location=None):
        self._database_location = database_location
        self._database = None 
        self._connection = None 
        self._cursor = None 
        self._connected_to_database = False
        self._current_row_id = None  

    def createNewDatabase(self, database_name):
        """Creates a new database."""
        try:
            connection = None
            if ".db" not in database_name:
                database_name = database_name+".db" 
            database_location = "/".join(["database", database_name])
            if os.path.isfile(database_location):
                print("Database already exists!") 
            else:
                connection = sqlite3.connect(database_location)
                print("Creating database... SQLite version", sqlite3.version)

        except Exception as e:
            print("Failed to create or read database:",e)
        finally:
            if connection:
                connection.close()

    def getSQLType(self, sql_type):
        """Returns the SQL type if it exists."""
        types = {
            SQLTypes.NULL: "NULL",
            SQLTypes.BOOL: "INTEGER",
            SQLTypes.INTEGER: "INTEGER",
            SQLTypes.TEXT: "TEXT",
            SQLTypes.REAL: "REAL",
            SQLTypes.BLOB: "BLOB"
        }
        if sql_type not in types:
            return None
        return types[sql_type]

    def detectSQLType(self, value):
        """SQL python type checking."""
        if isinstance(value, int):
            return self.getSQLType(SQLTypes.INTEGER)
        if isinstance(value, float):
            return self.getSQLType(SQLTypes.REAL)
        if isinstance(value, str):
            return self.getSQLType(SQLTypes.TEXT)
        if isinstance(value, bool):
            return self.getSQLType(SQLTypes.INTEGER)
        if isinstance(value, bytes):
            return self.getSQLType(SQLTypes.BLOB)
        return self.getSQLType(SQLTypes.NULL)

    # openDatabase()
    #
    # -Opens the database, if a different location is
    #  placed in the parameter than the one used in 
    #  object init, then the method will use the db location
    #  placed in it's parameter. 
    def openDatabase(self, database_location=None):
        """
        Opens the database; if a different location is placed in the parameter than the one used in 
        object init, then the method will use the db location placed in its parameter.
        """
        try:
            # Set new database
            if self._database_location != database_location and database_location != None:
                self._database_location = database_location
            
            if self._database_location != None and not self._connected_to_database:
                self._connection = sqlite3.connect(self._database_location)
                self._cursor = self._connection.cursor()
                self._connected_to_database = True

        except Exception as e:
            print("Failed to open the database: ",e)
    
    # closeDatabase()
    #
    # -Closes the database connection. 
    def closeDatabase(self):
        """Closes the database connection."""
        try:
            if self._connection != None and self._connected_to_database:
                self._connection.close()
                self._connected_to_database = False 
        except Exception as e:
            print("Failed to close the database: "+str(e))

    def fixInTextApostrophes(self, string):
        """Handles when a string contains an apostrophe."""
        if "'" in string:
            new_string = ""
            for i in range(0, len(string)):
                if string[i] == "'":
                    new_string = new_string + "\'"
                else:
                    new_string = new_string + string[i]
            return new_string
        return string 
    
    # createSQLInsertCommand()
    #
    # -This method is primarily for internal use.
    #  It basically preps the requested fields into an SQL
    #  command string, and also inserts with the "?"s in the
    #  SQL VALUE() entry string. 
    def createSQLInsertCommand(self, table_name="", fields=[]):
        """
        This method is primarily for internal use.
        It basically preps the requested fields into an SQL
        command string, and also inserts with the "?"s in the
        SQL VALUE() entry string.
        """
        command_head = " ".join(["INSERT INTO", table_name, "("])
        command_list = []
        command_temp = ""
        command = ""
        value_list = []
        value_temp = ""
        value = ""
        try:
            if table_name != "" and len(fields) > 0:
                command_list.append("ID")
                for field in fields:
                    command_list.append(field)
                    value_list.append('?')
                value_list.append('?')
                value_temp = ", ".join(value_list)
                value = "".join(["VALUES (", value_temp, ")"])
                command_temp = ", ".join(command_list)
                command = "".join([command_head, command_temp, ") ", value])
         
        except Exception as e:
            print("Failed to create SQL command: "+command+" - "+str(e))
            print("command_head:", command_head)
            print("command_list", command_list)
            print("command_temp", command_temp)
            print("value_list", value_list)
            print("value_temp", value_temp)
            print("value", value)
            return command
        return command

    # insertRow()
    #
    # -Inserts a record into the chosen table.
    #  The length of the fields and values MUST 
    #  match inorder to insert a record. 
    def insertRow(self, table_name="", fields=[], values=[]):
        """
        Inserts a record into the chosen table.
        The length of the fields and values MUST 
        match inorder to insert a record.
        """
        sql_statement= ""
        mod_vals = []
        if len(values) > 0 and table_name != "":
            mod_vals.append(self.getNextRowID(table_name))
            mod_vals.extend(values)
            for i, value in enumerate(values):
                if isinstance(value, str):
                    mod_vals[i+1] = self.fixInTextApostrophes(value)

        try:
            if self._connected_to_database and table_name != "" and len(fields) > 0 and len(fields)+1 == len(mod_vals):
                sql_statement = self.createSQLInsertCommand(table_name, fields)
                self._cursor.execute(sql_statement, tuple(mod_vals))
                self._connection.commit()

        except Exception as e:
            print("Failed to enter row: "+str(e))
            self.closeDatabase()

    def updateValue(self, table_name="", field="", value=None):
        """ Updates the selected value in the record."""
        try:
            if self._connected_to_database and table_name != "" and field != "" and value != None:
                if isinstance(value, str):
                    value = self.fixInTextApostrophes(value)
                    value = "'"+value+"'"
                update_query = "UPDATE {tn} SET {cn} = {v}".format(tn=table_name, cn=field, v=str(value))
                self._cursor.execute(update_query)
                self._connection.commit()

        except Exception as e:
            print("Failed to update sqlite table: "+str(e))
            self.closeDatabase()
    # removeRow()
    #
    # -Removes a record from the chosen table. 
    '''
    *NOTE: ADD A REMOVE ALL FROM ID METHOD
    '''
    def removeRow(self, table_name="", word=""):
        """ Removes a record from the selected table."""
        try:
            if self._connected_to_database and table_name != "" and word != "":
                command = "".join(["DELETE FROM ", table_name, " WHERE WORD = '", str(word),"'"])
                self._cursor.execute(command)
                self._connection.commit()
           
        except Exception as e:
            print("Failed to remove row: "+str(e))
            self.closeDatabase()

    def readRow(self, table_name="", row_id=-1):
        """Returns a selected row."""
        try:
            if self._connected_to_database and (table_name !="" and row_id != -1):
                self._cursor.execute("SELECT * FROM {tn} WHERE {cn} = {ri}".format(tn=table_name, cn="ID", ri=str(row_id)))
                row = self._cursor.fetchone()
                return row

        except Exception as e:
            print("Failed to read row: "+str(e))
            self.closeDatabase()
    
    def getValuesFromField(self, table_name, field):
        """ Returns values from a selected field."""
        try:
            if self._connected_to_database and (table_name != "" and field != ""):
                self._cursor.execute("SELECT {cn} FROM {tn}".format(tn=table_name, cn=field))
                values = [value[0] for value in self._cursor.fetchall()]
                return values

        except Exception as e:
            print("Failed to read row: "+str(e))
            self.closeDatabase()
    
    def getCondValuesFromField(self, table_name, field, cond, cond_val):
        """Returns values from a field with a specified condition value.""" 
        try:
            if self._connected_to_database and (table_name != "" and field != ""):
                self._cursor.execute("SELECT {cn} FROM {tn} WHERE {cd} = '{cdv}' ".format(tn=table_name, cn=field, cd=cond, cdv=cond_val))
                values = [value[0] for value in self._cursor.fetchall()]
                return values

        except Exception as e:
            print("Failed to read row: "+str(e))
            self.closeDatabase()
    
    def getValuesFrom2Fields(self, table_name, field_1, field_2):
        """Returns values from two specified fields."""
        try:
            if self._connected_to_database and (table_name != "" and field_1 != "" and field_2 != ""):
                self._cursor.execute("SELECT {cn1},{cn2} FROM {tn}".format(tn=table_name, cn1=field_1, cn2=field_2))
                values = self._cursor.fetchall()
                return values

        except Exception as e:
            print("Failed to read row: "+str(e))
            self.closeDatabase()
    
    def readTable(self, table_name=""):
        """Read the entire contents of a table."""
        try:
            table = []
            if self._connected_to_database and table_name != "":
                self._cursor.execute("SELECT * FROM {tn}".format(tn=table_name))
                table = self._cursor.fetchall()
                table = [row[1] for row in table]
            
        except Exception as e:
            print("Failed to read table: "+str(e))
            self.closeDatabase()
            return table
        return table

    def createTable(self, table_name="", data={}):
        """Create a new table into the database."""
        item_count = len(data)
        command = """CREATE TABLE """+table_name+"""(
        ID INTEGER PRIMARY KEY,
        """
        temp_line = ""
        try:
            if self._connected_to_database and table_name != "" and len(data) > 0:
                if table_name not in self.readListOfTables():
                    for field, value_and_prop in data.items():
                        field_caps = field.upper()
                        temp_line = temp_line+str(field_caps)
                        temp_line = temp_line+" "+self.detectSQLType(value_and_prop["value"])
                        if value_and_prop["is_not_null"]:
                            temp_line = temp_line+" NOT NULL"
                        if value_and_prop["is_unique"]:
                            temp_line = temp_line+" UNIQUE"
                        item_count -= 1
                        # Don't add comma if last item. 
                        if item_count > 0:
                            temp_line = temp_line+","
                        command = command+"\n"+temp_line
                        temp_line = ""
                    command = command+");"
                    self._cursor.execute(command)
                    self._connection.commit()
                    print("Table {tn} created successfully.".format(tn=table_name))
                else:
                    print("Table {tn} already exists.".format(tn=table_name))

        except sqlite3.Error as e:
            print("Failed to create table {tn}: {err}".format(tn=table_name, err=str(e)))
            self.closeDatabase()      

    def removeTable(self, table_name=""):
        """Removes a table from the database."""
        try:
            if self._connected_to_database and table_name != "":
                if table_name in self.readListOfTables():
                    self._cursor.execute("DROP TABLE {tn}".format(tn=table_name))
                    print("Table {tn} removed successfully.".format(tn=table_name))
                else:
                    print("Table {tn} does not exist.".format(tn=table_name))
        except Exception as e:
            print("Failed to remove table: "+str(e))
            self.closeDatabase()

    def readListOfTables(self):
        """ Returns a list of tables from the selected database."""
        table_names = []
        if self._connected_to_database:
            self._cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_names = [table[0] for table in self._cursor.fetchall()]
        return table_names

    # getNextRowID()
    #
    # -Returns the next row ID from the chosen table
    #  to be inserted into. This row ID does not exist 
    #  yet. 
    def getNextRowID(self, table_name=""):
        try:
            """
            Returns the next row ID from the chosen table
            to be inserted into. This row ID does not exist 
            yet.
            """
            next_row_id = None 
            if table_name != "":
                command = " ".join(["SELECT MAX(ID) FROM", table_name])
                self._cursor.execute(command)
                # First row of table, so there is no next row 
                next_row_id = self._cursor.fetchone()[0] 
                if next_row_id == None:
                    return 1
                
        except Exception as e:
            print("Failed to get the next row id: "+str(e))
            return next_row_id 
        return (next_row_id + 1)
    
    # getFirstRowID()
    #
    # -Returns the first row ID from the chosen table.
    def getFirstRowID(self, table_name=""):
        """Returns the first row ID from the chosen table."""
        try:
            first_row_id = None 
            if table_name != "":
                command = " ".join(["SELECT MIN(ID) FROM", table_name])
                self._cursor.execute(command)
                first_row_id = int(self._cursor.fetchone()[0])
            return first_row_id
                
        except Exception as e:
            print("Failded to get the first row id: "+str(e))
        return first_row_id
    
    # getLastRowID()
    #
    # -Returns the last row ID from the chosen table.
    def getLastRowID(self, table_name=""):
        """Returns the last row ID from the chosen table."""
        try:
            last_row_id = None 
            if table_name != "":
                command = " ".join(["SELECT MAX(ID) FROM", table_name])
                self._cursor.execute(command)
                last_row_id = int(self._cursor.fetchone()[0]) 
            return last_row_id
                
        except Exception as e:
            print("Failed to get the last row id: "+str(e))
        return last_row_id
    # getLastInsertedRowID()
    #
    # -Returns the row ID that was last inserted into.
    # This method will return None if table has not been
    # used yet. 
    def getLastInsertedRowID(self):
        """
        Returns the row ID that was last inserted into.
        This method will return None if table has not been
        used yet.
        """
        try:
            return self._cursor.lastrowid
        except Exception as e:
            print("Failed to get last used row ID: "+str(e))


    
