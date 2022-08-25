import mysql.connector
import os
import schedule
import time
from bs4 import BeautifulSoup as bs
from dotenv import load_dotenv
from pushbullet import API
from urllib.request import urlopen

load_dotenv()
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_NAME = os.getenv("DATABASE_NAME")
PB_KEY = os.getenv("PB_KEY")

api = API()
api.set_token(PB_KEY)

url = 'https://schedule.hololive.tv/lives/'

def checkPhotos():
    text = urlopen(url).read()
    soup = bs(text, "html.parser")
    data = soup.findAll('img', style=lambda value: value and 
        'border-radius: 50%' in value
    )

    photosToCheck = set()

    for photo in data:
        photosToCheck.add(photo['src'])

    if len(photosToCheck):
        # print(photosToCheck)
        db = mysql.connector.connect(
            host = DATABASE_HOST,
            user = DATABASE_USERNAME,
            passwd = DATABASE_PASSWORD,
            db = DATABASE_NAME
        )

        cursor = db.cursor()
        q1 = 'CREATE TEMPORARY TABLE tmp_table (photo_url VARCHAR(255));'
        cursor.execute(q1)
        q2 = 'INSERT INTO tmp_table VALUES '

        for photoURL in photosToCheck:
            q2 += f'("{photoURL}"),'

        # remove trailing comma
        q2 = q2[:-1] + ';'

        cursor.execute(q2)

        q3 = """
            SELECT tmp_table.photo_url 
                FROM tmp_table
                LEFT JOIN member_photos m
                on tmp_table.photo_url = m.photo_url
                WHERE m.photo_url IS NULL;
        """
        cursor.execute(q3)
        photosToAdd = cursor.fetchall()

        db.close()

        if len(photosToAdd) > 0:
            body = f'Found {len(photosToAdd)} photo{"s" if len(photosToAdd) > 1 else ""} to add: ' + ' '.join([x[0] for x in photosToAdd])
            print(body)
            api.send_note("Hololively New Photos", body)
        else:
            print('No new photos found')
    return
    
if __name__ == '__main__':
    # in utc
    # 16:00 utc = 12:00 edt
    schedule.every().day.at("16:00").do(checkPhotos)

    while True:
        print(time.ctime())
        schedule.run_pending()
        time.sleep(60)