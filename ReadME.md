## HRM


Instrucion to run the project:

1. Clone the repository
2. Install the Dependencies
-- Check whether you have poetry installed or not 
--install poetry 
--poetry install

Check whether you have installed my sql server or not 
 reference for mac  : https://www.youtube.com/watch?v=nj3nBCwZaqI
 reference for windows : https://www.youtube.com/watch?v=hiS_mWZmmI0


 and create a local database.
    change the database url according to your local database.

now the db ready to use.
to run the project :
poetry run uvicorn app.main:app --reload

Docker Commands:
docker build --platform linux/amd64 -t nandakish0106/recruitproai .

docker push nandakish0106/recruitproai:latest 



  




