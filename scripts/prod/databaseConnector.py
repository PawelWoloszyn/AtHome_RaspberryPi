import mysql.connector
from mysql.connector import errorcode
import CREDENTIALS as cred
import logging

def executeQuerryInDB(sqlQuerry, isSelectQuery, logger):
    try:
        cnx = mysql.connector.connect(host=cred.DB_ADDRESS,
                                      user=cred.DB_USERNAME,
                                      password=cred.DB_PASSWORD,
                                      database=cred.DB_NAME)
        mycursor = cnx.cursor()
        mycursor.execute(sqlQuerry)
        if isSelectQuery:
            fetchResult = mycursor.fetchall()
        cnx.commit()
        mycursor.close()
        cnx.close()
        if isSelectQuery:
            return fetchResult
        return

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.error("Database does not exist")
        else:
            logger.error(err)
    else:
        cnx.close()
