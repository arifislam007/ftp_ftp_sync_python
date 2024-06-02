from flask import Flask, request, render_template_string
import ftplib
import os

app = Flask(__name__)

form_html = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>FTP Connection Form</title>
  </head>
  <body>
    <div class="container">
      <h2>FTP Connection Form</h2>
      <form method="post">
        <div class="form-group">
          <label for="ftp_server">FTP Server:</label>
          <input type="text" class="form-control" id="ftp_server" name="ftp_server" required>
        </div>
        <div class="form-group">
          <label for="ftp_username">FTP Username:</label>
          <input type="text" class="form-control" id="ftp_username" name="ftp_username" required>
        </div>
        <div class="form-group">
          <label for="ftp_password">FTP Password:</label>
          <input type="password" class="form-control" id="ftp_password" name="ftp_password" required>
        </div>
        <div class="form-group">
          <label for="ftp_directory">FTP Directory:</label>
          <input type="text" class="form-control" id="ftp_directory" name="ftp_directory" required>
        </div>
        <div class="form-group">
          <label for="dest_ftp_server">Destination FTP Server:</label>
          <input type="text" class="form-control" id="dest_ftp_server" name="dest_ftp_server" required>
        </div>
        <div class="form-group">
          <label for="dest_ftp_username">Destination FTP Username:</label>
          <input type="text" class="form-control" id="dest_ftp_username" name="dest_ftp_username" required>
        </div>
        <div class="form-group">
          <label for="dest_ftp_password">Destination FTP Password:</label>
          <input type="password" class="form-control" id="dest_ftp_password" name="dest_ftp_password" required>
        </div>
        <div class="form-group">
          <label for="dest_ftp_directory">Destination FTP Directory:</label>
          <input type="text" class="form-control" id="dest_ftp_directory" name="dest_ftp_directory" required>
        </div>
        <button type="submit" class="btn btn-primary">Connect</button>
      </form>
    </div>
  </body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def ftp_connect():
    if request.method == 'POST':
        ftp_server = request.form['ftp_server']
        ftp_username = request.form['ftp_username']
        ftp_password = request.form['ftp_password']
        ftp_directory = request.form['ftp_directory']
        dest_ftp_server = request.form['dest_ftp_server']
        dest_ftp_username = request.form['dest_ftp_username']
        dest_ftp_password = request.form['dest_ftp_password']
        dest_ftp_directory = request.form['dest_ftp_directory']

        try:
            # Connect to the source FTP server
            ftp = ftplib.FTP(ftp_server)
            ftp.login(user=ftp_username, passwd=ftp_password)
            ftp.cwd(ftp_directory)

            # List files in the directory
            files = ftp.nlst()
            file_list = ", ".join(files)

            # Connect to the destination FTP server
            dest_ftp = ftplib.FTP(dest_ftp_server)
            dest_ftp.login(user=dest_ftp_username, passwd=dest_ftp_password)
            dest_ftp.cwd(dest_ftp_directory)

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

            return f"Connected to {ftp_server} and accessed directory {ftp_directory}. Files: {file_list}. Files synced to {dest_ftp_server}:{dest_ftp_directory}"
        except Exception as e:
            return f"Failed to connect or access directory. Error: {e}"

    return render_template_string(form_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

