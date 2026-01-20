class UserRegistry:
    def __init__(self):
        self._users = []

    def add_user(self, username):
        self._users.append(username)

    def remove_user(self, username):
        self._users.remove(username)

    def get_all_users(self):
        return self._users

# Instantiate here so it can be imported elsewhere
online_users = UserRegistry()
