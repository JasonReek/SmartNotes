from PySide2.QtCore import QTimer
import os 
from datetime import datetime

def minutes(minutes):
    MINUTE = 60000
    return MINUTE * minutes

class NotepadRecovery:
    def __init__(self):
        self.RECOVERY_DIR = "recovery"
        self.TEMP_EXT = '.bak'
        # Create a recovery directory if one does not exist. 
        try:
            if not os.path.isdir(self.RECOVERY_DIR):
                os.mkdir("recovery")
        except Exception as error:
            self.terminal("Failed to create the main recovery folder: {e}".format(e=error))
        
        # Number of temps to generate before overwriting the last temps 
        self.TEMP_LIMIT = 3

        self.recovery_timer = QTimer(self)
        self.recovery_timer.start(minutes(3))
        self.recovery_timer.timeout.connect(self.makeDocumentTemps)

    def tempCountInPath(self, path, file_name):
        temp_count = 0
        if os.path.isdir(path):
            for file_obj in os.listdir(path):
                if file_obj.lower().endswith(self.TEMP_EXT) and file_name in file_obj:
                    temp_count += 1
        return temp_count

    def removeExcessTempFiles(self, path, unsaved_file_name, temp_count):
        files = iter(os.listdir(path))
        num_of_files_to_remove =  1
        file_name = next(files)

        if temp_count > self.TEMP_LIMIT:
            num_of_files_to_remove = (temp_count - self.TEMP_LIMIT) + 1
        
        while num_of_files_to_remove and file_name is not None:
            
            if file_name.lower().endswith(self.TEMP_EXT) and unsaved_file_name in file_name:
                file_path = '\\'.join([path, file_name])
                os.remove(file_path)
                num_of_files_to_remove -= 1

            file_name = next(files)
        
    def makeDocumentTemps(self):
        todays_date = datetime.now()
        date = todays_date.strftime('%b-%d-%Y')
        temp_file_date = todays_date.strftime('%b-%d-%Y_%H_%M_%S')
        temp_dir_path = ''.join([self.RECOVERY_DIR, '\\', 'temp_', date])
        temp_file_path = ''

        document_text = None 
        temp_path = ""
        temp_name = ""
        temp_number = 1

        try:
            if not os.path.isdir(temp_dir_path):
                os.mkdir(temp_dir_path)
        except Exception as error:
            self.terminal("Failed to create temp folder: {e}".format(e=error))
        
        try:
            saved, saves = self.areDocumentsSaved()
            if saved is not None:
                if not saved:
                    for unsaved_name in saves:

                        # Check if any temp files exist in this path, and if 
                        # the number of files exceed the temp limit.
                        temp_count = self.tempCountInPath(temp_dir_path, unsaved_name) 
                        if temp_count >= self.TEMP_LIMIT:
                            self.removeExcessTempFiles(temp_dir_path, unsaved_name, temp_count)

                        document_text = self._notepads[unsaved_name].toHtml()
                        temp_name = ''.join([temp_file_date, unsaved_name, self.TEMP_EXT])
                        temp_file_path = '\\'.join([temp_dir_path, temp_name])
                        with open(temp_file_path, 'w') as t_f:
                            t_f.write(document_text)
                            t_f.flush()
                            os.fsync(t_f)
        
        except Exception as error:
            self.terminal(str(error))





