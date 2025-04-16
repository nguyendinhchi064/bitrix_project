# bitrix_project
AASC test 

(Ex 1 -- Done; Ex 2 --- Missing Requisites -> can't add address or bank name, account and website url in bitrix24)

Requirements:

1. POSTMAN
2. Python 3.9.13
3. IDE like VS code or VS

Because this project is a test so I don't need to ignore my .env file. These are steps to run my project

Steps to run this project:

1. Create  virtual environment: py -m venv venv
2. Go to virtual environment and activate it: cd venv/Scripts/activate or .\venv\Scripts\activate
3. Download requirements: pip install -r requirements.txt 
Check if it download full, you can runserver freely: py manage.py runserver
If you run server success, run the ngrok: ngrok http 8000 

-------------------WARNINGS!!!--------------------------

If you use other bitrix24 account, remember to change file .env:

BITRIX24_CLIENT_ID = 'client_id'  ----- when you create local application

BITRIX24_CLIENT_SECRET = 'client_secret' ------- when you create local application

BITRIX_DOMAIN = 'Unknown.bitrix24.vn' ------ If you use other bitrix24 account change this

NGROK_URL = 'https://domain_ngrok'  ------- Need to change urls each time you run in ngrok (in website bitrix24 too)

ALLOWED_HOSTS= domain_ngrok,localhost,127.0.0.1

If you see error ALLOWED_HOSTS, you can try reinstall the local application from developer resources in bitrix24 again

Recommend to test ex 1 with POSTMAN not using browser because bitrix24 send POST request while browser often using GET 
For some reasons, I can't understand why bitrix_url in views.py can't get from .env so I end up typing straight url in views.py (I know it not recommended in real product but now it just test >__< right ?>)

Ex 2 we can use web browser test freely now (But don't use POSTMAN ?_? because POSTMAN don't save or create new contact in bitrix24)