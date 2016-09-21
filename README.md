# Item-Catalog-API
In this project, there is a web application that provides a list of items within a variety of categories and integrate third party user registration and authentication. Authenticated users should have the ability to post, edit, and delete their own items.
You will be creating this project essentially from scratch, no templates have been provided for you. This means that you have free reign over the HTML, the CSS, and the files that include the application itself utilizing Flask.

## Requirements

1.  Git
2.  Virtual Box
3.  Vagrant
4.  Sqlite

## Environment
Place the directory inside the vagrant directory and run vagrant VM

## Installation

* Clone the repository
* cd into the directory using
```
> cd db
```
* Create a new database:
```
python models.py
```
* Populate the database with dummy data
```
> python db_populate_test_data.py
```
or you can run SQLAlchemy python commands to add items

* cd back to the main folder
```
cd ..
```
then run the application.py file using
```
python application.py
```
The application would be accessible on ['http://localhost:8000'](http://localhost:8000)

