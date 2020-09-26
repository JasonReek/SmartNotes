from SQLiteLibrary import SQLiteLib, SQLTypes
import os 

# Default dictionary selection for testing purposes. 
DATABASE_NAME = "Heidegger.db"

class DefinitionsDatabase:
    """ A specialized "Definition Dictionary" SQL handler built on top of my "SQLiteLibrary"."""
    def __init__(self):
        self.DATABASE_PATH = "dictionary_databases"
        self._database_location = '/'.join([self.DATABASE_PATH, DATABASE_NAME])
        self._database = SQLiteLib()
        
    def setNewDatabase(self, database_location):
        """ Sets the new active dictionary."""
        if not database_location.endswith('.db'):
            database_location = '.'.join([database_location, 'db']) 
        f_database_location = '/'.join([self.DATABASE_PATH, database_location])
        self._database_location = f_database_location
    
    def addNewDatabase(self, database_name):
        """ Adds a new dictionary database."""
        try:
            database_names = [database_name.split(".")[0] for database_name in os.listdir(self.DATABASE_PATH)]
            if database_name not in database_names:
                self._database.createNewDatabase(database_name)
        except Exception as e:
            print("Failed to create a new database:",e)
    
    def getDatabaseNames(self):
        """Returns a list of dictionary names."""
        try:
            return [database_name.split(".")[0] for database_name in os.listdir(self.DATABASE_PATH)]
        except Exception as e:
            print("Failed to get database names:",e)

    def getAllDictWords(self):
        """Returns a list of all the words contained in the selected dictionary."""
        words = []
        try:
            self._database.openDatabase(self._database_location)
            for letter in self._database.readListOfTables():
                words.extend(self._database.readTable(letter))
            return words 
        except Exception as e:
            print(e)
        finally:
            self._database.closeDatabase()
        return words  
    
    def checkIfLetterExists(self, letter):
        """ Checks if the database contains a letter table for the word being entered."""
        try:
            letter = letter.upper()
            self._database.openDatabase(self._database_location)
            return (letter in self._database.readListOfTables())
        except Exception as e:
            print(e)
            return False 

        finally:
            self._database.closeDatabase() 
        return False 

    def addDefinition(self, letter, word, defintion):
        """Adds a new definition into the selected dictionary."""
        try:
            self._database.openDatabase(self._database_location)
            letter = letter.upper()
            self._database.insertRow(letter, ["WORD", "DEFINITION"], [word, defintion])
        except Exception as e:
            print("Failed to add defintion to dictionary:",e)
        finally:
            self._database.closeDatabase() 

    def updateDefinition(self, letter, word, definition):
        """Updates the current selected definition word.""" 
        try:
            self._database.openDatabase(self._database_location)
            letter = letter.upper()
            self._database.updateValue(self, letter, word, definition)

        except Exception as e:
            print("Failed to update defintion in dictionary:",e)
            return False 
        finally:
            self._database.closeDatabase() 
        return False 

    def removeDefinition(self, letter, word):
        """Removes the selected word from the dictionary database."""
        try:
            self._database.openDatabase(self._database_location)
            letter = letter.upper()
            self._database.removeRow(letter, word)
        except Exception as e:
            print("Failed to remove defintion from dictionary:",e)
        finally:
            self._database.closeDatabase() 

    def getDefinition(self, letter, word):
        """Returns the word selected definition from the dictionary as a string."""
        try:
            definition = None 
            self._database.openDatabase(self._database_location)
            definition = self._database.getCondValuesFromField(letter, "DEFINITION", "WORD", word)
            if definition:
                definition = definition[0]
            return definition
        except Exception as e:
            print(e)
        finally:
            self._database.closeDatabase() 

    def insertNewTableLetter(self, letter):
        """Inserts a new letter table into the dictionary database."""
        try:
            if len(letter) == 1:
                letter_caps = letter.upper()
                definition = {"WORD": {"value": "", "is_not_null": True, "is_unique": False},
                             "DEFINITION": {"value": "", "is_not_null": True, "is_unique": False}}
                self._database.openDatabase(self._database_location)
                self._database.createTable(letter_caps, definition)
            else:
                print("Incorrect input, must be a letter for new table entry.")

        
        except Exception as e:
            print("Failed to insert a new table letter:", e)
        
        finally:
            if self._database._connection:
                self._database.closeDatabase()

