from models.CreateAlert import CreateAlert
from models.clients.Bitvavo import BitvavoClient

if __name__ == '__main__':
    ca = CreateAlert(_client=BitvavoClient())
    ca.add_by_console()
