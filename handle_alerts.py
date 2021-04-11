from models.AlertHandler import AlertHandler
import main

if __name__ == '__main__':
    ah = AlertHandler()
    ah.update_alerts()
    ah.save_alerts()
