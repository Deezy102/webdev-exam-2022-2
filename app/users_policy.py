from flask_login import current_user

class UserPolicy:
    def __init__(self, record=None):
        self.record = record

    def create(self):
        return current_user.is_admin

    def delete(self):
        return current_user.is_admin

    def update(self):
        is_editing_user = current_user.id == self.record.id
        return current_user.is_admin or current_user.is_editor
    
    def show(self):
        is_showing_user = current_user.id == self.record.id
        return current_user.is_authenticated
    
    def get_all_stats(self):
        return current_user.is_admin 
    


    