# Wall Street

This project is a web app that simulates a stock trading experience for the user. It uses real time stock tickers and prices from the AlphaVantage databases.
## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Technlogies Used

```
Python 

Flask

Sqlite3

Jinja2

HTML

CSS
```



### Installing

A step by step series of examples that tell you how to get a development env running

It is recommended to use a virtual environment to add these packeges to avoid conflict. 

Installing cs50 library

```
pip install cs50
```
The above library gives you the necessary frameworks and dependencies.

Installing the database management 
```
pip install Flask-SQLAlchemy
```

Install astroid
```
pip install astroid
```




## Configuring

Before getting started on this assignment, or indeed even tinkering with the distribution code, we’ll need to register for an API key in order to be able to query AlphaVantage’s data. To do so, follow these steps:

* Visit https://www.alphavantage.co/support/#api-key.

* Enter your name and email address.

* Click Get Free API Key.

* A text field should appear below. Copy the value after "Your dedicated access key is: " up to, but excluding, the period.

* In you terminal execute :

```
export API_KEY=value
```

Where value is that (pasted) value, without any space immediately before or after the =. You also may wish to paste that value in a text document somewhere, in case you need it again later.


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* This project is a refined version of the cs50 pset Finance, completed by the author when he pursued the course via edX

