import ftplib
import mysql.connector
from io import BytesIO
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_pending_ftp_connections():
    try:
        with mysql.connector.connect(
            host='192.168.207.61',
            port=3308,
            user='root',
            password='ftppass',
            database='ftp_db'
        ) as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM ftp_connections WHERE status = 'pending'")
                ftp_connections = cursor.fetchall()
        return ftp_connections
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return []

def download_upload_ftp_directory(source_ftp, dest_ftp):
    def is_directory(ftp, name):
        current = ftp.pwd()
        try:
            ftp.cwd(name)
            ftp.cwd(current)
            return True
        except ftplib.error_perm:
            return False

    def transfer_directory(src_ftp, dst_ftp, src_dir, dst_dir):
        src_ftp.cwd(src_dir)
        dst_ftp.cwd(dst_dir)

        file_list = src_ftp.nlst()

        for file in file_list:
            if is_directory(src_ftp, file):
                try:
                    dst_ftp.mkd(file)
                except ftplib.error_perm:
                    pass  # Directory already exists
                transfer_directory(src_ftp, dst_ftp, file, file)
                src_ftp.cwd('..')
                dst_ftp.cwd('..')
            else:
                try:
                    with BytesIO() as f:
                        src_ftp.retrbinary('RETR ' + file, f.write)
                        f.seek(0)
                        dst_ftp.storbinary('STOR ' + file, f)
                except ftplib.error_perm as e:
                    logging.error(f"File transfer error for {file}: {e}")
                except Exception as e:
                    logging.error(f"Unexpected error for {file}: {e}")

    transfer_directory(source_ftp, dest_ftp, '.', '.')

def ftp_sync():
    ftp_connections = get_pending_ftp_connections()

    if ftp_connections:
        for ftp_details in ftp_connections:
            try:
                # Connect to the source FTP server
                with ftplib.FTP(ftp_details['source_ftp_ip']) as source_ftp:
                    source_ftp.login(user=ftp_details['source_ftp_username'], passwd=ftp_details['source_ftp_password'])
                    source_ftp.cwd(ftp_details['source_ftp_path'])

                    # Connect to the destination FTP server
                    with ftplib.FTP(ftp_details['destination_ftp_ip']) as dest_ftp:
                        dest_ftp.login(user=ftp_details['destination_ftp_username'], passwd=ftp_details['destination_ftp_password'])
                        dest_ftp.cwd(ftp_details['destination_ftp_path'])

                        # Transfer files and directories from the source to the destination FTP server
                        download_upload_ftp_directory(source_ftp, dest_ftp)

                # Update the status of the FTP connection to 'active'
                with mysql.connector.connect(
                    host='192.168.207.61',
                    port=3308,
                    user='root',
                    password='ftppass',
                    database='ftp_db'
                ) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("UPDATE ftp_connections SET status = 'active' WHERE id = %s", (ftp_details['id'],))
                        connection.commit()

                logging.info(f"Connected to {ftp_details['source_ftp_ip']} and accessed directory {ftp_details['source_ftp_path']}. Files and directories synced to {ftp_details['destination_ftp_ip']}:{ftp_details['destination_ftp_path']}")
            except Exception as e:
                logging.error(f"Failed to connect or access directory for ID {ftp_details['id']}. Error: {e}")
    else:
        logging.info("No pending FTP connections found in the database.")

if __name__ == '__main__':
    ftp_sync()
