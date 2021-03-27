# Bitvavo trailing alert

### Install python packages

./setup.sh

### Run trailing alert job

Add following line to cron job file, for example by ````crontab -e````

```
* * * * * /home/ubuntu/bitvavo_trailing_stop/bitvavo_trailing_stop/bin/python /home/ubuntu/bitvavo_trailing_stop/handle_alerts.py
```

### Add new alert

```
/home/ubuntu/bitvavo_trailing_stop/bitvavo_trailing_stop/bin/python create_new_alert.py
```

