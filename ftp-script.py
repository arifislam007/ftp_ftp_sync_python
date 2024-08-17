import ftplib
import os
import mysql.connector

def get_ftp_details():
    try:
        connection = mysql.connector.connect(
            host='192.168.207.61',
            port=3308,
            user='root',
            password='ftppass',
            database='ftp_db'
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ftp_connections WHERE status = 'pending' LIMIT 1")
        ftp_details = cursor.fetchone()
        cursor.close()
        connection.close()
        return ftp_details
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def ftp_sync():
    ftp_details = get_ftp_details()

    if ftp_details:
        try:
            # Connect to the source FTP server
            ftp = ftplib.FTP(ftp_details['source_ftp_ip'])
            ftp.login(user=ftp_details['source_ftp_username'], passwd=ftp_details['source_ftp_password'])
            ftp.cwd(ftp_details['source_ftp_path'])

            # List files in the directory
            files = ftp.nlst()
            file_list = ", ".join(files)

            # Connect to the destination FTP server
            dest_ftp = ftplib.FTP(ftp_details['destination_ftp_ip'])
            dest_ftp.login(user=ftp_details['destination_ftp_username'], passwd=ftp_details['destination_ftp_password'])
            dest_ftp.cwd(ftp_details['destination_ftp_path'])

            # Sync files to the destination FTP server
            for file in files:
                local_filename = os.path.join("/tmp", file)
                with open(local_filename, 'wb') as f:
                    ftp.retrbinary('RETR ' + file, f.write)
                with open(local_filename, 'rb') as f:
                    dest_ftp.storbinary('STOR ' + file, f)

            # Close FTP connections
            ftp.quit()
            dest_ftp.quit()

            # Update the status of the FTP connection to 'active'
            connection = mysql.connector.connect(
                host='192.168.207.61',
                port=3308,
                user='root',
                password='ftppass',
                database='ftp_db'
            )
            cursor = connection.cursor()
            cursor.execute("UPDATE ftp_connections SET status = 'active' WHERE id = %s", (ftp_details['id'],))
            connection.commit()
            cursor.close()
            connection.close()

            print(f"Connected to {ftp_details['source_ftp_ip']} and accessed directory {ftp_details['source_ftp_path']}. Files: {file_list}. Files synced to {ftp_details['destination_ftp_ip']}:{ftp_details['destination_ftp_path']}")
        except Exception as e:
            print(f"Failed to connect or access directory. Error: {e}")
    else:
        print("No pending FTP connections found in the database.")

if __name__ == '__main__':
    ftp_sync()
