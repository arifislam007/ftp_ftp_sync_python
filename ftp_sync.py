import ftplib
import mysql.connector

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='192.168.207.61',
            port=3308,
            user='root',
            password='ftppass',
            database='ftp_db'
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def get_pending_ftp_details(connection):
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ftp_connections WHERE status = 'pending'")
        ftp_details_list = cursor.fetchall()
        cursor.close()
        return ftp_details_list
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

def is_directory(ftp, name):
    current = ftp.pwd()
    try:
        ftp.cwd(name)
        ftp.cwd(current)
        return True
    except ftplib.error_perm:
        return False

def file_exists(ftp, file_name):
    file_list = ftp.nlst()
    return file_name in file_list

def transfer_directory(src_ftp, dst_ftp, src_dir, dst_dir):
    src_ftp.cwd(src_dir)
    dst_ftp.cwd(dst_dir)
    file_count = 0

    file_list = src_ftp.nlst()

    for file in file_list:
        if is_directory(src_ftp, file):
            try:
                dst_ftp.mkd(file)
            except ftplib.error_perm:
                pass  # Directory already exists
            file_count += transfer_directory(src_ftp, dst_ftp, file, file)
            src_ftp.cwd('..')
            dst_ftp.cwd('..')
        else:
            if not file_exists(dst_ftp, file):
                with src_ftp.transfercmd('RETR ' + file) as src_conn:
                    with dst_ftp.transfercmd('STOR ' + file) as dst_conn:
                        while True:
                            chunk = src_conn.recv(8192)
                            if not chunk:
                                break
                            dst_conn.sendall(chunk)
                file_count += 1

    return file_count

def update_ftp_status(connection, ftp_details_id):
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE ftp_connections SET status = 'active' WHERE id = %s", (ftp_details_id,))
        connection.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

def ftp_sync():
    connection = get_db_connection()

    if connection:
        ftp_details_list = get_pending_ftp_details(connection)

        if ftp_details_list:
            for ftp_details in ftp_details_list:
                try:
                    # Connect to the source FTP server
                    source_ftp = ftplib.FTP(ftp_details['source_ftp_ip'])
                    source_ftp.login(user=ftp_details['source_ftp_username'], passwd=ftp_details['source_ftp_password'])
                    source_ftp.cwd(ftp_details['source_ftp_path'])

                    # Connect to the destination FTP server
                    dest_ftp = ftplib.FTP(ftp_details['destination_ftp_ip'])
                    dest_ftp.login(user=ftp_details['destination_ftp_username'], passwd=ftp_details['destination_ftp_password'])
                    dest_ftp.cwd(ftp_details['destination_ftp_path'])

                    # Transfer files and directories from the source to the destination FTP server
                    file_count = transfer_directory(source_ftp, dest_ftp, '.', '.')

                    # Close FTP connections
                    source_ftp.quit()
                    dest_ftp.quit()

                    # Update the status of the FTP connection to 'active'
                    update_ftp_status(connection, ftp_details['id'])

                    print(f"Connected to {ftp_details['source_ftp_ip']} and accessed directory {ftp_details['source_ftp_path']}. {file_count} files and directories synced to {ftp_details['destination_ftp_ip']}:{ftp_details['destination_ftp_path']}")
                except Exception as e:
                    print(f"Failed to connect or access directory for FTP ID {ftp_details['id']}. Error: {e}")
        else:
            print("No pending FTP connections found in the database.")
        
        connection.close()
    else:
        print("Failed to connect to the database.")

if __name__ == '__main__':
    ftp_sync()
