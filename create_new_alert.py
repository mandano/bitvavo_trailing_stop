from handle_alerts import CreateAlert, BitvavoClient

if __name__ == '__main__':
    ca = CreateAlert(_client=BitvavoClient())
    ca.add_by_console()
