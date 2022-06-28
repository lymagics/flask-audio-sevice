# Flask audio service

Audio service build with python and flask.

## To run localy follow this steps:
- Fill in .flaskenv file.
- Create and setup firebase storage.
- Download and setup elasticsearch.

#### Create and activate virtual environment:
```sh
    python -m venv [YOUR_ENV_NAME]
    venv/Scripts/activate
```

#### Install requirements.txt file:
```sh
    pip install -r requirements.txt
```

#### Run this commands:
```sh
    flask db upgrade # Apply database migrations
    flask insert-roles # Insert user roles to database
    flask create-indx Song # Create elasticsearch index for Song model
    flask translate compile # Compile all application languages
```

#### Now you can run this application with following command:
```sh
    flask run
```

## Application overwiev
#### Index page:
![](https://drive.google.com/uc?export=view&id=1NiUF6aROoTqzWlLyl9eSHKQkx3p-t7Fv)

#### User profile:
![](https://drive.google.com/uc?export=view&id=1oS8alAQjyqeea1dB9iWu77OVVXkWOGxD)

#### Song information:
![](https://drive.google.com/uc?export=view&id=1E7VtulWee_dUWRGicUsJjzgknjq88ya7)

#### Song lyrics:
![](https://drive.google.com/uc?export=view&id=1O_1HhViZPwH8YVopbUCV83SwCPcdIzaI)

#### Multilanguage pages:
- English
![](https://drive.google.com/uc?export=view&id=1NiUF6aROoTqzWlLyl9eSHKQkx3p-t7Fv)
- Ukrainian
![](https://drive.google.com/uc?export=view&id=1ezIyA3IZJwiWbxLZUQz7WTljs3pLWADg)
- Russian
![](https://drive.google.com/uc?export=view&id=1G3fdN19y6LqvIMQInWFrMgwmuf6XuGTg)

#### You can find this application here(in case i didn't turn it off):
[Application](https://noisy-notes.herokuapp.com)
#### Or you can paste following link in your browser:
https://noisy-notes.herokuapp.com
