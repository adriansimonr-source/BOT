def update(self):

    if self.process_manager.is_connected():

        self.state.connected = True

    else:

        self.state.connected = False
        return


    # Datos simulados

    self.state.character_name = "Davion"

    self.state.level = 1


    self.state.hp = 2500
    self.state.max_hp = 3000


    self.state.mp = 800
    self.state.max_mp = 1000


    self.state.x = 125
    self.state.y = 340