## Statistics about GRE chargers in the field
### How to 
- Data capture from public database every hour
- Pre-processing to get health index
- etc


### Data upload and delete to / from sqlite
```
$ python manage.py load_charger_csv --path './data'
$ python manage.py clear_charger_data
```

### v02 upload 260224
- dashboard: staticstics
- data upload
- download data with csv form

### v04 upload 260225
- chart and table from top 5 CPOs for 7 days
- including Total and GRE CPs out of PL data