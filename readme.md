# bloodpressure_tracker

Simple blood pressure tracker app made using Django. 

To recreate this wep-app do the following:

1. Clone the repo
2. Install the django Python package and all the others found in [`views.py`](bloodpressure/views.py) and [`settings.py`](bloodpressure_tracker/settings.py)
3. Make a file called `settings.env` in the base directory and fill it in like so, making sure not to use quotes around your email or password name 

```
EMAIL_HOST_USER=ADD_YOUR_EMAIL_HERE
EMAIL_HOST_PASSWORD=ADD_YOUT_EMAIL_PASSWORD_HERE
```

4. Run the code:

``` bash
cd bloodpressure_tracker;
python manage.py runserver
```

5. go to http://localhost:8000/ 
