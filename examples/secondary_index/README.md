Secondary indexes example
-------------------------

Build and run as follows:

    $ ya make
    $ YDB_ENDPOINT="HOST:PORT" YDB_DATABASE="PATH" YDB_TOKEN="TOKEN" YDB_PATH="DB_PATH" ./secondary_index

Drop and create tables:

    $ curl -X POST localhost:5000/series/drop_tables
    $ curl -X POST localhost:5000/series/create_tables

Generate some random series records:

    $ curl -X POST 'localhost:5000/series/generate_random?startId=1&count=100'

Get the first 10 records:

    $ curl localhost:5000/series/list

Get the next 10 records:

    $ curl localhost:5000/series/list?lastSeriesId=10

Get first 10 most viewed series:

    $ curl localhost:5000/series/most_viewed

Get next 10 most viewed series:

    $ curl 'localhost:5000/series/most_viewed?lastSeriesId=...&lastViews=...'

Delete some record:

    $ curl -X POST localhost:5000/series/delete/5

Insert a new record:

    $ curl -X POST -H 'Content-Type: application/json' localhost:5000/series/insert --data-binary '{"seriesId":5,"title":"My Favorite Series","seriesInfo":"Series Description","releaseDate":"2018-09-05","views":1000000}'

Update views of the record:

    $ curl -X POST localhost:5000/series/update_views/5/1000001
