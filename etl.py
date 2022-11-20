import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    """
    - Extract data and insert into table 'song' and 'artist'
    
    - Parameters:
                cur: cursor of psycopg2.connection()
                filepath: directory of data files
    """
    # open song file
    df = pd.read_json(filepath, lines = True)

    # insert song record
    song_data = df[['song_id', 'title', 'artist_id', 'year', 'duration']].values[0].tolist()
    cur.execute(song_table_insert, song_data)
    
    # insert artist record
    artist_data = df[['artist_id', 'artist_name', 'artist_location', 'artist_latitude', 'artist_longitude']].values[0].tolist()
    
    cur.execute(artist_table_insert, artist_data)


def process_log_file(cur, filepath):
    """
    - Extract data and insert into table 'time', 'user' and 'songplays'
    
    - Parameters:
                cur: cursor of psycopg2.connection()
                filepath: directory of data files
    """
    # open log file
    df = pd.read_json(filepath, lines = True)

    # filter by NextSong action
    df = df.loc[df['page'] == 'NextSong']

    # convert timestamp column to datetime  
    df['ts'] = pd.to_datetime(df['ts'], unit = 'ms') 
    t = pd.to_datetime(df['ts']) 
    
    # insert time data records
    time_data = (t, t.dt.hour, t.dt.day, t.dt.weekofyear, t.dt.month, t.dt.year, t.dt.weekday)
    column_labels = ('start_time', 'hour', 'day', 'week', 'month', 'year', 'weekday')
    time_df = pd.DataFrame(data = dict(zip(column_labels, time_data)), columns = column_labels)

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = df[['userId', 'firstName', 'lastName', 'gender', 'level']]

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    for index, row in df.iterrows():
        
        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        songplay_data = (row.ts, row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent)
        cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
    """
    - Get the filepath for all the idenfitied json files and populate them 
    into a list. Then make the function calls to process each file from the
    list to insert the data into the tables.    
    
    - The total number of files identified and the processing progress will 
    be printed to the command line window while processing.
    
    - Parameters:
                cur: cursor of psycopg2.connection()
                conn: connection of psycopg2
                filepath: directory of data files
                func: function for the related processing
    """
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    """
    - Establishes connection with the sparkify database and gets the cursor
    to it.
    
    - Bulk loads the json format files for song and log that stored under 
    the specified directories, then transform the loaded data to the correct format
    and insert into the table created by 'create_tables.py'
    
    - Finally, close the connection.    
    """
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()